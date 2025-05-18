import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv
import os

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("SERPAPI_KEY")

# --- Streamlit UI ---
st.title("🔍 AI Job Finder")
st.write("Find jobs from Google Jobs in seconds!")

# User inputs
job_title = st.text_input("Job Title", "Software Engineer")
location = st.text_input("Location", "New York")

if st.button("Search Jobs"):
    # Fetch jobs from SerpAPI
    params = {
        "engine": "google_jobs",
        "q": job_title,
        "location": location,
        "hl": "en",
        "api_key": API_KEY
    }
    response = requests.get("https://serpapi.com/search", params=params).json()

    # Display results
    jobs = response.get("jobs_results", [])
    if jobs:
        st.success(f"Found {len(jobs)} jobs!")
        # Show as a table
        df = pd.DataFrame(jobs)[["title", "company_name", "location", "via"]]
        st.dataframe(df)
    else:
        st.error("No jobs found. Try another search!")