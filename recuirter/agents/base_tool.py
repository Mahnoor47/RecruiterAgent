from typing import Any, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict, Field
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

class Tool(ABC, BaseModel):
    name: str
    description: str
    arg: str

    def model_post_init(self, __context: Any) -> None:
        self.name = self.name.lower().replace(' ', '_')
        self.description = self.description.lower()
        self.arg = self.arg.lower()

    @abstractmethod
    def run(self, prompt: str) -> str:
        pass

    def get_tool_description(self):
        return f"Tool: {self.name}\nDescription: {self.description}\nArg: {self.arg}\n"

class LLMTool(Tool):
    ollama_base_url: str = Field(default="http://localhost:11434")
    model: str = Field(default="mistral")
    
    def __init__(self, **data):
        super().__init__(**data)
        
    async def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """Generate response using Ollama."""
        try:
            url = f"{self.ollama_base_url}/api/generate"
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "" 