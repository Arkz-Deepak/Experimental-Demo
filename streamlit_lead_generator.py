import streamlit as st
import requests
import pandas as pd
import time
import io
import os
from dotenv import load_dotenv

load_dotenv()
DEFAULT_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")


# --- Page Configuration ---
st.set_page_config(page_title="Precise3DM Lead Generator", page_icon="🎯", layout="wide")

def fetch_google_maps_leads(query, api_key, max_results=60, status_text=None):
    """Fetches leads from Google Places API (New)"""
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName.text,places.formattedAddress,places.internationalPhoneNumber,places.websiteUri,places.primaryType,nextPageToken"
    }
    data = {"textQuery": query, "pageSize": 20}
    leads = []
    
    while len(leads) < max_results:
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                st.error(f"API Error {response.status_code}: {response.json().get('error', {}).get('message', 'Unknown Error')}")
                break
                
            response_data = response.json()
            places = response_data.get('places', [])
            
            if not places:
                break
                
            for place in places:
                leads.append({
                    "Company Name": place.get('displayName', {}).get('text', 'N/A'),
                    "Mobile": place.get('internationalPhoneNumber', 'N/A'),
                    "Website": place.get('websiteUri', 'N/A'),
                    "Type of Company": place.get('primaryType', 'N/A').replace('_', ' ').title(),
                    "Address": place.get('formattedAddress', 'N/A')
                })
            
            if status_text:
                status_text.text(f"✅ Extracted {len(leads)} leads so far...")
            
            next_page_token = response_data.get('nextPageToken')
            if not next_page_token:
                break
                
            data['pageToken'] = next_page_token
            time.sleep(2) # Prevent rate-limiting

        except requests.exceptions.RequestException as e:
            st.error(f"Network request failed: {e}")
            break

    return pd.DataFrame(leads)

def categorize_lead(row):
    """Categorizes leads into Type A, B, C based on sales strategy."""
    name = str(row['Company Name']).lower()
    biz_type = str(row['Type of Company']).lower()
    combined_text = name + " " + biz_type

    # TYPE A: End Users (Direct Buyers)
    type_a_keywords = ['cnc', 'machining', 'automotive', 'auto', 'aerospace', 'tool', 'die', 'foundry', 'mould', 'mold', 'manufacturer', 'precision', 'components', 'fabricat']
    if any(kw in combined_text for kw in type_a_keywords):
        return "Type A: End User"

    # TYPE B: Channel Partners (Resellers/Integrators)
    type_b_keywords = ['3d print', 'cad', 'cam', 'solution', 'automation', 'metrology', 'distributor', 'dealer', 'supplier', 'trader', 'wholesaler', 'equipment']
    if any(kw in combined_text for kw in type_b_keywords):
        return "Type B: Channel Partner"

    # TYPE C: Ecosystem Partners (Referrals/Influencers)
    type_c_keywords = ['consultant', 'design', 'college', 'university', 'institute', 'r&d', 'research', 'technology park']
    if any(kw in combined_text for kw in type_c_keywords):
        return "Type C: Ecosystem Partner"

    # Default if it passes the exclusion filter but doesn't match above
    return "Uncategorized Prospect"

def process_data(df):
    """Cleans data and applies the sales categorization."""
    if df.empty:
        return df

    # Drop exact duplicates
    df = df.drop_duplicates(subset=['Company Name'])
    
    # 1. Exclusion Filter (Drop completely irrelevant businesses)
    exclude_keywords = ['showroom', 'mechanic', 'repair', 'restaurant', 'grocery'] 
    pattern = '|'.join(exclude_keywords)
    df = df[~df['Company Name'].str.contains(pattern, case=False, na=False)]
    
    # 2. Drop rows missing BOTH phone and website (useless for sales)
    df = df[~((df['Mobile'] == 'N/A') & (df['Website'] == 'N/A'))]
    
    # 3. Apply Categorization
    df['Customer Category'] = df.apply(categorize_lead, axis=1)
    
    # Reorder columns for the final Excel sheet
    cols = ['Customer Category', 'Company Name', 'Mobile', 'Website', 'Address', 'Type of Company']
    df = df[cols]
    
    # Sort so Type A is at the top, then B, then C
    df = df.sort_values(by='Customer Category')
    
    return df

# --- Streamlit UI Layout ---

st.title("🎯 Precise3DM Outbound Lead Generator")
st.markdown("Automated targeting for End Users, Channel Partners, and Ecosystem Partners.")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Configuration")

    api_key = st.text_input(
    "Google Maps API Key",
    value=DEFAULT_API_KEY,   # 👈 pre-filled default
    type="password",
    help="Paste your Maps Demo Key or Production Key here."
)

    max_results = st.slider("Max Leads to Fetch", min_value=20, max_value=200, value=60, step=20)
    
    st.markdown("---")
    st.markdown("**Category Legend:**")
    st.markdown("🟢 **Type A:** Direct End Users (CNC, Auto, Aero)")
    st.markdown("🔵 **Type B:** Channel Partners (Dealers, CAD/CAM)")
    st.markdown("🟡 **Type C:** Ecosystem (Consultants, Colleges)")

# Main Search Area
search_query = st.text_input("🔎 Search Query (e.g., 'CNC machining companies in Ambattur')")

if st.button("Generate Leads", type="primary"):
    if not api_key:
        st.warning("⚠️ Please enter your API Key in the sidebar to begin.")
    elif not search_query:
        st.warning("⚠️ Please enter a search query.")
    else:
        with st.status("Mining Google Maps Data...", expanded=True) as status:
            status_text = st.empty()
            
            # Step 1: Fetch
            raw_df = fetch_google_maps_leads(search_query, api_key, max_results, status_text)
            
            if not raw_df.empty:
                status.update(label="Processing and Categorizing Leads...", state="running")
                # Step 2: Process & Categorize
                clean_df = process_data(raw_df)
                
                status.update(label=f"✅ Successfully processed {len(clean_df)} leads!", state="complete")
                
                # Step 3: Display Results
                st.subheader("📊 Lead Results")
                
                # Metrics row
                col1, col2, col3 = st.columns(3)
                col1.metric("Type A (End Users)", len(clean_df[clean_df['Customer Category'] == 'Type A: End User']))
                col2.metric("Type B (Partners)", len(clean_df[clean_df['Customer Category'] == 'Type B: Channel Partner']))
                col3.metric("Type C (Ecosystem)", len(clean_df[clean_df['Customer Category'] == 'Type C: Ecosystem Partner']))

                # Interactive Dataframe
                st.dataframe(clean_df, use_container_width=True, hide_index=True)
                
                # Step 4: CSV Download logic
                csv = clean_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Leads as CSV",
                    data=csv,
                    file_name=f"precise3dm_leads_{search_query.replace(' ', '_')}.csv",
                    mime="text/csv",
                    type="primary"
                )
            else:
                status.update(label="❌ No leads found or API error occurred.", state="error")