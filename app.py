import streamlit as st
import cv2
import numpy as np
import pandas as pd
from datetime import datetime, date
import sqlite3
import tempfile
import os
from PIL import Image
import easyocr
import json
import openai
import base64
from io import BytesIO
import requests

# Initialize EasyOCR reader
@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(['en'])

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
def extract_asset_tags(image):
    """Extract text from image using OCR"""
    reader = load_ocr_reader()

    # Convert PIL image to numpy array
    if isinstance(image, Image.Image):
        image = np.array(image)

    # Use EasyOCR to detect text
    results = reader.readtext(image)

    detected_tags = []
    for (bbox, text, confidence) in results:
        # Filter for likely asset tags (adjust patterns as needed)
        text = text.strip().upper()
        if confidence > 0.5 and (
                text.startswith('GYM') or
                text.startswith('ASS') or
                text.startswith('EQ') or
                len(text) >= 4 and text.isalnum()
        ):
            detected_tags.append({
                'tag': text,
                'confidence': confidence,
                'bbox': bbox
            })

    return detected_tags

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
                if st.button("🔍 Detect Asset Tags", type="primary"):
                    with st.spinner("Analyzing image..."):
                        detected_tags = extract_asset_tags(image)

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