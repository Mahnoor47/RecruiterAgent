import os
from typing import List, Dict
import PyPDF2
from .base_tool import LLMTool
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()

class CVMatcherTool(LLMTool):
    name: str = "CV Matching Tool"
    description: str = "A tool that analyzes CVs against job descriptions and provides match scores"
    arg: str = "A job description to match against available CVs"
    cv_directory: str = Field(default="cvs")

    def __init__(self, **data):
        super().__init__(**data)
        
    async def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file."""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text

    async def analyze_cv(self, cv_text: str, job_description: str) -> float:
        """Analyze CV against job description using Ollama."""
        system_prompt = """You are an expert CV analyzer. Your task is to analyze a CV against a job description and provide a match score from 0 to 1.
        Consider skills, experience, and qualifications. Return ONLY a number between 0 and 1, nothing else."""
        
        prompt = f"""
        Job Description:
        {job_description}
        
        CV:
        {cv_text}
        """
        
        response = await self.generate_response(prompt, system_prompt)
        
        try:
            # Extract the first number from the response
            import re
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", response)
            if numbers:
                score = float(numbers[0])
                return min(max(score, 0), 1)  # Ensure score is between 0 and 1
            return 0.0
        except:
            return 0.0

    async def run(self, job_description: str) -> str:
        """Match CVs with job description and return top candidates."""
        candidates = []
        
        # Ensure CV directory exists
        if not os.path.exists(self.cv_directory):
            os.makedirs(self.cv_directory)
            return {
                "status": "error",
                "error": "No CVs found in the directory.",
                "candidates": [],
                "total_candidates": 0
            }
        
        # Process each CV in the directory
        for filename in os.listdir(self.cv_directory):
            if filename.endswith('.pdf'):
                cv_path = os.path.join(self.cv_directory, filename)
                cv_text = await self.extract_text_from_pdf(cv_path)
                
                # Extract basic information from CV
                name = filename.split('.')[0]  # Using filename as name for now
                
                # Analyze CV against job description
                match_score = await self.analyze_cv(cv_text, job_description)
                
                candidates.append({
                    "name": name,
                    "cv_path": cv_path,
                    "match_score": match_score,
                    "phone": "",  # You'll need to extract this from CV
                    "email": ""   # You'll need to extract this from CV
                })
        
        if not candidates:
            return {
                "status": "error",
                "error": "No CVs found in the directory.",
                "candidates": [],
                "total_candidates": 0
            }
        
        # Sort candidates by match score
        candidates.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Return top 5 candidates
        top_candidates = candidates[:5]
        return {
            "status": "success",
            "candidates": top_candidates,
            "total_candidates": len(candidates)
        } 