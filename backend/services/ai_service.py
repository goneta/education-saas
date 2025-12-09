import os
import json
import time
from typing import Dict, Any, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class AIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key and OpenAI:
            self.client = OpenAI(api_key=self.api_key)
        else:
            print("Warning: OPENAI_API_KEY not found or openai not installed. Using Mock AI Service.")

    def generate_response(self, message: str) -> Dict[str, Any]:
        """
        Generates a response based on the user message.
        If API key is present, uses OpenAI.
        Otherwise, uses varied mock responses.
        """
        if self.client:
            return self._call_openai(message)
        else:
            return self._call_mock(message)

    def _call_openai(self, message: str) -> Dict[str, Any]:
        try:
            # We enforce a JSON structure prompt
            system_prompt = """
            You are an expert AI assistant for an Education SaaS.
            You must return a JSON object with this structure:
            {
                "type": "chat" | "content",
                "message": "A conversational response to the user.",
                "data": null | string (Markdown content if type is 'content')
            }
            If the user asks to create something (course, report, list), set type to 'content' and put the result in 'data' (Markdown).
            If just chatting, set type to 'chat' and data to null.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo", # Or gpt-4-turbo
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"OpenAI Error: {e}")
            return {
                "type": "chat",
                "message": "I encountered an error connecting to the AI brain. Falling back to internal logic.",
                "data": None
            }

    def _call_mock(self, message: str) -> Dict[str, Any]:
        """
        Sophisticated mock logic to simulate AI behavior.
        """
        time.sleep(1.5) # Simulate thinking
        msg_lower = message.lower()

        if "course" in msg_lower or "curriculum" in msg_lower:
            return {
                "type": "content",
                "message": "I have drafted a course outline for you. You can review it in the preview panel.",
                "data": """# Introduction to Computer Science
## Course Overview
This course provides a comprehensive introduction to the fundamental concepts of computer science.

## Modules
1. **Basics of Programming**
   - Variables and Data Types
   - Control Structures
   - Functions
2. **Data Structures**
   - Arrays and Lists
   - Trees and Graphs
3. **Algorithms**
   - Sorting and Searching
   - Complexity Analysis

## Duration
- 12 Weeks
- 4 Hours/Week
"""
            }
        elif "list" in msg_lower or "report" in msg_lower:
             return {
                "type": "content",
                "message": "Here is the list you requested.",
                "data": """## Top 5 Educational Trends 2025
1. **AI-Driven Personalization**: Custom learning paths.
2. **Immersive Learning**: AR/VR integration.
3. **Micro-Learning**: Bite-sized content consumption.
4. **Gamification**: Engagement through game mechanics.
5. **Blockchain Credentials**: Secure and verifiable certificates.
"""
            }
        else:
            return {
                "type": "chat",
                "message": f"I understand you said: '{message}'. I am running in Simulation Mode because no API Key was configured. Ask me to 'create a course' to see the Preview feature in action!",
                "data": None
            }

ai_service = AIService()
