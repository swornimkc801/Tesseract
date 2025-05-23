import streamlit as st
import requests
import pandas as pd
import os
import time
import traceback
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import json
from pathlib import Path
import base64
import tempfile
from datetime import datetime
import pytz
import re
from PyPDF2 import PdfReader, PdfWriter
import torch
from transformers import pipeline
from huggingface_hub import InferenceClient
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from transformers import pipeline
from huggingface_hub import InferenceClient
from saved_jobs import SavedJobsManager
from resume_builder import ProfessionalResumeBuilder
from logo import show_animated_logo
# --- Existing Imports ---
import streamlit as st
import requests
import pandas as pd
import os
import time
import traceback
# ... (your other imports)

# +++ ADD DEBUG CODE HERE +++
print("\n=== DEBUGGING SECRETS ===")
print("Secrets available:", list(st.secrets.keys()))
print("SERPAPI_KEY exists:", "SERPAPI_KEY" in st.secrets)
print("HF_TOKEN exists:", "HF_TOKEN" in st.secrets)

# --- Rest of your existing code ---
API_KEY = st.secrets["SERPAPI_KEY"]
HF_TOKEN = st.secrets["HF_TOKEN"]

if not HF_TOKEN:
    st.error("""
    ❌ Hugging Face token not found. Please:
    1. Get token from https://huggingface.co/settings/tokens
    2. Add to .env file as: HF_TOKEN=your_token_here
    3. Ensure .env is in the same folder as your script
    """)

# --- Page Configuration ---
st.set_page_config(
    page_title="JobFinder Pro+",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

show_animated_logo()
# --- Environment Setup ---
try:
    # Load secrets
    API_KEY = st.secrets.get("SERPAPI_KEY")
    HF_TOKEN = st.secrets.get("HF_TOKEN")
    
    if not API_KEY:
        st.error("❌ SERPAPI_KEY not found in secrets")
    if not HF_TOKEN:
        st.warning("ℹ️ HF_TOKEN not found, some features may be limited")
except Exception as e:
    st.error(f"🚨 Critical Error: {str(e)}")
    st.code(traceback.format_exc())
    st.stop()  # Stop execution if env setup fails

# --- AI Model Initialization ---
@st.cache_resource
def load_ai_model():
    try:
        return pipeline(
            "text-generation",
            model="facebook/blenderbot-400M-distill",  # Smaller free model
            device="cpu",
            truncation=True,
            max_length=500
        )
    except Exception as e:
        st.error(f"⚠️ Failed to load AI model: {str(e)}")
        return None

local_ai = load_ai_model()
hf_client = InferenceClient(token=HF_TOKEN) if HF_TOKEN else None


# --- PyTorch CPU Optimization ---
import torch
torch.set_num_threads(4)  # Limit CPU threads for better performance

# --- Constants and Configuration ---
CACHE_FILE = "geocode_cache.json"
SAVED_JOBS_FILE = "saved_jobs.json"
USER_PROFILES_FILE = "user_profiles.json"
COUNTRIES = {
    "Australia": "au",
    "United States": "us",
    "Canada": "ca",
    "United Kingdom": "uk",
    "Germany": "de",
    "France": "fr",
    "India": "in",
    "Japan": "jp",
    "Singapore": "sg",
    "New Zealand": "nz"
}

# --- File Management Functions ---
def load_cache():
    if Path(CACHE_FILE).exists():
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def load_saved_jobs():
    if Path(SAVED_JOBS_FILE).exists():
        with open(SAVED_JOBS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_jobs(jobs):
    with open(SAVED_JOBS_FILE, "w") as f:
        json.dump(jobs, f)

def load_user_profiles():
    if Path(USER_PROFILES_FILE).exists():
        with open(USER_PROFILES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_profiles(profiles):
    with open(USER_PROFILES_FILE, "w") as f:
        json.dump(profiles, f)

# Initialize data stores
geocode_cache = load_cache()
# Initialize SavedJobsManager
jobs_manager = SavedJobsManager()
user_profiles = load_user_profiles()
# Initialize resume builder
resume_builder = ProfessionalResumeBuilder()

# --- Geocoding Setup ---
geolocator = Nominatim(user_agent="job_finder_pro")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

def get_coordinates(location_name):
    """Get latitude and longitude for a location name with caching"""
    if location_name in geocode_cache:
        return tuple(geocode_cache[location_name])
    
    try:
        location = geocode(location_name)
        if location:
            coords = (location.latitude, location.longitude)
            geocode_cache[location_name] = coords
            save_cache(geocode_cache)
            return coords
        return (0, 0)
    except Exception as e:
        st.warning(f"Geocoding error for {location_name}: {str(e)}")
        return (0, 0)

# --- PDF Functions ---
def create_pdf_resume(user_data):
    """Create PDF resume using PyPDF2 and ReportLab"""
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    # Set font and starting position
    can.setFont("Helvetica-Bold", 16)
    y_position = 750
    
    # Personal Information
    can.drawString(72, y_position, user_data['name'])
    y_position -= 20
    
    can.setFont("Helvetica", 12)
    can.drawString(72, y_position, user_data['email'])
    y_position -= 15
    can.drawString(72, y_position, user_data['phone'])
    y_position -= 30
    
    # Summary
    can.setFont("Helvetica-Bold", 14)
    can.drawString(72, y_position, "Professional Summary")
    y_position -= 20
    can.setFont("Helvetica", 12)
    
    # Handle multi-line summary
    summary_lines = []
    words = user_data['summary'].split()
    line = ""
    for word in words:
        if len(line) + len(word) < 80:
            line += word + " "
        else:
            summary_lines.append(line)
            line = word + " "
    if line:
        summary_lines.append(line)
    
    for line in summary_lines:
        can.drawString(72, y_position, line)
        y_position -= 15
    y_position -= 15
    
    # Experience
    can.setFont("Helvetica-Bold", 14)
    can.drawString(72, y_position, "Work Experience")
    y_position -= 20
    
    for exp in user_data['experience']:
        can.setFont("Helvetica-Bold", 12)
        can.drawString(72, y_position, f"{exp['title']} at {exp['company']}")
        y_position -= 15
        
        can.setFont("Helvetica-Oblique", 10)
        can.drawString(72, y_position, f"{exp['start']} - {exp['end']}")
        y_position -= 15
        
        can.setFont("Helvetica", 12)
        desc_lines = []
        words = exp['description'].split()
        line = ""
        for word in words:
            if len(line) + len(word) < 80:
                line += word + " "
            else:
                desc_lines.append(line)
                line = word + " "
        if line:
            desc_lines.append(line)
        
        for line in desc_lines:
            can.drawString(72, y_position, line)
            y_position -= 15
        y_position -= 10
    
    # Education
    can.setFont("Helvetica-Bold", 14)
    can.drawString(72, y_position, "Education")
    y_position -= 20
    
    can.setFont("Helvetica", 12)
    for edu in user_data['education']:
        can.drawString(72, y_position, f"{edu['degree']}, {edu['institution']} ({edu['year']})")
        y_position -= 15
    
    # Skills
    can.setFont("Helvetica-Bold", 14)
    can.drawString(72, y_position, "Skills")
    y_position -= 20
    
    can.setFont("Helvetica", 12)
    skills = ', '.join(user_data['skills'])
    skill_lines = []
    words = skills.split()
    line = ""
    for word in words:
        if len(line) + len(word) < 80:
            line += word + " "
        else:
            skill_lines.append(line)
            line = word + " "
    if line:
        skill_lines.append(line)
    
    for line in skill_lines:
        can.drawString(72, y_position, line)
        y_position -= 15
    
    # Save the PDF
    can.save()
    
    # Move to beginning of BytesIO buffer
    packet.seek(0)
    new_pdf = PdfReader(packet)
    
    # Create output PDF
    output = BytesIO()
    writer = PdfWriter()
    writer.add_page(new_pdf.pages[0])
    writer.write(output)
    
    return output.getvalue()

def extract_text_from_pdf(uploaded_file):
    """Extract text from uploaded PDF"""
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# --- AI Assistant Functions ---
def generate_ai_response(prompt, context=""):
    """Generate response using BlenderBot model with resume-focused tuning"""
    try:
        # Enhanced prompt template for career advice
        full_prompt = f"""<<SYS>>You are TESSERACT, an expert career coach specializing in resumes and job hunting. Provide:
        - Concise, actionable advice
        - Industry-specific best practices
        - Professional tone
        - Focus on resumes, cover letters, and interviews
        <</SYS>>
        
        [CONTEXT]
        {context}
        
        [QUESTION]
        {prompt}
        
        [ANSWER]"""
        
        # Generate response using the local BlenderBot model
        if "chatbot" in st.session_state and "conversation" in st.session_state:
            st.session_state.conversation.add_user_input(full_prompt)
            st.session_state.chatbot(st.session_state.conversation)
            response = st.session_state.conversation.generated_responses[-1]
            
            # Clean the output
            return response.split("[ANSWER]")[-1].strip()
        else:
            return "⚠️ AI assistant is not properly initialized. Please refresh the page."
    
    except Exception as e:
        return f"⚠️ I'm having trouble generating a response. Error: {str(e)}"

def analyze_resume_for_job(resume_text, job_description):
    prompt = f"""
    Analyze how well this resume matches the job description and suggest improvements.
    
    Resume:
    {resume_text}
    
    Job Description:
    {job_description}
    
    Provide:
    1. Match score (0-100%)
    2. 3 key strengths
    3. 3 areas for improvement
    4. Suggested resume tweaks
    """
    return generate_ai_response(prompt)

def generate_cover_letter(resume_text, job_description):
    prompt = f"""
    Write a professional cover letter based on this resume and job description.
    
    Resume:
    {resume_text}
    
    Job Description:
    {job_description}
    
    The cover letter should:
    - Be 3-4 paragraphs
    - Highlight relevant skills/experience
    - Show enthusiasm for the role
    - Be tailored to the job
    """
    return generate_ai_response(prompt)

# --- Notification Functions ---
def check_for_new_jobs(user_profile):
    """Check if new jobs matching user criteria have been posted"""
    return []

def send_notification(message):
    """In a real app, this would send email/push notifications"""
    st.session_state.notifications.append({
        "message": message,
        "time": datetime.now(pytz.utc).isoformat(),
        "read": False
    })



# --- CSS Styling ---
st.markdown("""
<style>
    /* ===== NEON LIGHT GREEN & BLACK THEME ===== */
    :root {
        --neon-green: #00FF7F;
        --dark-bg: #0D0208;
        --text-white: #F0F8FF;
        --hover-glow: 0 0 15px #00FF7F;
    }

    /* Main Background */
    .stApp {
        background-color: var(--dark-bg);
    }

    /* Header */
    .header {
        background: linear-gradient(90deg, #0A0A0A 0%, var(--dark-bg) 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid var(--neon-green);
        box-shadow: 0 0 10px rgba(0, 255, 127, 0.2);
    }

    /* Chat Messages */
    .chat-message {
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        max-width: 80%;
    }
    .user-message {
        background-color: rgba(0, 255, 127, 0.15);
        margin-left: auto;
        margin-right: 0;
        border: 1px solid var(--neon-green);
        color: var(--text-white);
    }
    .assistant-message {
        background-color: rgba(13, 2, 8, 0.7);
        margin-left: 0;
        margin-right: auto;
        border: 1px solid #555;
        color: var(--text-white);
    }

    /* Resume Section */
    .resume-section {
        background-color: rgba(13, 2, 8, 0.8);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        box-shadow: 0 0 8px rgba(0, 255, 127, 0.1);
        border: 1px solid var(--neon-green);
        color: var(--text-white);
    }

    /* Tabs */
    .tab-content {
        padding: 15px;
        background-color: rgba(13, 2, 8, 0.7);
        border-radius: 0 0 10px 10px;
        box-shadow: 0 2px 4px rgba(0, 255, 127, 0.1);
        color: var(--text-white);
    }

    /* Notifications */
    .notification {
        padding: 10px;
        border-left: 4px solid var(--neon-green);
        background-color: rgba(13, 2, 8, 0.9);
        margin-bottom: 10px;
        border-radius: 4px;
        color: var(--text-white);
        transition: all 0.3s ease;
    }
    .notification.unread {
        border-left-color: #00F5FF;
        box-shadow: 0 0 10px rgba(0, 245, 255, 0.2);
    }
    .notification:hover {
        transform: translateX(5px);
        box-shadow: var(--hover-glow);
    }

    /* Job Cards */
    .job-card {
        padding: 15px;
        background-color: rgba(13, 2, 8, 0.7);
        border-radius: 8px;
        margin-bottom: 15px;
        border: 1px solid #333;
        transition: all 0.3s ease;
    }
    .job-card:hover {
        border-color: var(--neon-green);
        box-shadow: var(--hover-glow);
        transform: translateY(-3px);
    }
    .job-title {
        font-weight: bold;
        font-size: 1.1em;
        margin-bottom: 5px;
        color: var(--neon-green);
    }
    .company-name {
        font-style: italic;
        margin-bottom: 5px;
        color: #00F5FF;
    }

    /* Footer */
    .footer {
        text-align: center;
        margin-top: 30px;
        padding: 10px;
        color: var(--neon-green);
        font-size: 0.9em;
        border-top: 1px solid var(--neon-green);
    }

    /* Buttons (Added extra) */
    .stButton>button {
        background-color: var(--dark-bg) !important;
        color: var(--neon-green) !important;
        border: 1px solid var(--neon-green) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        box-shadow: var(--hover-glow);
        color: var(--dark-bg) !important;
        background-color: var(--neon-green) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "💬 AI Assistant"
if 'selected_job' not in st.session_state:
    st.session_state.selected_job = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'notifications' not in st.session_state:
    st.session_state.notifications = []
if 'resume_data' not in st.session_state:
    st.session_state.resume_data = {
        "name": "",
        "email": "",
        "phone": "",
        "summary": "",
        "experience": [],
        "education": [],
        "skills": []
    }
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'resume_file' not in st.session_state:
    st.session_state.resume_file = None
if 'generated_cover_letter' not in st.session_state:
    st.session_state.generated_cover_letter = ""

# --- Header Section ---
st.markdown("""
    <div class="header">
        <h1 style="color:white; margin:0;">🔍 JobFinder Pro+</h1>
        <p style="color:white; opacity:0.8; margin:0;">The Next-Gen AI-Powered Career Revolution</p>
    </div>
""", unsafe_allow_html=True)

# --- Main App Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Job Search", 
    "💬 AI Assistant", 
    "📄 Resume Builder", 
    "🔔 Notifications", 
    "💾 Saved Jobs"
])

with tab1:
    # --- Job Search Interface ---
    with st.container():
        col1, col2 = st.columns([3, 2])
        
        with col1:
            job_title = st.text_input("Job Title", "Software Engineer", key="job_title")
        
        with col2:
            default_country = "Australia"
            selected_country = st.selectbox(
                "Country",
                list(COUNTRIES.keys()),
                index=list(COUNTRIES.keys()).index(default_country) if default_country in COUNTRIES else 0
            )

    with st.container():
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            location = st.text_input(
                "Location", 
                "Sydney",
                key="location",
                help="Enter city, region, or postal code."
            )
        
        with col2:
            radius_options = {
                "Exact location only": 0,
                "Within 5 km": 5,
                "Within 10 km": 10,
                "Within 25 km": 25,
                "Within 50 km": 50,
                "Within 100 km": 100
            }
            radius = st.selectbox(
                "Search Radius",
                options=list(radius_options.keys()),
                index=2
            )
            radius_km = radius_options[radius]
        
        with col3:
            st.write("")  # Spacer
            st.write("")  # Spacer
            search_clicked = st.button("🚀 Find Jobs", key="search_button")

    # --- Job Results Display ---
    if search_clicked:
        with st.spinner('Searching for the best jobs...'):
            # Simulate job search results
            time.sleep(2)
            st.session_state.selected_job = {
                "title": "Senior Software Engineer",
                "company_name": "Tech Corp Inc.",
                "location": "Sydney, NSW",
                "via": "LinkedIn",
                "description": "We're looking for a skilled software engineer with 5+ years experience in Python and web development. Responsibilities include developing new features, maintaining existing codebase, and collaborating with cross-functional teams.",
                "posted": "2 days ago"
            }
            st.success("Found 15 matching jobs!")

    # --- Job Details Section with Save Option ---
    if st.session_state.selected_job:
        job = st.session_state.selected_job
        job_id = f"{job.get('title', '')}_{job.get('company_name', '')}".replace(" ", "_")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
                <div class="job-card">
                    <div class="job-title">{job.get('title', 'N/A')}</div>
                    <div class="company-name">{job.get('company_name', 'N/A')}</div>
                    <div class="location">{job.get('location', 'N/A')}</div>
                    <div class="via">via {job.get('via', 'Unknown')}</div>
                    <p><strong>Description:</strong></p>
                    <p>{job.get('description', 'No description available')}</p>
                    <p><small>Posted: {job.get('posted', 'Date not available')}</small></p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("💾 Save Job"):
                job_id=jobs_manager.save_job(job)
                st.success("Job Saved")
    
            
            if st.button("📄 Generate Cover Letter"):
                if 'resume_text' in st.session_state and st.session_state.resume_text:
                    with st.spinner('Generating cover letter...'):
                        cover_letter = generate_cover_letter(
                            st.session_state.resume_text,
                            job.get('description', '')
                        )
                        st.session_state.generated_cover_letter = cover_letter
                        st.rerun()  # Use this instead
                else:
                    st.warning("Please upload or create a resume first")

            if 'generated_cover_letter' in st.session_state:
                st.download_button(
                    label="📥 Download Cover Letter",
                    data=st.session_state.generated_cover_letter,
                    file_name=f"cover_letter_{job_id}.txt",
                    mime="text/plain"
                )

with tab2:
    st.markdown("### 🤖 Career Assistant - TESSERACT")
    
    # Initialize the chatbot in session state if not exists
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Hello! I'm TESSERACT, your AI career coach. "
             "Ask me anything about resumes, cover letters, or job interviews!"}
        ]
    
    # Display chat messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Quick action buttons
    with st.expander("💡 Quick Career Questions"):
        cols = st.columns(2)
        with cols[0]:
            if st.button("Best resume format"):
                st.session_state.chat_history.append({"role": "user", "content": "What's the best resume format for my industry?"})
        with cols[1]:
            if st.button("ATS optimization"):
                st.session_state.chat_history.append({"role": "user", "content": "How can I optimize my resume for ATS systems?"})
        
        cols = st.columns(2)
        with cols[0]:
            if st.button("Cover letter tips"):
                st.session_state.chat_history.append({"role": "user", "content": "What makes a strong cover letter?"})
        with cols[1]:
            if st.button("Interview prep"):
                st.session_state.chat_history.append({"role": "user", "content": "What are the top interview preparation tips?"})

    # Main chat input
    if prompt := st.chat_input("Ask your career question..."):
        st.session_state.active_tab = "💬 AI Assistant"
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.spinner("Researching..."):
            # Add resume context if available
            context = ""
            if 'resume_text' in st.session_state and st.session_state.resume_text:
                context = f"Resume Context:\n{st.session_state.resume_text[:500]}..."
            
            # Generate response using either local model or Hugging Face Inference API
            if HF_TOKEN:  # If you have a Hugging Face token
                try:
                    response = hf_client.chat_completion(
                        messages=[{"role": m["role"], "content": m["content"]} 
                                 for m in st.session_state.chat_history[-6:]],
                        model="HuggingFaceH4/zephyr-7b-beta",
                        max_tokens=500
                    )
                    ai_response = response.choices[0].message.content
                except Exception as e:
                    st.error(f"API Error: {str(e)}")
                    ai_response = "I'm having trouble connecting to the AI service. Please try again later."
            elif local_ai:  # Fallback to local model
                full_prompt = f"""<<SYS>>You are TESSERACT, an expert career coach. Provide concise, actionable advice.<</SYS>>
                
                [CONTEXT]
                {context}
                
                [QUESTION]
                {prompt}"""
                
                response = local_ai(full_prompt, max_length=500, do_sample=True)
                ai_response = response[0]['generated_text'].split('[QUESTION]')[-1].strip()
            else:
                ai_response = "AI assistant is not available. Please check your configuration."
            
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        
        st.rerun()

    # Clear chat button
    if st.button("🗑️ Clear Chat History", type="secondary"):
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Chat history cleared. How can I help with your career questions today?"}
        ]
        st.rerun()


with tab3:
    # --- Professional Resume Builder ---
    st.markdown("### 📄 Professional Resume Builder")
    
    # Template selection
    templates = resume_builder.get_resume_templates()
    selected_template = st.selectbox(
        "Choose a resume template",
        list(templates.keys()),
        index=0
    )
    
    # Resume form
    with st.form("resume_form"):
        st.session_state.resume_data["name"] = st.text_input(
            "Full Name", 
            st.session_state.resume_data["name"],
            placeholder="John Doe"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.resume_data["email"] = st.text_input(
                "Email", 
                st.session_state.resume_data["email"],
                placeholder="john.doe@example.com"
            )
        with col2:
            st.session_state.resume_data["phone"] = st.text_input(
                "Phone", 
                st.session_state.resume_data["phone"],
                placeholder="(123) 456-7890"
            )
        
        st.session_state.resume_data["summary"] = st.text_area(
            "Professional Summary", 
            st.session_state.resume_data["summary"],
            placeholder="Experienced professional with 5+ years in...",
            height=100
        )
        
        # Experience section
        st.markdown("### Work Experience")
        for i, exp in enumerate(st.session_state.resume_data["experience"]):
            exp_col1, exp_col2 = st.columns([3, 1])
            
            with exp_col1:
                st.session_state.resume_data["experience"][i]["title"] = st.text_input(
                    f"Job Title #{i+1}", 
                    exp["title"],
                    key=f"exp_title_{i}",
                    placeholder="Senior Software Engineer"
                )
                
                st.session_state.resume_data["experience"][i]["company"] = st.text_input(
                    f"Company #{i+1}", 
                    exp["company"],
                    key=f"exp_company_{i}",
                    placeholder="Tech Corporation Inc."
                )
                
                st.session_state.resume_data["experience"][i]["description"] = st.text_area(
                    f"Description #{i+1}", 
                    exp["description"],
                    key=f"exp_desc_{i}",
                    placeholder="• Led team of 5 developers...\n• Implemented new features...",
                    height=100
                )
            
            with exp_col2:
                years = st.text_input(
                    f"Years #{i+1}", 
                    f"{exp['start']}-{exp['end']}" if exp['start'] else "",
                    key=f"exp_years_{i}",
                    placeholder="2020-2023"
                )
                start_end = years.split("-")
                if len(start_end) == 2:
                    st.session_state.resume_data["experience"][i]["start"] = start_end[0].strip()
                    st.session_state.resume_data["experience"][i]["end"] = start_end[1].strip()
        
        # Add experience button
        if st.form_submit_button("➕ Add Another Position"):
            st.session_state.resume_data["experience"].append({
                "title": "",
                "company": "",
                "start": "",
                "end": "",
                "description": ""
            })
            st.rerun()
        
        # Education section
        st.markdown("### Education")
        for i, edu in enumerate(st.session_state.resume_data["education"]):
            edu_col1, edu_col2 = st.columns([3, 1])
            
            with edu_col1:
                st.session_state.resume_data["education"][i]["degree"] = st.text_input(
                    f"Degree #{i+1}", 
                    edu["degree"],
                    key=f"edu_degree_{i}",
                    placeholder="Bachelor of Science in Computer Science"
                )
                
                st.session_state.resume_data["education"][i]["institution"] = st.text_input(
                    f"Institution #{i+1}", 
                    edu["institution"],
                    key=f"edu_institution_{i}",
                    placeholder="University of Technology"
                )
            
            with edu_col2:
                st.session_state.resume_data["education"][i]["year"] = st.text_input(
                    f"Year #{i+1}", 
                    edu["year"],
                    key=f"edu_year_{i}",
                    placeholder="2018"
                )
        
        # Add education button
        if st.form_submit_button("➕ Add Another Education"):
            st.session_state.resume_data["education"].append({
                "degree": "",
                "institution": "",
                "year": ""
            })
            st.rerun()
        
        # Skills section
        st.markdown("### Skills")
        skills_text = ", ".join(st.session_state.resume_data["skills"])
        new_skills = st.text_input(
            "List your skills (comma separated)", 
            skills_text,
            placeholder="Python, JavaScript, Project Management, etc."
        )
        st.session_state.resume_data["skills"] = [s.strip() for s in new_skills.split(",") if s.strip()]
        
        # Form submit button
        if st.form_submit_button("💾 Save & Generate Resume"):
            st.success("Resume saved!")
            
            # Generate PDF
            try:
                template_key = templates[selected_template]
                pdf_bytes = resume_builder.create_resume_pdf(
                    st.session_state.resume_data,
                    template=template_key
                )
                
                # Show download button
                file_name = f"{st.session_state.resume_data['name'].replace(' ', '_')}_Resume.pdf"
                resume_builder.create_download_button(pdf_bytes, file_name)
                
                # Store text version for AI analysis
                resume_text = f"""
                Name: {st.session_state.resume_data["name"]}
                Contact: {st.session_state.resume_data["email"]} | {st.session_state.resume_data["phone"]}
                
                Summary:
                {st.session_state.resume_data["summary"]}
                
                Experience:
                {chr(10).join([f"{exp['title']} at {exp['company']} ({exp['start']}-{exp['end']}): {exp['description']}" 
                 for exp in st.session_state.resume_data["experience"]])}
                
                Education:
                {chr(10).join([f"{edu['degree']}, {edu['institution']} ({edu['year']})" 
                 for edu in st.session_state.resume_data["education"]])}
                
                Skills:
                {', '.join(st.session_state.resume_data["skills"])}
                """
                st.session_state.resume_text = resume_text
                
            except Exception as e:
                st.error(f"Failed to generate PDF: {str(e)}")

with tab4:
    # --- Notifications Center ---
    st.markdown("### 🔔 Notifications")
    
    if not st.session_state.notifications:
        st.info("You have no notifications yet.")
    else:
        for i, notification in enumerate(st.session_state.notifications):
            read_class = "" if notification['read'] else "unread"
            st.markdown(f"""
                <div class="notification {read_class}">
                    <strong>{notification['time']}</strong><br>
                    {notification['message']}
                </div>
            """, unsafe_allow_html=True)
            
            if not notification['read']:
                if st.button(f"Mark as read #{i+1}"):
                    st.session_state.notifications[i]['read'] = True
                    st.rerun()  # Use this instead
    
    # Simulate new job notifications (demo only)
    if st.button("Simulate New Job Alert (Demo)"):
        send_notification("3 new Data Analyst jobs matching your profile were posted!")
        st.rerun()  # Use this instead

with tab5:
    # --- Saved Jobs ---
    st.markdown("### 💾 Saved Jobs")
    
    saved_jobs = jobs_manager.get_all_jobs()
    
    if not saved_jobs:
        st.info("You haven't saved any jobs yet.")
    else:
        for job_id, saved_job in saved_jobs.items():
            job = saved_job['job']
            
            # Create expandable section for each job
            with st.expander(f"{job.get('title', 'N/A')} at {job.get('company_name', 'N/A')} - {saved_job['application_status']}"):
                st.markdown(f"""
                    <div class="job-card">
                        <div class="job-title">{job.get('title', 'N/A')}</div>
                        <div class="company-name">{job.get('company_name', 'N/A')}</div>
                        <div class="location">{job.get('location', 'N/A')}</div>
                        <div class="via">via {job.get('via', 'Unknown')}</div>
                        <p><strong>Status:</strong> {saved_job['application_status']}</p>
                        <p><small>Saved on: {saved_job['saved_at']}</small></p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Job description
                st.markdown("**Job Description:**")
                st.write(job.get('description', 'No description available'))
                
                # User notes
                notes = st.text_area("Your Notes", 
                                   saved_job.get('notes', ''), 
                                   key=f"notes_{job_id}")
                
                if notes != saved_job.get('notes', ''):
                    jobs_manager.update_job_notes(job_id, notes)
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"📄 Apply Now", key=f"apply_{job_id}"):
                        # Set the job as selected for application
                        st.session_state.selected_job = job
                        st.session_state.applying_for_job_id = job_id
                        st.rerun()
                
                with col2:
                    if st.button(f"✏️ Generate Cover Letter", key=f"cover_{job_id}"):
                        if 'resume_text' in st.session_state and st.session_state.resume_text:
                            with st.spinner('Generating cover letter...'):
                                cover_letter = generate_cover_letter(
                                    st.session_state.resume_text,
                                    job.get('description', '')
                                )
                                st.session_state.generated_cover_letter = cover_letter
                                st.rerun()
                        else:
                            st.warning("Please upload or create a resume first")
                
                with col3:
                    if st.button(f"🗑️ Remove", key=f"remove_{job_id}"):
                        jobs_manager.remove_job(job_id)
                        st.success("Job removed from saved jobs!")
                        st.rerun()
                
                # If we're applying for this specific job
                if st.session_state.get('applying_for_job_id') == job_id:
                    st.markdown("---")
                    st.markdown("### 🚀 Apply for This Position")
                    
                    # Display application form
                    with st.form(f"application_form_{job_id}"):
                        # Pre-fill with user info if available
                        name = st.text_input("Full Name", st.session_state.resume_data.get("name", ""))
                        email = st.text_input("Email", st.session_state.resume_data.get("email", ""))
                        phone = st.text_input("Phone", st.session_state.resume_data.get("phone", ""))
                        
                        # Use generated cover letter or create new one
                        if 'generated_cover_letter' in st.session_state:
                            cover_letter = st.text_area("Cover Letter", 
                                                      st.session_state.generated_cover_letter,
                                                      height=300)
                        else:
                            cover_letter = st.text_area("Cover Letter", height=300)
                        
                        # Resume upload
                        resume_file = st.file_uploader("Upload Resume (PDF)", 
                                                      type=["pdf"],
                                                      key=f"resume_upload_{job_id}")
                        
                        # Submit application
                        submitted = st.form_submit_button("Submit Application")
                        
                        if submitted:
                            # Validate form
                            if not all([name, email, cover_letter]):
                                st.error("Please fill in all required fields")
                            else:
                                # In a real app, you would submit to the job board/company here
                                success, message = jobs_manager.apply_to_job(job_id, cover_letter)
                                if success:
                                    st.success(message)
                                    del st.session_state.applying_for_job_id
                                    st.rerun()
                                else:
                                    st.error(message)

# --- Footer Section ---
st.markdown("""
    <div class="footer">
        <p>JobFinder Pro+ • Powered by Tesseract • © 2025 All Rights Reserved</p>
    </div>
""", unsafe_allow_html=True)




