import os
from typing import List, Dict
from .base_tool import LLMTool
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()

class WhatsAppTool(LLMTool):
    name: str = "WhatsApp Communication Tool"
    description: str = "A tool that handles WhatsApp communication with candidates for interview scheduling"
    arg: str = "A candidate object containing contact information and interview details"
    whatsapp_token: str = Field(default="")

    def __init__(self, **data):
        super().__init__(**data)
        if not self.whatsapp_token:
            self.whatsapp_token = os.getenv("WHATSAPP_TOKEN", "")
        
    async def contact_candidate(self, candidate: dict) -> Dict:
        """Contact candidate via WhatsApp and get available slots."""
        system_prompt = """You are a professional recruiter. Your task is to generate a WhatsApp message to contact a candidate for an interview.
        The message should be friendly, professional, and ask for 3-5 available time slots for an initial screening interview."""
        
        prompt = f"""
        Generate a WhatsApp message for the following candidate:
        Name: {candidate['name']}
        """
        
        message = await self.generate_response(prompt, system_prompt)
        
        # In a real implementation, you would send this message via WhatsApp API
        # For now, we'll simulate the response
        return {
            "success": True,
            "message": message,
            "available_slots": [
                "2024-03-20T10:00:00",
                "2024-03-20T14:00:00",
                "2024-03-21T11:00:00"
            ]
        }
    
    async def send_interview_confirmation(self, candidate: dict, interview: dict) -> bool:
        """Send interview confirmation via WhatsApp."""
        system_prompt = """You are a professional recruiter. Your task is to generate a confirmation message for a scheduled interview.
        The message should include the interview date, time, format, and any preparation needed."""
        
        prompt = f"""
        Generate a confirmation message for the following interview:
        Candidate: {candidate['name']}
        Date: {interview['date']}
        Time: {interview['time']}
        Format: {interview['format']}
        """
        
        message = await self.generate_response(prompt, system_prompt)
        
        # In a real implementation, you would send this message via WhatsApp API
        return True

    async def run(self, candidate: dict) -> str:
        """Main entry point for the WhatsApp tool."""
        if "interview" in candidate:
            # If interview details are provided, send confirmation
            success = await self.send_interview_confirmation(candidate, candidate["interview"])
            return {
                "status": "success" if success else "failed",
                "action": "confirmation_sent",
                "candidate": candidate["name"]
            }
        else:
            # Otherwise, initiate contact
            response = await self.contact_candidate(candidate)
            return {
                "status": "success" if response["success"] else "failed",
                "action": "contact_initiated",
                "candidate": candidate["name"],
                "available_slots": response.get("available_slots", [])
            } 