import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List
from agents.cv_matcher import CVMatcherTool
from agents.whatsapp_agent import WhatsAppTool
from agents.scheduler_agent import SchedulerTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_execution.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('AgentExecutor')

class MockJobDescription:
    def __init__(self, title: str, description: str, requirements: List[str], location: str, employment_type: str):
        self.title = title
        self.description = description
        self.requirements = requirements
        self.location = location
        self.employment_type = employment_type

class AgentExecutor:
    def __init__(self):
        logger.info("Initializing Agent Executor")
        self.cv_matcher = CVMatcherTool()
        self.whatsapp_tool = WhatsAppTool()
        self.scheduler_tool = SchedulerTool()
        
        # Mock CV data
        self.mock_cvs = {
            "john_doe.pdf": {
                "name": "John Doe",
                "phone": "+971503609967",
                "email": "john@example.com",
                "skills": ["Python", "FastAPI", "AWS"],
                "experience": "5 years"
            },
            "jane_smith.pdf": {
                "name": "Jane Smith",
                "phone": "+923169985540",
                "email": "jane@example.com",
                "skills": ["Python", "Django", "Docker"],
                "experience": "3 years"
            }
        }
        
        logger.info("Agent Executor initialized successfully")

    async def execute_workflow(self, job_description: MockJobDescription):
        """Execute the complete recruitment workflow."""
        try:
            logger.info(f"Starting workflow for job: {job_description.title}")
            
            # Step 1: CV Matching
            logger.info("Step 1: Starting CV Matching")
            cv_matching_result = await self.cv_matcher.run(job_description.description)
            logger.info(f"CV Matching Result: {json.dumps(cv_matching_result, indent=2)}")
            
            if cv_matching_result.get("status") != "success":
                logger.error("CV matching failed")
                return
            
            top_candidates = cv_matching_result.get("candidates", [])
            logger.info(f"Found {len(top_candidates)} matching candidates")
            
            # Step 2: WhatsApp Communication
            logger.info("Step 2: Starting WhatsApp Communication")
            contacted_candidates = []
            for candidate in top_candidates[:5]:
                logger.info(f"Contacting candidate: {candidate['name']}")
                candidate["job_title"] = job_description.title
                
                whatsapp_result = await self.whatsapp_tool.run(candidate)
                logger.info(f"WhatsApp Result for {candidate['name']}: {json.dumps(whatsapp_result, indent=2)}")
                
                if whatsapp_result.get("status") == "success":
                    candidate["available_slots"] = whatsapp_result.get("available_slots", [])
                    contacted_candidates.append(candidate)
                    logger.info(f"Successfully contacted {candidate['name']}")
            
            # Step 3: Interview Scheduling
            logger.info("Step 3: Starting Interview Scheduling")
            scheduled_interviews = []
            for candidate in contacted_candidates:
                if candidate.get("available_slots"):
                    logger.info(f"Scheduling interview for {candidate['name']}")
                    scheduler_result = await self.scheduler_tool.run(candidate)
                    logger.info(f"Scheduler Result for {candidate['name']}: {json.dumps(scheduler_result, indent=2)}")
                    
                    if scheduler_result.get("status") == "success":
                        interview = scheduler_result.get("interview")
                        scheduled_interviews.append(interview)
                        
                        # Send confirmation
                        logger.info(f"Sending confirmation to {candidate['name']}")
                        candidate["interview"] = interview
                        confirmation_result = await self.whatsapp_tool.run(candidate)
                        logger.info(f"Confirmation Result: {json.dumps(confirmation_result, indent=2)}")
            
            # Final Summary
            logger.info("Workflow completed successfully")
            logger.info(f"Summary:")
            logger.info(f"- Total candidates matched: {len(top_candidates)}")
            logger.info(f"- Candidates contacted: {len(contacted_candidates)}")
            logger.info(f"- Interviews scheduled: {len(scheduled_interviews)}")
            
            return {
                "status": "success",
                "matched_candidates": len(top_candidates),
                "contacted_candidates": len(contacted_candidates),
                "scheduled_interviews": len(scheduled_interviews),
                "interviews": scheduled_interviews
            }
            
        except Exception as e:
            logger.error(f"Error in workflow execution: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

async def main():
    # Create a sample job description
    job = MockJobDescription(
        title="Senior Python Developer",
        description="We are looking for an experienced Python developer with strong backend skills.",
        requirements=["Python", "FastAPI", "AWS", "Docker"],
        location="Remote",
        employment_type="Full-time"
    )
    
    # Initialize and run the executor
    executor = AgentExecutor()
    result = await executor.execute_workflow(job)
    
    # Print final result
    print("\nFinal Result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 