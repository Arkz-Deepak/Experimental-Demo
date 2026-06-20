import requests
import pandas as pd
import time
import sys
import os
from dotenv import load_dotenv

load_dotenv()
DEFAULT_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")


def fetch_google_maps_leads(query, api_key, max_results=40):
    """
    Production-grade extraction pipeline using the Google Places API (New).
    Includes network error handling and graceful fallbacks.
    """
    # 1. Validate API Key Input
    if api_key == "YOUR_GOOGLE_API_KEY_HERE" or not api_key:
        print("❌ CRITICAL ERROR: No API Key provided.")
        print("Please paste your Google Maps Demo Key into the MY_API_KEY variable.")
        return pd.DataFrame() # Return empty DataFrame safely

    print(f"🔍 Automating search for: '{query}'...")
    
    url = "https://places.googleapis.com/v1/places:searchText"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        # Fetching exact columns needed for the outbound sales sheet
        "X-Goog-FieldMask": "places.displayName.text,places.formattedAddress,places.internationalPhoneNumber,places.websiteUri,places.primaryType,nextPageToken"
    }
    
    data = {
        "textQuery": query,
        "pageSize": 20 # The API returns max 20 per page
    }

    leads = []
    
    while len(leads) < max_results:
        try:
            response = requests.post(url, headers=headers, json=data)
            
            # 2. Catch HTTP Errors (e.g., 403 Forbidden, 400 Bad Request)
            if response.status_code != 200:
                print(f"❌ API Error {response.status_code}: {response.json().get('error', {}).get('message', 'Unknown Error')}")
                break
                
            response_data = response.json()
            places = response_data.get('places', [])
            
            if not places:
                print("⚠️ No more places found for this query.")
                break
                
            # Parse the deeply nested JSON safely
            for place in places:
                leads.append({
                    "Company Name": place.get('displayName', {}).get('text', 'N/A'),
                    "Mobile": place.get('internationalPhoneNumber', 'N/A'),
                    "Website": place.get('websiteUri', 'N/A'),
                    "Type of Company": place.get('primaryType', 'N/A').replace('_', ' ').title(),
                    "Address": place.get('formattedAddress', 'N/A')
                })
                
            print(f"✅ Extracted {len(leads)} leads so far...")
            
            # Check for pagination token to get the next batch
            next_page_token = response_data.get('nextPageToken')
            if not next_page_token:
                break # No more pages available
                
            data['pageToken'] = next_page_token
            time.sleep(2) # Respectful delay to prevent rate-limiting

        except requests.exceptions.RequestException as e:
            print(f"❌ Network request failed: {e}")
            break

    return pd.DataFrame(leads)

def auto_clean_data(df, output_filename="clean_leads.csv"):
    """
    Cleans the raw dataframe. Safely aborts if the dataframe is empty.
    """
    output_filename= search_query+'.csv'
    # 3. Guardrail: Prevent the exact KeyError you experienced
    if df is None or df.empty:
        print("🛑 Data Cleaning Aborted: The lead table is empty. Please check your API key and query.")
        return

    # Check if the specific column exists before trying to access it
    if 'Company Name' not in df.columns:
        print("🛑 Data Cleaning Aborted: 'Company Name' column missing from data payload.")
        return

    print("\n🧹 Initiating automated data cleaning...")
    
    initial_count = len(df)
    
    # Drop exact duplicates
    df = df.drop_duplicates(subset=['Company Name'])
    
    # Filter out irrelevant businesses safely handling NaN values
    exclude_keywords = ['retail', 'showroom', 'mechanic', 'repair', 'dealer']
    pattern = '|'.join(exclude_keywords)
    df = df[~df['Company Name'].str.contains(pattern, case=False, na=False)]
    
    # Handle missing essential contact info (Drop rows with no phone AND no website)
    df = df[~((df['Mobile'] == 'N/A') & (df['Website'] == 'N/A'))]
    
    try:
        df.to_csv(output_filename, index=False)
        final_count = len(df)
        print(f"✨ Cleaning complete! Removed {initial_count - final_count} low-quality/duplicate rows.")
        print(f"📁 Saved perfectly formatted, production-ready file to: {output_filename}")
    except PermissionError:
        print(f"❌ Could not save file. Make sure '{output_filename}' is not open in Excel.")

if __name__ == "__main__":
    # --- PASTE YOUR DEMO KEY HERE ---
    MY_API_KEY = DEFAULT_API_KEY
    
    search_query = "Mining Equipment manufacturers in Delhi" # TYPE YOUR PROMPT FOR MAP SEARCH HERE
    
    print("-" * 50)
    print("🚀 PRECISE3DM OUTBOUND LEAD AUTOMATOR")
    print("-" * 50)
    
    raw_dataframe = fetch_google_maps_leads(search_query, MY_API_KEY)
    
    auto_clean_data(raw_dataframe)