from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from agents.cv_matcher import CVMatcherTool
from agents.whatsapp_agent import WhatsAppTool
from agents.scheduler_agent import SchedulerTool

# Load environment variables
load_dotenv()

app = FastAPI(title="AI Recruiter Agent")

class JobDescription(BaseModel):
    title: str
    description: str
    requirements: List[str]
    location: str
    employment_type: str

class Candidate(BaseModel):
    name: str
    phone: str
    email: str
    cv_path: str
    match_score: float
    available_slots: Optional[List[str]] = None
    job_title: Optional[str] = None

# Initialize tools
cv_matcher = CVMatcherTool()
whatsapp_tool = WhatsAppTool()
scheduler_tool = SchedulerTool()

@app.post("/process-job")
async def process_job(job: JobDescription):
    try:
        # Step 1: Match CVs with job description
        cv_matching_result = await cv_matcher.run(job.description)
        if cv_matching_result.get("status") != "success":
            raise HTTPException(status_code=500, detail="CV matching failed")
        
        top_candidates = cv_matching_result.get("candidates", [])
        
        # Step 2: Contact candidates via WhatsApp
        contacted_candidates = []
        for candidate in top_candidates[:5]:  # Top 5 candidates
            candidate["job_title"] = job.title
            whatsapp_result = await whatsapp_tool.run(candidate)
            if whatsapp_result.get("status") == "success":
                candidate["available_slots"] = whatsapp_result.get("available_slots", [])
                contacted_candidates.append(candidate)
        
        # Step 3: Schedule interviews
        scheduled_interviews = []
        for candidate in contacted_candidates:
            if candidate.get("available_slots"):
                scheduler_result = await scheduler_tool.run(candidate)
                if scheduler_result.get("status") == "success":
                    interview = scheduler_result.get("interview")
                    scheduled_interviews.append(interview)
                    
                    # Send confirmation via WhatsApp
                    candidate["interview"] = interview
                    await whatsapp_tool.run(candidate)
        
        return {
            "status": "success",
            "matched_candidates": len(top_candidates),
            "contacted_candidates": len(contacted_candidates),
            "scheduled_interviews": len(scheduled_interviews),
            "interviews": scheduled_interviews
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 