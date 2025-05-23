import json
from pathlib import Path
from datetime import datetime
import pytz
import streamlit as st

# Constants
SAVED_JOBS_FILE = "saved_jobs.json"

class SavedJobsManager:
    def __init__(self):
        self.saved_jobs = self._load_saved_jobs()
    
    def _load_saved_jobs(self):
        """Load saved jobs from JSON file"""
        if Path(SAVED_JOBS_FILE).exists():
            with open(SAVED_JOBS_FILE, "r") as f:
                saved_jobs = json.load(f)
                # Add missing application_status to old entries
                for job_id, job_data in saved_jobs.items():
                    if 'application_status' not in job_data:
                        job_data['application_status'] = "Not Applied"
                return saved_jobs
        return {}
    
    def _save_jobs(self):
        """Save jobs to JSON file"""
        with open(SAVED_JOBS_FILE, "w") as f:
            json.dump(self.saved_jobs, f, indent=2)
    
    def save_job(self, job):
        """Save a job to the collection"""
        job_id = f"{job.get('title', '')}_{job.get('company_name', '')}".replace(" ", "_")
        self.saved_jobs[job_id] = {
            "job": job,
            "saved_at": datetime.now(pytz.utc).isoformat(),
            "notes": "",
            "application_status": "Not Applied"
        }
        self._save_jobs()
        return job_id
    
    def remove_job(self, job_id):
        """Remove a job from saved jobs"""
        if job_id in self.saved_jobs:
            del self.saved_jobs[job_id]
            self._save_jobs()
            return True
        return False
    
    def update_job_notes(self, job_id, notes):
        """Update notes for a saved job"""
        if job_id in self.saved_jobs:
            self.saved_jobs[job_id]["notes"] = notes
            self._save_jobs()
            return True
        return False
    
    def update_application_status(self, job_id, status):
        """Update application status for a job"""
        if job_id in self.saved_jobs:
            self.saved_jobs[job_id]["application_status"] = status
            self._save_jobs()
            return True
        return False
    
    def get_job(self, job_id):
        """Get a specific saved job"""
        return self.saved_jobs.get(job_id)
    
    def get_all_jobs(self):
        """Get all saved jobs"""
        return self.saved_jobs
    
    def apply_to_job(self, job_id, cover_letter=None):
        """
        Simulate applying to a job
        In a real app, this would integrate with job boards or company websites
        """
        if job_id not in self.saved_jobs:
            return False, "Job not found in saved jobs"
        
        # Update application status
        self.update_application_status(job_id, "Applied")
        
        job = self.saved_jobs[job_id]["job"]
        return True, f"Application submitted for {job.get('title', '')} at {job.get('company_name', '')}"