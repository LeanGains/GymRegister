from os import getenv
import streamlit as st
import pandas as pd
from datetime import datetime, date
import sqlite3
import os
from PIL import Image
import json
import base64
from io import BytesIO
from openai import OpenAI
import re
import gc
import sys
from contextlib import contextmanager

API_KEY = os.getenv('OPENAI_API_KEY')

# Aggressive memory management
def force_memory_cleanup():
    """Aggressively clean up memory"""
    gc.collect()
    if hasattr(gc, 'set_threshold'):
        gc.set_threshold(10, 10, 10)

# Simple OpenAI client - never cached
def create_openai_client():
    """Create fresh OpenAI client"""
    if not API_KEY:
        st.error("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        return None
    try:
        return OpenAI(api_key=API_KEY)
    except Exception as e:
        st.error(f"OpenAI client error: {e}")
        return None

def compress_image_efficiently(image, max_pixels=400000, quality=75):
    """Compress image for OpenAI while maintaining quality for detection"""
    try:
        width, height = image.size
        total_pixels = width * height

        if total_pixels > max_pixels:
            scale_factor = (max_pixels / total_pixels) ** 0.5
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Convert to RGB if needed
        if image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            if image.mode in ('RGBA', 'LA'):
                rgb_image.paste(image, mask=image.split()[-1])
            else:
                rgb_image.paste(image)
            image.close()
            image = rgb_image
        elif image.mode != 'RGB':
            new_image = image.convert('RGB')
            image.close()
            image = new_image

        return image

    except Exception as e:
        st.error(f"Image compression error: {e}")
        return None

def image_to_base64(image):
    """Convert image to base64 with memory management"""
    buffer = None
    try:
        compressed = compress_image_efficiently(image, max_pixels=300000, quality=80)
        if not compressed:
            return None

        buffer = BytesIO()
        compressed.save(buffer, format="JPEG", quality=80, optimize=True)

        img_bytes = buffer.getvalue()
        base64_str = base64.b64encode(img_bytes).decode('utf-8')

        # Immediate cleanup
        buffer.close()
        compressed.close()
        if compressed != image:
            del compressed
        del img_bytes

        force_memory_cleanup()
        return base64_str

    except Exception as e:
        st.error(f"Base64 conversion error: {e}")
        return None
    finally:
        if buffer:
            buffer.close()
        force_memory_cleanup()

def analyze_gym_equipment_with_gpt4o(image):
    """Use GPT-4o to detect both asset tags and equipment in gym images"""
    client = None
    base64_image = None

    try:
        # Convert to base64
        base64_image = image_to_base64(image)
        if not base64_image:
            return {"error": "Failed to process image"}

        # Check size limit (OpenAI has ~20MB limit)
        if len(base64_image) > 15 * 1024 * 1024:  # 15MB safety margin
            return {"error": "Image too large after compression"}

        client = create_openai_client()
        if not client:
            return {"error": "OpenAI client unavailable"}

        prompt = """You are an expert gym equipment analyzer. Analyze this image and identify:

1. Any asset tags, labels, barcodes, or identification codes on equipment
2. All gym equipment visible with their weights/specifications
3. Equipment condition if visible

Return a JSON response with this exact structure:
{
  "asset_tags": [
    {
      "tag": "asset_tag_text",
      "confidence": 0.95,
      "location_description": "where on the equipment"
    }
  ],
  "equipment": [
    {
      "type": "dumbbell/barbell_plate/kettlebell/medicine_ball/resistance_band/cable_attachment/bench/other",
      "weight": "25 lbs" or "unknown",
      "description": "detailed description",
      "condition": "excellent/good/fair/poor/unknown",
      "suggested_asset_tag": "suggested tag if no tag visible",
      "location_in_image": "description of location in image"
    }
  ],
  "image_quality": "excellent/good/fair/poor",
  "total_items": 0,
  "recommendations": "any suggestions for better detection"
}

Be thorough but concise. If you see multiple identical items (like a rack of dumbbells), list each separately.
For asset tags, look for any text/codes that could be used for tracking - stickers, engraved text, barcodes, etc.
For equipment, be specific about weights and types."""

        # Use GPT-4o model
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"  # Use high detail with GPT-4o
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500,
            temperature=0.1
        )

        content = response.choices[0].message.content

        # Parse JSON response
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                return {"error": "No valid JSON in response", "raw_response": content}
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw_response": content}

    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

    finally:
        # Aggressive cleanup
        if base64_image:
            del base64_image
        if client:
            del client
        force_memory_cleanup()

# Database operations
@contextmanager
def get_db():
    conn = sqlite3.connect('gym_assets.db', timeout=10)
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS assets (
                                                              id INTEGER PRIMARY KEY,
                                                              asset_tag TEXT UNIQUE,
                                                              item_type TEXT,
                                                              description TEXT,
                                                              location TEXT,
                                                              last_seen DATETIME,
                                                              status TEXT,
                                                              weight TEXT,
                                                              condition TEXT,
                                                              notes TEXT
                        )''')

        conn.execute('''CREATE TABLE IF NOT EXISTS audit_log (
                                                                 id INTEGER PRIMARY KEY,
                                                                 asset_tag TEXT,
                                                                 action TEXT,
                                                                 timestamp DATETIME,
                                                                 location TEXT,
                                                                 notes TEXT
                        )''')
        conn.commit()

def add_asset(asset_data):
    try:
        with get_db() as conn:
            conn.execute('''INSERT OR REPLACE INTO assets 
                (asset_tag, item_type, description, location, last_seen, status, weight, condition, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', asset_data)

            conn.execute('''INSERT INTO audit_log (asset_tag, action, timestamp, location, notes)
                            VALUES (?, 'REGISTERED', ?, ?, ?)''',
                         (asset_data[0], datetime.now(), asset_data[3], f"Added {asset_data[1]}"))
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

def get_all_assets():
    try:
        with get_db() as conn:
            return pd.read_sql_query("SELECT * FROM assets ORDER BY last_seen DESC", conn)
    except:
        return pd.DataFrame()

def search_asset(tag):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM assets WHERE asset_tag = ?", (tag,))
            return cursor.fetchone()
    except:
        return None

def update_asset_location(tag, location, notes=""):
    try:
        with get_db() as conn:
            conn.execute("UPDATE assets SET location = ?, last_seen = ? WHERE asset_tag = ?",
                         (location, datetime.now(), tag))
            conn.execute("INSERT INTO audit_log (asset_tag, action, timestamp, location, notes) VALUES (?, 'MOVED', ?, ?, ?)",
                         (tag, datetime.now(), location, notes))
            conn.commit()
        return True
    except:
        return False

def main():
    # Memory management initialization
    if 'memory_initialized' not in st.session_state:
        force_memory_cleanup()
        st.session_state.memory_initialized = True

    st.set_page_config(
        page_title="Gym Asset Registry",
        page_icon="🏋️",
        layout="wide"
    )

    init_database()

    st.title("🏋️ Gym Asset Registry - GPT-4o Powered")

    # Memory controls
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown("**Powered by GPT-4o** - Advanced gym equipment and asset tag detection")
    with col2:
        if st.button("🧹 Clear Memory"):
            for key in list(st.session_state.keys()):
                if key != 'memory_initialized':
                    del st.session_state[key]
            force_memory_cleanup()
            st.success("Memory cleared!")
    with col3:
        memory_mb = sys.getsizeof(st.session_state) / (1024 * 1024)
        st.metric("Session MB", f"{memory_mb:.1f}")

    # Navigation
    page = st.sidebar.selectbox("Choose a page", [
        "📷 Equipment Scanner",
        "➕ Register Asset",
        "📋 View Assets",
        "🔍 Search Asset",
        "📊 Reports"
    ])

    if page == "📷 Equipment Scanner":
        st.header("🤖 AI Equipment Scanner")
        st.markdown("Take a photo to detect equipment and asset tags using GPT-4o")

        # Camera input - RESTORED and prioritized
        st.subheader("📱 Take Photo")
        camera_photo = st.camera_input("Take a photo of gym equipment")

        # File upload as alternative
        st.subheader("📁 Or Upload Image")
        uploaded_file = st.file_uploader("Upload an image", type=['png', 'jpg', 'jpeg'])

        image_source = camera_photo or uploaded_file

        if image_source is not None:
            try:
                # Check file size
                file_size = len(image_source.getvalue()) if hasattr(image_source, 'getvalue') else image_source.size
                if file_size > 20 * 1024 * 1024:  # 20MB limit
                    st.error("File too large! Please use a smaller image (under 20MB).")
                    return

                # Load and display image
                original_image = Image.open(image_source)
                st.info(f"Image: {original_image.size[0]}x{original_image.size[1]} pixels, {file_size/1024:.0f}KB")

                # Show image
                display_image = original_image.copy()
                if display_image.size[0] > 600 or display_image.size[1] > 600:
                    display_image.thumbnail((600, 600))
                st.image(display_image, caption="Image to Analyze", use_column_width=True)
                display_image.close()

                # Analysis button
                if st.button("🚀 Analyze with GPT-4o", type="primary", use_container_width=True):
                    with st.spinner("GPT-4o analyzing image... This may take 10-20 seconds..."):
                        analysis_result = analyze_gym_equipment_with_gpt4o(original_image)

                    # Store analysis result in session state to persist across interactions
                    st.session_state.analysis_result = analysis_result
                    st.session_state.image_analyzed = True

                # Display results if we have them (from current analysis or previous)
                analysis_result = st.session_state.get('analysis_result', {})
                if st.session_state.get('image_analyzed', False) and analysis_result:

                    if analysis_result.get('error'):
                        st.error(f"Analysis Error: {analysis_result['error']}")
                        if analysis_result.get('raw_response'):
                            with st.expander("Raw Response"):
                                st.text(analysis_result['raw_response'])
                    else:
                        # Display results
                        st.success("✅ Analysis Complete!")

                        # Show image quality and recommendations
                        col1, col2 = st.columns(2)
                        with col1:
                            quality = analysis_result.get('image_quality', 'unknown')
                            if quality in ['excellent', 'good']:
                                st.success(f"📸 Image Quality: {quality.title()}")
                            else:
                                st.warning(f"📸 Image Quality: {quality.title()}")

                        with col2:
                            total = analysis_result.get('total_items', 0)
                            st.info(f"🔢 Total Items Detected: {total}")

                        if analysis_result.get('recommendations'):
                            st.info(f"💡 **Tip:** {analysis_result['recommendations']}")

                        # Display detected asset tags
                        asset_tags = analysis_result.get('asset_tags', [])
                        if asset_tags:
                            st.subheader("🏷️ Asset Tags Found")
                            for tag_info in asset_tags:
                                tag_text = tag_info.get('tag', '').upper()
                                confidence = tag_info.get('confidence', 0)
                                location_desc = tag_info.get('location_description', 'Unknown location')

                                with st.expander(f"Tag: **{tag_text}** (Confidence: {confidence:.2f})"):
                                    st.write(f"**Location on equipment:** {location_desc}")

                                    # Check if exists in database
                                    existing = search_asset(tag_text)
                                    if existing:
                                        st.success("✅ This asset is already in the database!")
                                        st.write(f"**Type:** {existing[2]}")
                                        st.write(f"**Current Location:** {existing[4]}")
                                        st.write(f"**Status:** {existing[6]}")

                                        # Quick location update
                                        new_location = st.text_input(f"Update location for {tag_text}",
                                                                     value=existing[4],
                                                                     key=f"update_loc_{tag_text}")
                                        if st.button(f"Update Location", key=f"update_{tag_text}"):
                                            if new_location != existing[4]:
                                                if update_asset_location(tag_text, new_location, "Updated from scanner"):
                                                    st.success("Location updated!")
                                    else:
                                        st.warning("⚠️ This asset tag is not in the database yet.")

                        # Display detected equipment
                        equipment_list = analysis_result.get('equipment', [])
                        if equipment_list:
                            st.subheader("🏋️ Equipment Detected")

                            # Initialize registered items tracker in session state
                            if 'registered_items' not in st.session_state:
                                st.session_state.registered_items = set()

                            for i, equipment in enumerate(equipment_list):
                                eq_type = equipment.get('type', 'unknown')
                                weight = equipment.get('weight', 'unknown')
                                description = equipment.get('description', 'No description')
                                condition = equipment.get('condition', 'unknown')
                                suggested_tag = equipment.get('suggested_asset_tag', '')
                                location_in_image = equipment.get('location_in_image', '')

                                # Check if this item was already registered
                                item_key = f"item_{i}"
                                is_registered = item_key in st.session_state.registered_items

                                status_icon = "✅" if is_registered else "📦"
                                status_text = " (REGISTERED)" if is_registered else ""

                                with st.expander(f"{status_icon} Equipment {i+1}: {eq_type.title().replace('_', ' ')} - {weight}{status_text}"):
                                    # Equipment details
                                    st.write(f"**Type:** {eq_type.title().replace('_', ' ')}")
                                    st.write(f"**Weight:** {weight}")
                                    st.write(f"**Description:** {description}")
                                    st.write(f"**Condition:** {condition.title()}")
                                    st.write(f"**Location in image:** {location_in_image}")

                                    if is_registered:
                                        st.success("✅ This item has been registered!")
                                        if st.button(f"Register Another Copy", key=f"register_copy_{i}"):
                                            st.session_state.registered_items.discard(item_key)
                                            st.rerun()
                                    else:
                                        st.markdown("---")
                                        st.subheader("🏷️ Register This Equipment")

                                        # Registration form - NO st.form to prevent page refresh
                                        reg_col1, reg_col2 = st.columns(2)

                                        with reg_col1:
                                            asset_tag_input = st.text_input(
                                                "Asset Tag *",
                                                value=suggested_tag,
                                                key=f"asset_tag_{i}",
                                                help="Enter or scan the asset tag for this equipment"
                                            )

                                            # Map equipment type to our categories
                                            type_mapping = {
                                                'dumbbell': 'Dumbbell',
                                                'barbell_plate': 'Barbell Plate',
                                                'kettlebell': 'Kettle Bell',
                                                'medicine_ball': 'Medicine Ball',
                                                'resistance_band': 'Resistance Band',
                                                'cable_attachment': 'Cable Attachment',
                                                'bench': 'Bench',
                                                'other': 'Other'
                                            }

                                            equipment_types = ["Dumbbell", "Barbell Plate", "Kettle Bell", "Resistance Band",
                                                               "Medicine Ball", "Cable Attachment", "Bench", "Jump Rope",
                                                               "Yoga Mat", "Foam Roller", "Other"]

                                            default_type = type_mapping.get(eq_type.lower(), 'Other')
                                            type_index = equipment_types.index(default_type) if default_type in equipment_types else -1

                                            equipment_type = st.selectbox(
                                                "Equipment Type *",
                                                equipment_types,
                                                index=max(0, type_index),
                                                key=f"eq_type_{i}"
                                            )

                                        with reg_col2:
                                            location_input = st.text_input(
                                                "Location *",
                                                key=f"location_{i}",
                                                placeholder="e.g., Weight Room - Rack 3"
                                            )

                                            # Map AI condition to our options
                                            condition_options = ["Excellent", "Good", "Fair", "Poor", "Needs Repair"]
                                            ai_condition = condition.lower()
                                            if ai_condition in ['excellent', 'good', 'fair', 'poor']:
                                                condition_index = condition_options.index(ai_condition.title())
                                            else:
                                                condition_index = 1  # Default to 'Good'

                                            condition_select = st.selectbox(
                                                "Condition",
                                                condition_options,
                                                index=condition_index,
                                                key=f"condition_{i}"
                                            )

                                        notes_input = st.text_area(
                                            "Notes",
                                            value=f"Auto-detected: {description}",
                                            key=f"notes_{i}"
                                        )

                                        # Regular button instead of form submit button
                                        if st.button(
                                                f"✅ Register {eq_type.title().replace('_', ' ')}",
                                                type="primary",
                                                key=f"register_btn_{i}",
                                                use_container_width=True
                                        ):
                                            if not asset_tag_input or not location_input:
                                                st.error("Please fill in Asset Tag and Location")
                                            else:
                                                # Check if tag already exists
                                                existing_asset = search_asset(asset_tag_input.upper())
                                                if existing_asset:
                                                    st.error(f"Asset tag '{asset_tag_input}' already exists in database!")
                                                else:
                                                    asset_data = (
                                                        asset_tag_input.upper(),
                                                        equipment_type,
                                                        description,
                                                        location_input,
                                                        datetime.now(),
                                                        "Active",
                                                        weight if weight != 'unknown' else '',
                                                        condition_select,
                                                        notes_input
                                                    )

                                                    if add_asset(asset_data):
                                                        st.success(f"🎉 Successfully registered: {asset_tag_input}!")
                                                        # Mark this item as registered
                                                        st.session_state.registered_items.add(item_key)
                                                        st.balloons()
                                                        # Rerun to update the display
                                                        st.rerun()
                                                    else:
                                                        st.error("Failed to register asset. Please try again.")

                        else:
                            st.warning("No equipment detected in the image.")

                        # Clear analysis button to reset
                        if st.button("🔄 Analyze New Image", use_container_width=True):
                            st.session_state.analysis_result = {}
                            st.session_state.image_analyzed = False
                            st.session_state.registered_items = set()
                            st.rerun()

                # Cleanup original image
                original_image.close()
                force_memory_cleanup()

            except Exception as e:
                st.error(f"Image processing error: {e}")
                force_memory_cleanup()

    elif page == "➕ Register Asset":
        st.header("Register New Asset")

        with st.form("register_form"):
            col1, col2 = st.columns(2)

            with col1:
                asset_tag = st.text_input("Asset Tag *").upper()
                item_type = st.selectbox("Type *", ["Dumbbell", "Barbell Plate", "Kettle Bell", "Resistance Band",
                                                    "Medicine Ball", "Cable Attachment", "Bench", "Jump Rope",
                                                    "Yoga Mat", "Foam Roller", "Other"])
                description = st.text_input("Description")
                weight = st.text_input("Weight", placeholder="e.g., 25 lbs")

            with col2:
                location = st.text_input("Location *", placeholder="e.g., Weight Room - Rack 3")
                condition = st.selectbox("Condition", ["Excellent", "Good", "Fair", "Poor", "Needs Repair"])
                status = st.selectbox("Status", ["Active", "Out of Service", "Missing"])
                notes = st.text_area("Notes")

            if st.form_submit_button("Register Asset", type="primary"):
                if asset_tag and item_type and location:
                    # Check for duplicates
                    existing = search_asset(asset_tag)
                    if existing:
                        st.error(f"Asset tag '{asset_tag}' already exists!")
                    else:
                        asset_data = (asset_tag, item_type, description, location, datetime.now(),
                                      status, weight, condition, notes)
                        if add_asset(asset_data):
                            st.success(f"✅ {asset_tag} registered successfully!")
                            st.balloons()
                        else:
                            st.error("Registration failed")
                else:
                    st.error("Please fill in all required fields (*)")

    elif page == "📋 View Assets":
        st.header("All Assets")

        assets_df = get_all_assets()
        if not assets_df.empty:
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                type_filter = st.selectbox("Filter by Type", ["All"] + sorted(assets_df['item_type'].unique().tolist()))
            with col2:
                status_filter = st.selectbox("Filter by Status", ["All"] + sorted(assets_df['status'].unique().tolist()))
            with col3:
                location_filter = st.text_input("Location contains:")

            # Apply filters
            filtered_df = assets_df.copy()
            if type_filter != "All":
                filtered_df = filtered_df[filtered_df['item_type'] == type_filter]
            if status_filter != "All":
                filtered_df = filtered_df[filtered_df['status'] == status_filter]
            if location_filter:
                filtered_df = filtered_df[filtered_df['location'].str.contains(location_filter, case=False, na=False)]

            st.info(f"Showing {len(filtered_df)} of {len(assets_df)} assets")

            # Display table
            st.dataframe(
                filtered_df[['asset_tag', 'item_type', 'description', 'location', 'weight', 'last_seen', 'status', 'condition']],
                use_container_width=True,
                column_config={
                    "asset_tag": "Asset Tag",
                    "item_type": "Type",
                    "description": "Description",
                    "location": "Location",
                    "weight": "Weight",
                    "last_seen": st.column_config.DatetimeColumn("Last Seen"),
                    "status": "Status",
                    "condition": "Condition"
                }
            )

            # Export
            csv = filtered_df.to_csv(index=False)
            st.download_button("📥 Download CSV", csv, f"gym_assets_{date.today()}.csv", "text/csv")
        else:
            st.info("No assets found. Use the Equipment Scanner to add some!")

    elif page == "🔍 Search Asset":
        st.header("Search Asset")

        search_tag = st.text_input("Enter Asset Tag", placeholder="Type asset tag to search").upper()

        if search_tag:
            result = search_asset(search_tag)
            if result:
                st.success("✅ Asset found!")

                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Asset Tag:** {result[1]}")
                    st.write(f"**Type:** {result[2]}")
                    st.write(f"**Description:** {result[3]}")
                    st.write(f"**Weight:** {result[7] or 'Not specified'}")
                    st.write(f"**Notes:** {result[9] or 'None'}")

                with col2:
                    st.write(f"**Location:** {result[4]}")
                    st.write(f"**Last Seen:** {result[5]}")
                    st.write(f"**Status:** {result[6]}")
                    st.write(f"**Condition:** {result[8]}")

                # Quick location update
                st.subheader("Update Location")
                new_location = st.text_input("New Location", value=result[4])
                if st.button("Update Location", type="primary"):
                    if new_location != result[4]:
                        if update_asset_location(result[1], new_location, "Manual update"):
                            st.success("✅ Location updated!")
                            st.rerun()
                    else:
                        st.info("Location unchanged")
            else:
                st.error("❌ Asset not found in database")
                st.info("💡 Use the Equipment Scanner to detect and register new assets")

    elif page == "📊 Reports":
        st.header("Asset Reports")

        assets_df = get_all_assets()
        if not assets_df.empty:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Assets", len(assets_df))
            with col2:
                active_count = len(assets_df[assets_df['status'] == 'Active'])
                st.metric("Active", active_count)
            with col3:
                missing_count = len(assets_df[assets_df['status'] == 'Missing'])
                st.metric("Missing", missing_count, delta=f"{missing_count/len(assets_df)*100:.1f}%")
            with col4:
                repair_count = len(assets_df[assets_df['condition'] == 'Needs Repair'])
                st.metric("Needs Repair", repair_count)

            # Charts
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Equipment by Type")
                type_counts = assets_df['item_type'].value_counts()
                st.bar_chart(type_counts)

            with col2:
                st.subheader("Equipment by Status")
                status_counts = assets_df['status'].value_counts()
                st.bar_chart(status_counts)

            # Recent activity
            st.subheader("Recently Added Assets")
            recent = assets_df.head(10)[['asset_tag', 'item_type', 'location', 'last_seen', 'status']]
            st.dataframe(recent, use_container_width=True)

            # Alerts
            if missing_count > 0:
                st.error(f"⚠️ {missing_count} assets are marked as missing!")
                missing_assets = assets_df[assets_df['status'] == 'Missing'][['asset_tag', 'item_type', 'location']]
                st.dataframe(missing_assets, use_container_width=True)

            if repair_count > 0:
                st.warning(f"🔧 {repair_count} assets need repair!")
                repair_assets = assets_df[assets_df['condition'] == 'Needs Repair'][['asset_tag', 'item_type', 'location']]
                st.dataframe(repair_assets, use_container_width=True)

        else:
            st.info("📊 No assets to analyze yet. Start by scanning some equipment!")

if __name__ == "__main__":
    main()