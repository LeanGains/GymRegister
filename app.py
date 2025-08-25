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

# Initialize OpenAI client
@st.cache_resource
def get_openai_client():
    """Get OpenAI client with API key from Streamlit secrets or environment"""
    try:
        # Try to get API key from Streamlit secrets first
        if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
            api_key = st.secrets['OPENAI_API_KEY']
        else:
            # Fallback to environment variable
            api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            st.error("OpenAI API key not found. Please set OPENAI_API_KEY in secrets or environment variables.")
            return None
        
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"Error setting up OpenAI: {e}")
        return None

def encode_image_to_base64(image):
    """Convert PIL image to base64 string for OpenAI API"""
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def identify_weight_with_openai(image):
    """Use OpenAI GPT-4 Vision to identify weights in gym equipment images"""
    client = get_openai_client()
    if not client:
        return None
    
    try:
        # Convert image to base64
        base64_image = encode_image_to_base64(image)
        
        # Create the prompt for weight identification
        prompt = """
        You are an expert gym equipment identifier. Analyze this image and identify any weights or gym equipment visible.
        
        Please provide a JSON response with the following structure:
        {
            "equipment_detected": [
                {
                    "type": "dumbbell/barbell_plate/kettlebell/medicine_ball/other",
                    "weight": "weight in lbs or kg (specify unit)",
                    "confidence": "high/medium/low",
                    "description": "brief description of the equipment",
                    "condition": "excellent/good/fair/poor (if visible)",
                    "location_in_image": "description of where in the image"
                }
            ],
            "total_items": "number of items detected",
            "image_quality": "excellent/good/fair/poor",
            "recommendations": "suggestions for better image capture if needed"
        }
        
        Focus on:
        - Identifying specific weights (look for numbers on dumbbells, plates, kettlebells)
        - Equipment type classification
        - Condition assessment if visible
        - Multiple items in the same image
        
        If no weights are clearly visible, indicate this in the response.
        """
        
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.1
        )
        
        # Parse the response
        response_text = response.choices[0].message.content
        
        # Try to extract JSON from the response
        try:
            # Find JSON in the response (it might be wrapped in markdown)
            import re
            json_match = re.search(r'```json\s*({.*?})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without markdown
                json_match = re.search(r'{.*}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response_text
            
            result = json.loads(json_str)
            return result
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return a structured response with the raw text
            return {
                "equipment_detected": [],
                "total_items": 0,
                "image_quality": "unknown",
                "raw_response": response_text,
                "error": "Failed to parse JSON response"
            }
            
    except Exception as e:
        st.error(f"Error with OpenAI vision analysis: {e}")
        return {
            "equipment_detected": [],
            "total_items": 0,
            "error": str(e)
        }

# Database setup
def init_database():
    conn = sqlite3.connect('gym_assets.db')
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS assets (
                                                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                         asset_tag TEXT UNIQUE,
                                                         item_type TEXT,
                                                         description TEXT,
                                                         location TEXT,
                                                         last_seen DATETIME,
                                                         status TEXT,
                                                         weight TEXT,
                                                         condition TEXT,
                                                         notes TEXT
                   )
                   ''')

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS audit_log (
                                                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                            asset_tag TEXT,
                                                            action TEXT,
                                                            timestamp DATETIME,
                                                            location TEXT,
                                                            notes TEXT
                   )
                   ''')
    conn.commit()
    conn.close()

# OCR functions
def extract_asset_tags_and_weights(image):
    """Extract both asset tags using OCR and identify weights using OpenAI Vision"""
    # Get OCR results for asset tags
    ocr_results = extract_asset_tags_ocr(image)
    
    # Get OpenAI vision results for weight identification
    vision_results = identify_weight_with_openai(image)
    
    return {
        "asset_tags": ocr_results,
        "weight_analysis": vision_results
    }

def extract_asset_tags_ocr(image):
    """Extract asset tags from image using OpenAI Vision API"""
    client = get_openai_client()
    if not client:
        return []
    
    try:
        # Convert image to base64
        base64_image = encode_image_to_base64(image)
        
        # Create prompt for asset tag detection
        prompt = """
        You are an expert at identifying asset tags, barcodes, and equipment labels in gym equipment images.
        
        Please analyze this image and identify any asset tags, equipment labels, serial numbers, or identification codes.
        Look for:
        - Asset tags (often start with GYM, ASS, EQ, or similar prefixes)
        - Barcodes with text underneath
        - Equipment serial numbers
        - Model numbers
        - Any alphanumeric codes that could be used for tracking
        
        Return the results as a JSON array with this format:
        [
            {
                "tag": "extracted tag/code",
                "confidence": 0.95,
                "type": "asset_tag" or "barcode" or "serial_number" or "model_number",
                "location": "description of where the tag appears in the image"
            }
        ]
        
        Only include tags that are clearly visible and readable. Provide confidence scores from 0.0 to 1.0.
        If no asset tags are found, return an empty array [].
        """
        
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=800,
            temperature=0.1
        )
        
        # Parse the response
        content = response.choices[0].message.content
        
        # Try to extract JSON from the response
        try:
            # Look for JSON array in the response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                detected_tags = json.loads(json_match.group())
                # Convert to the expected format for compatibility
                formatted_tags = []
                for tag in detected_tags:
                    formatted_tags.append({
                        'tag': tag.get('tag', '').strip().upper(),
                        'confidence': tag.get('confidence', 0.8),
                        'type': tag.get('type', 'unknown'),
                        'location': tag.get('location', 'unknown')
                    })
                return formatted_tags
            else:
                return []
        except json.JSONDecodeError:
            # If no valid JSON found, return empty list
            return []
            
    except Exception as e:
        st.error(f"Error extracting asset tags: {str(e)}")
        return []

# Database operations
def add_asset(asset_data):
    conn = sqlite3.connect('gym_assets.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO assets 
            (asset_tag, item_type, description, location, last_seen, status, weight, condition, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', asset_data)

        # Log the action
        cursor.execute('''
                       INSERT INTO audit_log (asset_tag, action, timestamp, location, notes)
                       VALUES (?, 'REGISTERED', ?, ?, ?)
                       ''', (asset_data[0], datetime.now(), asset_data[3], f"Added {asset_data[1]}"))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding asset: {e}")
        return False
    finally:
        conn.close()

def get_all_assets():
    conn = sqlite3.connect('gym_assets.db')
    df = pd.read_sql_query("SELECT * FROM assets ORDER BY last_seen DESC", conn)
    conn.close()
    return df

def update_asset_location(asset_tag, new_location, notes=""):
    conn = sqlite3.connect('gym_assets.db')
    cursor = conn.cursor()
    cursor.execute('''
                   UPDATE assets SET location = ?, last_seen = ? WHERE asset_tag = ?
                   ''', (new_location, datetime.now(), asset_tag))

    cursor.execute('''
                   INSERT INTO audit_log (asset_tag, action, timestamp, location, notes)
                   VALUES (?, 'MOVED', ?, ?, ?)
                   ''', (asset_tag, datetime.now(), new_location, notes))

    conn.commit()
    conn.close()

def search_asset(asset_tag):
    conn = sqlite3.connect('gym_assets.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assets WHERE asset_tag = ?", (asset_tag,))
    result = cursor.fetchone()
    conn.close()
    return result

# Streamlit UI
def main():
    st.set_page_config(page_title="Gym Asset Registry", page_icon="🏋️", layout="wide")

    # Initialize database
    init_database()

    st.title("🏋️ Gym Asset Registry")
    st.markdown("Track your gym equipment using AI-powered asset tag recognition")

    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "📷 Quick Scan",
        "➕ Register New Asset",
        "📋 View All Assets",
        "🔍 Search Asset",
        "📊 Reports"
    ])

    if page == "📷 Quick Scan":
        st.header("Quick Asset Scan")
        st.markdown("Take a photo to automatically detect asset tags")

        # Camera input
        camera_photo = st.camera_input("Take a photo of equipment")

        # File upload as alternative
        uploaded_file = st.file_uploader("Or upload an image", type=['png', 'jpg', 'jpeg'])

        image_to_process = camera_photo or uploaded_file

        if image_to_process is not None:
            # Display image
            image = Image.open(image_to_process)
            col1, col2 = st.columns(2)

            with col1:
                st.image(image, caption="Captured Image", use_column_width=True)

            with col2:
                col_scan1, col_scan2 = st.columns(2)
                
                with col_scan1:
                    if st.button("🔍 Detect Asset Tags (OCR)", type="secondary"):
                        with st.spinner("Analyzing image for asset tags..."):
                            detected_tags = extract_asset_tags_ocr(image)

                        if detected_tags:
                            st.success(f"Found {len(detected_tags)} potential asset tags:")

                            for i, tag_info in enumerate(detected_tags):
                                with st.expander(f"Tag: {tag_info['tag']} (Confidence: {tag_info['confidence']:.2f})"):
                                    col_a, col_b = st.columns(2)

                                    with col_a:
                                        # Check if asset exists
                                        existing_asset = search_asset(tag_info['tag'])
                                        if existing_asset:
                                            st.info("Asset found in database!")
                                            st.write(f"**Type:** {existing_asset[2]}")
                                            st.write(f"**Location:** {existing_asset[4]}")
                                            st.write(f"**Last Seen:** {existing_asset[5]}")
                                        else:
                                            st.warning("Asset not in database")

                                    with col_b:
                                        new_location = st.text_input(f"Update location for {tag_info['tag']}", key=f"loc_{i}")
                                        if st.button(f"Update Location", key=f"update_{i}"):
                                            if new_location:
                                                if existing_asset:
                                                    update_asset_location(tag_info['tag'], new_location, "Quick scan update")
                                                    st.success("Location updated!")
                                                else:
                                                    st.error("Asset must be registered first")
                        else:
                            st.warning("No asset tags detected. Try a clearer image or better lighting.")
                
                with col_scan2:
                    if st.button("🤖 AI Weight Identification", type="primary"):
                        with st.spinner("Analyzing image with AI to identify weights..."):
                            vision_results = identify_weight_with_openai(image)

                        if vision_results and vision_results.get('equipment_detected'):
                            st.success(f"AI detected {vision_results.get('total_items', 0)} equipment items:")
                            
                            # Display image quality assessment
                            if vision_results.get('image_quality'):
                                quality = vision_results['image_quality']
                                if quality in ['excellent', 'good']:
                                    st.success(f"Image Quality: {quality.title()}")
                                else:
                                    st.warning(f"Image Quality: {quality.title()}")
                            
                            # Display recommendations if any
                            if vision_results.get('recommendations'):
                                st.info(f"💡 **Tip:** {vision_results['recommendations']}")

                            # Display detected equipment
                            for i, equipment in enumerate(vision_results['equipment_detected']):
                                with st.expander(f"{equipment.get('type', 'Unknown').title()}: {equipment.get('weight', 'Unknown weight')} (Confidence: {equipment.get('confidence', 'unknown').title()})"):
                                    col_eq1, col_eq2 = st.columns(2)
                                    
                                    with col_eq1:
                                        st.write(f"**Type:** {equipment.get('type', 'Unknown').title()}")
                                        st.write(f"**Weight:** {equipment.get('weight', 'Not specified')}")
                                        st.write(f"**Description:** {equipment.get('description', 'No description')}")
                                        st.write(f"**Location in Image:** {equipment.get('location_in_image', 'Not specified')}")
                                        if equipment.get('condition'):
                                            st.write(f"**Condition:** {equipment.get('condition').title()}")
                                    
                                    with col_eq2:
                                        st.subheader("Quick Register")
                                        
                                        # Pre-fill form with AI-detected information
                                        suggested_tag = st.text_input(
                                            "Asset Tag", 
                                            placeholder=f"Enter tag for {equipment.get('type', 'item')}",
                                            key=f"ai_tag_{i}"
                                        )
                                        
                                        # Auto-select equipment type based on AI detection
                                        equipment_types = ["Dumbbell", "Barbell Plate", "Kettle Bell", "Resistance Band", "Medicine Ball", "Jump Rope", "Yoga Mat", "Foam Roller", "Other"]
                                        detected_type = equipment.get('type', '').lower()
                                        
                                        # Map AI detected types to our categories
                                        type_mapping = {
                                            'dumbbell': 'Dumbbell',
                                            'barbell_plate': 'Barbell Plate', 
                                            'kettlebell': 'Kettle Bell',
                                            'medicine_ball': 'Medicine Ball'
                                        }
                                        
                                        default_type_index = 0
                                        if detected_type in type_mapping:
                                            try:
                                                default_type_index = equipment_types.index(type_mapping[detected_type])
                                            except ValueError:
                                                default_type_index = 0
                                        
                                        selected_type = st.selectbox(
                                            "Equipment Type",
                                            equipment_types,
                                            index=default_type_index,
                                            key=f"ai_type_{i}"
                                        )
                                        
                                        location_input = st.text_input(
                                            "Location",
                                            placeholder="e.g., Free Weight Area - Rack 3",
                                            key=f"ai_location_{i}"
                                        )
                                        
                                        # Auto-fill condition if detected
                                        condition_options = ["Excellent", "Good", "Fair", "Poor", "Needs Repair"]
                                        condition_index = 0
                                        if equipment.get('condition'):
                                            detected_condition = equipment['condition'].title()
                                            if detected_condition in condition_options:
                                                condition_index = condition_options.index(detected_condition)
                                        
                                        selected_condition = st.selectbox(
                                            "Condition",
                                            condition_options,
                                            index=condition_index,
                                            key=f"ai_condition_{i}"
                                        )
                                        
                                        if st.button(f"Register This Item", key=f"ai_register_{i}", type="primary"):
                                            if suggested_tag and selected_type and location_input:
                                                asset_data = (
                                                    suggested_tag.upper(),
                                                    selected_type,
                                                    equipment.get('description', f"AI-detected {selected_type}"),
                                                    location_input,
                                                    datetime.now(),
                                                    "Active",
                                                    equipment.get('weight', ''),
                                                    selected_condition,
                                                    f"Registered via AI detection. Confidence: {equipment.get('confidence', 'unknown')}"
                                                )
                                                
                                                if add_asset(asset_data):
                                                    st.success(f"Asset {suggested_tag} registered successfully!")
                                                else:
                                                    st.error("Failed to register asset")
                                            else:
                                                st.error("Please fill in Asset Tag, Equipment Type, and Location")
                        
                        elif vision_results and vision_results.get('error'):
                            st.error(f"AI Analysis Error: {vision_results['error']}")
                            if vision_results.get('raw_response'):
                                with st.expander("Raw AI Response"):
                                    st.text(vision_results['raw_response'])
                        
                        else:
                            st.warning("No equipment detected by AI. Try a clearer image with better lighting, or ensure gym equipment is clearly visible.")
                
                # Combined Analysis Button
                st.markdown("---")
                if st.button("🚀 Complete Analysis (OCR + AI)", type="primary", use_container_width=True):
                    with st.spinner("Running complete analysis..."):
                        combined_results = extract_asset_tags_and_weights(image)
                    
                    # Display combined results
                    if combined_results:
                        col_combined1, col_combined2 = st.columns(2)
                        
                        with col_combined1:
                            st.subheader("🔍 Asset Tags Found (OCR)")
                            asset_tags = combined_results.get('asset_tags', [])
                            if asset_tags:
                                for tag in asset_tags:
                                    st.write(f"• {tag['tag']} (Confidence: {tag['confidence']:.2f})")
                            else:
                                st.write("No asset tags detected")
                        
                        with col_combined2:
                            st.subheader("🤖 Equipment Identified (AI)")
                            weight_analysis = combined_results.get('weight_analysis', {})
                            if weight_analysis and weight_analysis.get('equipment_detected'):
                                for eq in weight_analysis['equipment_detected']:
                                    st.write(f"• {eq.get('type', 'Unknown').title()}: {eq.get('weight', 'Unknown weight')}")
                            else:
                                st.write("No equipment detected")

    elif page == "➕ Register New Asset":
        st.header("Register New Asset")

        col1, col2 = st.columns(2)

        with col1:
            asset_tag = st.text_input("Asset Tag", placeholder="Enter or scan asset tag").upper()
            item_type = st.selectbox("Equipment Type", [
                "Dumbbell", "Barbell Plate", "Kettle Bell", "Resistance Band",
                "Medicine Ball", "Jump Rope", "Yoga Mat", "Foam Roller", "Other"
            ])
            description = st.text_input("Description", placeholder="e.g., 25lb dumbbell, rubber coated")
            weight = st.text_input("Weight", placeholder="e.g., 25 lbs")

        with col2:
            location = st.text_input("Current Location", placeholder="e.g., Free Weight Area - Rack 3")
            condition = st.selectbox("Condition", ["Excellent", "Good", "Fair", "Poor", "Needs Repair"])
            status = st.selectbox("Status", ["Active", "Out of Service", "Missing"])
            notes = st.text_area("Notes", placeholder="Additional information...")

        if st.button("Register Asset", type="primary"):
            if asset_tag and item_type:
                asset_data = (
                    asset_tag, item_type, description, location,
                    datetime.now(), status, weight, condition, notes
                )

                if add_asset(asset_data):
                    st.success(f"Asset {asset_tag} registered successfully!")
                    st.balloons()
                else:
                    st.error("Failed to register asset")
            else:
                st.error("Asset tag and equipment type are required")

    elif page == "📋 View All Assets":
        st.header("All Assets")

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            type_filter = st.selectbox("Filter by Type", ["All"] + [
                "Dumbbell", "Barbell Plate", "Kettle Bell", "Resistance Band",
                "Medicine Ball", "Jump Rope", "Yoga Mat", "Foam Roller", "Other"
            ])
        with col2:
            status_filter = st.selectbox("Filter by Status", ["All", "Active", "Out of Service", "Missing"])
        with col3:
            location_filter = st.text_input("Filter by Location (contains)")

        assets_df = get_all_assets()

        # Apply filters
        if type_filter != "All":
            assets_df = assets_df[assets_df['item_type'] == type_filter]
        if status_filter != "All":
            assets_df = assets_df[assets_df['status'] == status_filter]
        if location_filter:
            assets_df = assets_df[assets_df['location'].str.contains(location_filter, case=False, na=False)]

        if not assets_df.empty:
            st.dataframe(
                assets_df,
                column_config={
                    "asset_tag": "Asset Tag",
                    "item_type": "Type",
                    "description": "Description",
                    "location": "Location",
                    "last_seen": "Last Seen",
                    "status": "Status",
                    "condition": "Condition"
                },
                hide_index=True,
                use_container_width=True
            )

            # Export functionality
            csv = assets_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"gym_assets_{date.today()}.csv",
                mime="text/csv"
            )
        else:
            st.info("No assets found matching the filters")

    elif page == "🔍 Search Asset":
        st.header("Search for Asset")

        search_tag = st.text_input("Enter Asset Tag", placeholder="Type asset tag to search").upper()

        if search_tag:
            result = search_asset(search_tag)
            if result:
                st.success("Asset found!")

                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Asset Tag:** {result[1]}")
                    st.write(f"**Type:** {result[2]}")
                    st.write(f"**Description:** {result[3]}")
                    st.write(f"**Weight:** {result[7]}")

                with col2:
                    st.write(f"**Location:** {result[4]}")
                    st.write(f"**Last Seen:** {result[5]}")
                    st.write(f"**Status:** {result[6]}")
                    st.write(f"**Condition:** {result[8]}")

                if result[9]:  # Notes
                    st.write(f"**Notes:** {result[9]}")

                # Quick location update
                new_location = st.text_input("Update Location")
                if st.button("Update Location"):
                    if new_location:
                        update_asset_location(result[1], new_location)
                        st.success("Location updated!")
                        st.rerun()
            else:
                st.error("Asset not found in database")

    elif page == "📊 Reports":
        st.header("Asset Reports")

        assets_df = get_all_assets()

        if not assets_df.empty:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Asset Summary")
                total_assets = len(assets_df)
                active_assets = len(assets_df[assets_df['status'] == 'Active'])
                missing_assets = len(assets_df[assets_df['status'] == 'Missing'])

                st.metric("Total Assets", total_assets)
                st.metric("Active Assets", active_assets)
                st.metric("Missing Assets", missing_assets)

            with col2:
                st.subheader("Assets by Type")
                type_counts = assets_df['item_type'].value_counts()
                st.bar_chart(type_counts)

            # Recent activity
            st.subheader("Recently Updated Assets")
            recent_assets = assets_df.head(10)[['asset_tag', 'item_type', 'location', 'last_seen', 'status']]
            st.dataframe(recent_assets, hide_index=True)
        else:
            st.info("No assets in database yet")

if __name__ == "__main__":
    main()