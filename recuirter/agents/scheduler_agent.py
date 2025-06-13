import os
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta, timezone
from .base_tool import LLMTool
from pydantic import Field, ConfigDict
from dotenv import load_dotenv

load_dotenv()

class MockCalendarEvent:
    def __init__(self, summary: str, start: datetime, end: datetime):
        self.summary = summary
        self.start = start
        self.end = end

class MockCalendarService:
    def __init__(self):
        self.events: List[MockCalendarEvent] = []
    
    def list_events(self, calendarId: str, timeMin: str, timeMax: str, singleEvents: bool, orderBy: str) -> Dict:
        """Mock implementation of calendar events list."""
        return {
            'items': [
                {
                    'summary': event.summary,
                    'start': {'dateTime': event.start.isoformat()},
                    'end': {'dateTime': event.end.isoformat()}
                }
                for event in self.events
            ]
        }
    
    def insert_event(self, calendarId: str, body: Dict) -> Dict:
        """Mock implementation of event creation."""
        start_time = datetime.fromisoformat(body['start']['dateTime'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(body['end']['dateTime'].replace('Z', '+00:00'))
        
        event = MockCalendarEvent(
            summary=body['summary'],
            start=start_time,
            end=end_time
        )
        self.events.append(event)
        
        return {
            'id': f'mock_event_{len(self.events)}',
            'summary': event.summary,
            'start': {'dateTime': event.start.isoformat()},
            'end': {'dateTime': event.end.isoformat()}
        }

class SchedulerTool(LLMTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = "Interview Scheduler Tool"
    description: str = "A tool that manages interview scheduling using Google Calendar"
    arg: str = "A candidate object with available slots and job details"
    service: Optional[MockCalendarService] = Field(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        self.service = MockCalendarService()
    
    def find_available_slot(self, candidate_slots: list) -> Optional[Dict]:
        """Find an available slot that matches the interviewer's calendar."""
        # Get interviewer's calendar events for the next 7 days
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=7)
        
        events_result = self.service.list_events(
            calendarId='primary',
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        )
        
        busy_slots = events_result.get('items', [])
        
        # Convert candidate slots to datetime objects with UTC timezone
        candidate_dt_slots = []
        for slot in candidate_slots:
            try:
                # Parse the datetime string and ensure it's UTC
                dt = datetime.fromisoformat(slot)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                candidate_dt_slots.append(dt)
            except ValueError:
                continue
        
        # Find first available slot that doesn't conflict with interviewer's calendar
        for slot in candidate_dt_slots:
            slot_end = slot + timedelta(hours=1)  # Assuming 1-hour interviews
            
            # Check if slot conflicts with any existing events
            conflict = False
            for event in busy_slots:
                event_start = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')))
                event_end = datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date')))
                
                # Ensure event times are timezone-aware
                if event_start.tzinfo is None:
                    event_start = event_start.replace(tzinfo=timezone.utc)
                if event_end.tzinfo is None:
                    event_end = event_end.replace(tzinfo=timezone.utc)
                
                if (slot >= event_start and slot < event_end) or \
                   (slot_end > event_start and slot_end <= event_end):
                    conflict = True
                    break
            
            if not conflict:
                return {
                    "date": slot.strftime("%Y-%m-%d"),
                    "time": slot.strftime("%H:%M"),
                    "format": "Video Call",
                    "duration": "1 hour"
                }
        
        return None
    
    async def schedule_interview(self, candidate: dict, job_title: str) -> Optional[Dict]:
        """Schedule an interview based on candidate's available slots."""
        if not candidate.get('available_slots'):
            return None
        
        # Find an available slot
        interview_slot = self.find_available_slot(candidate['available_slots'])
        
        if interview_slot:
            # Create calendar event
            event = {
                'summary': f'Interview: {candidate["name"]} - {job_title}',
                'description': f'Initial screening interview with {candidate["name"]} for {job_title} position.',
                'start': {
                    'dateTime': f"{interview_slot['date']}T{interview_slot['time']}:00Z",
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': f"{interview_slot['date']}T{interview_slot['time']}:00Z",
                    'timeZone': 'UTC',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }
            
            event = self.service.insert_event(calendarId='primary', body=event)
            
            return {
                **interview_slot,
                "event_id": event['id'],
                "meeting_link": "https://meet.google.com/xxx-yyyy-zzz"  # Mock meeting link
            }
        
        return None

    async def run(self, candidate: dict) -> str:
        """Main entry point for the scheduler tool."""
        if not candidate.get('available_slots'):
            return {
                "status": "failed",
                "error": "No available slots provided"
            }
        
        interview = await self.schedule_interview(candidate, candidate.get('job_title', 'Position'))
        
        if interview:
            return {
                "status": "success",
                "interview": interview,
                "candidate": candidate["name"]
            }
        else:
            return {
                "status": "failed",
                "error": "Could not find a suitable time slot"
            } 