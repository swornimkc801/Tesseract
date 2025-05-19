import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv
import os
import time
import traceback
import folium
from streamlit_folium import folium_static

# --- Environment Setup ---
try:
    # Load environment variables
    if not load_dotenv():
        st.error("⚠️ Could not load .env file")
    API_KEY = os.getenv("SERPAPI_KEY")
    
    if not API_KEY:
        st.error("❌ SERPAPI_KEY not found in .env file")
    
except Exception as e:
    st.error(f"🚨 Critical Error: {str(e)}")
    st.code(traceback.format_exc())
    st.stop()  # Stop execution if env setup fails

# --- Page Configuration ---
st.set_page_config(
    page_title="JobFinder Pro",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Styling ---
st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
        }
        .stTextInput>div>div>input {
            padding: 10px;
            font-size: 16px;
        }
        .stButton>button {
            width: 100%;
            padding: 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: #45a049;
            transform: scale(1.01);
        }
        .job-card {
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            background-color: white;
            transition: all 0.3s;
            cursor: pointer;
        }
        .job-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        .company-name {
            font-weight: bold;
            color: #2c3e50;
        }
        .job-title {
            font-size: 18px;
            color: #3498db;
            margin-bottom: 5px;
        }
        .location {
            color: #7f8c8d;
            font-size: 14px;
        }
        .via {
            font-size: 12px;
            color: #95a5a6;
            font-style: italic;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 0 0 10px 10px;
            margin-bottom: 2rem;
        }
        .search-container {
            background-color: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        .footer {
            text-align: center;
            padding: 1rem;
            color: #7f8c8d;
            font-size: 12px;
        }
        .error-box {
            background-color: #ffebee;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #f44336;
            margin-bottom: 15px;
        }
        .job-details {
            padding: 20px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-top: 15px;
        }
        .map-container {
            margin-top: 20px;
            border-radius: 10px;
            overflow: hidden;
        }
    </style>
""", unsafe_allow_html=True)

# --- Header Section ---
st.markdown("""
    <div class="header">
        <h1 style="color:white; margin:0;">🔍 JobFinder Pro</h1>
        <p style="color:white; opacity:0.8; margin:0;">Find your dream job from thousands of listings worldwide</p>
    </div>
""", unsafe_allow_html=True)

# --- Search Section ---
with st.container():
    col1, col2, col3 = st.columns([3, 3, 2])
    
    with col1:
        job_title = st.text_input("Job Title", "Software Engineer", key="job_title")
    
    with col2:
        location = st.text_input("Location", "New York", key="location")
    
    with col3:
        st.write("")  # Spacer
        st.write("")  # Spacer
        search_clicked = st.button("🚀 Find Jobs", key="search_button")

# --- Session State for Selected Job ---
if 'selected_job' not in st.session_state:
    st.session_state.selected_job = None

# --- Results Section ---
if search_clicked:
    with st.spinner('Searching for the best jobs...'):
        # Simulate loading for better UX
        time.sleep(1)
        
        # Fetch jobs from SerpAPI
        params = {
            "engine": "google_jobs",
            "q": job_title,
            "location": location,
            "hl": "en",
            "api_key": API_KEY,
            "chips": "date_posted:today"  # Get fresher jobs
        }
        
        try:
            response = requests.get("https://serpapi.com/search", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            jobs = data.get("jobs_results", [])
            
            if jobs:
                st.success(f"🎉 Found {len(jobs)} jobs in {location}!")
                
                # --- Display Jobs as Clickable Cards ---
                for idx, job in enumerate(jobs):
                    with st.container():
                        # Add clickable card
                        clicked = st.markdown(f"""
                            <div class="job-card" onclick="window.jobClicked{idx} = true">
                                <div class="job-title">{job.get('title', 'N/A')}</div>
                                <div class="company-name">{job.get('company_name', 'N/A')}</div>
                                <div class="location">{job.get('location', 'N/A')}</div>
                                <div class="via">via {job.get('via', 'Unknown')}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Handle card click (using session state)
                        if st.session_state.get(f"job_clicked_{idx}", False):
                            st.session_state.selected_job = job
                        
                        # Set click handler via JS (workaround for Streamlit)
                        st.components.v1.html(f"""
                            <script>
                                window.jobClicked{idx} = false;
                                setInterval(() => {{
                                    if (window.jobClicked{idx}) {{
                                        parent.window.jobClicked{idx} = true;
                                        window.jobClicked{idx} = false;
                                    }}
                                }}, 100);
                            </script>
                        """, height=0)
                
                # --- Show Selected Job Details ---
                if st.session_state.selected_job:
                    job = st.session_state.selected_job
                    
                    with st.container():
                        st.markdown(f"""
                            <div class="job-details">
                                <h3>{job.get('title', 'N/A')}</h3>
                                <p><strong>Company:</strong> {job.get('company_name', 'N/A')}</p>
                                <p><strong>Location:</strong> {job.get('location', 'N/A')}</p>
                                <p><strong>Posted via:</strong> {job.get('via', 'Unknown')}</p>
                                <hr>
                                <p><strong>Description:</strong></p>
                                <p>{job.get('description', 'No description available')}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Apply Button
                        if job.get('related_links') and len(job['related_links']) > 0:
                            apply_url = job['related_links'][0]['link']
                            st.link_button("✨ Apply Now", apply_url)
                        
                        # Map (using approximate coordinates)
                        try:
                            # Note: In production, use geocoding API for precise coordinates
                            m = folium.Map(location=[40.7128, -74.0060], zoom_start=12)  # Default to NYC
                            folium.Marker(
                                [40.7128, -74.0060],  # Replace with actual coordinates
                                popup=job.get('company_name', 'Job Location'),
                                tooltip="Click for details"
                            ).add_to(m)
                            
                            st.markdown("### 📍 Location")
                            with st.container():
                                folium_static(m, width=700)
                        except Exception as e:
                            st.warning(f"Couldn't load map: {str(e)}")
                
                # --- Data Table View ---
                with st.expander("📊 View as Data Table"):
                    df = pd.DataFrame(jobs)[["title", "company_name", "location", "via"]]
                    st.dataframe(df.style.set_properties(**{
                        'background-color': '#f8f9fa',
                        'color': '#2c3e50',
                        'border': '1px solid #e0e0e0'
                    }))
                
            else:
                st.warning("No jobs found. Try adjusting your search criteria.")
        
        except requests.exceptions.RequestException as e:
            st.markdown(f"""
                <div class="error-box">
                    <strong>Error fetching jobs:</strong> {str(e)}<br><br>
                    Try these solutions:
                    <ul>
                        <li>Check your internet connection</li>
                        <li>Verify your SerpAPI key is valid</li>
                        <li>Try a more common job title/location</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

# --- Footer Section ---
st.markdown("""
    <div class="footer">
        <p>JobFinder Pro • Powered by SerpAPI • © 2023 All Rights Reserved</p>
    </div>
""", unsafe_allow_html=True)