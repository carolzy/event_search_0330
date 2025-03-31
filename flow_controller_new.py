from typing import Dict, List, Optional, Any
import logging
import os
import random
import json
import httpx
from pathlib import Path
from dotenv import load_dotenv
from question_engine_new import QuestionEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class FlowController:
    """Controls the multi-step B2B sales flow"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = FlowController()
        return cls._instance
    
    def __init__(self):
        """Initialize the flow controller."""
        # Load API keys
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        logger.info(f"Loaded Gemini API key: {self.gemini_api_key[:10] if self.gemini_api_key else 'Not found'}")
        
        # User data
        self.current_product_line = ""
        self.current_sector = ""
        self.current_segment = ""
        self.keywords = []
        self.linkedin_consent = False
        self.zip_code = ""
        
        # Conversation memory
        self.conversation_memory = []
        self.context_summary = ""
        
        # Flow state
        self.steps = [
            'product',
            'market',
            'differentiation',
            'company_size',
            'linkedin',
            'location',
            'complete'
        ]
        
        # Initialize the question engine
        self.question_engine = QuestionEngine()
    
    def get_next_step(self, current_step):
        """Get the next step in the flow."""
        try:
            current_index = self.steps.index(current_step)
            if current_index < len(self.steps) - 1:
                return self.steps[current_index + 1]
            else:
                return 'complete'
        except ValueError:
            return 'product'  # Default to the first step if current_step is not found
    
    async def get_question(self, step: str) -> str:
        """Get the question for the current step."""
        try:
            # Build context from previous answers
            context = self._build_context()
            
            # Get the question from the question engine
            question = await self.question_engine.get_question(step, context)
            
            return question
            
        except Exception as e:
            logger.error(f"Error generating question: {str(e)}")
            return self._get_fallback_question(f"We need to ask about: {step}")
    
    async def get_follow_up_question(self, step: str, previous_answer: str, follow_up_count: int = 0, suggest_next: bool = False) -> str:
        """Get a follow-up question for the current step."""
        try:
            # Check if we should suggest moving to the next step
            if suggest_next:
                next_step = self.get_next_step(step)
                next_step_name = {
                    'product': 'your target market',
                    'market': 'what makes your product unique',
                    'differentiation': 'your target company size',
                    'company_size': 'LinkedIn integration',
                    'linkedin': 'your location',
                    'location': 'completing your setup'
                }.get(next_step, 'the next step')
                
                return f"Thanks for that information. Would you like to add anything else or shall we move on to {next_step_name}?"
            
            # Check for signs of user impatience in the previous answer
            impatience_indicators = [
                "next", "move on", "continue", "skip", "enough", "let's go", 
                "proceed", "done", "finished", "complete", "that's it", "that's all"
            ]
            
            if any(indicator in previous_answer.lower() for indicator in impatience_indicators):
                next_step = self.get_next_step(step)
                next_question = await self.get_question(next_step)
                return f"Let's move on to the next question. {next_question}"
            
            # Use the Gemini API to generate a follow-up question
            if not self.gemini_api_key:
                logger.warning("No Gemini API key found. Using default follow-up questions.")
                return "Can you tell me more about that?"
            
            # Generate a more conversational follow-up question based on the current context
            prompt = f"""
            You are a friendly B2B research assistant helping a user set up their company research preferences.
            
            Current context:
            - Product/Service: {self.current_product_line or 'Not provided yet'}
            - Target Market: {self.current_sector or 'Not provided yet'}
            - Company Size: {self.current_segment or 'Not provided yet'}
            
            Current step: {step}
            User's answer: "{previous_answer}"
            Follow-up count: {follow_up_count + 1}
            
            Generate a brief, friendly follow-up question that helps clarify or expand on their answer.
            Keep it concise (1 sentence max). Do not use technical jargon.
            If this is the second follow-up (count = 1), make it a final clarification before moving on.
            Do not include any thinking process in your response.
            """
            
            follow_up = await self._call_gemini_api(prompt)
            
            return follow_up
                
        except Exception as e:
            logger.error(f"Error generating follow-up question: {str(e)}")
            return "Can you tell me more about that?"
    
    async def _call_gemini_api(self, prompt):
        """Call the Gemini API with the given prompt."""
        if not self.gemini_api_key:
            logger.error("Gemini API key not found")
            return self._get_fallback_question(prompt)
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}"
            
            data = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=data,
                    timeout=5.0  # Reduced timeout to improve latency
                )
                
                if response.status_code != 200:
                    logger.error(f"Error from Gemini API: {response.status_code}, {response.text}")
                    return self._get_fallback_question(prompt)
                
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    content = result["candidates"][0]["content"]
                    if "parts" in content and len(content["parts"]) > 0:
                        return content["parts"][0]["text"]
                
                logger.error(f"Unexpected response format from Gemini API: {result}")
                return self._get_fallback_question(prompt)
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            return self._get_fallback_question(prompt)
    
    def _get_fallback_question(self, prompt):
        """Get a fallback question if the Gemini API call fails."""
        step = "unknown"
        lines = prompt.split('\n')
        if any("We need to ask about:" in line for line in lines):
            step_line = [line for line in lines if "We need to ask about:" in line]
            if step_line:
                step = step_line[0].split(':')[1].strip()
        
        fallback_questions = {
            'product': "What product or service are you selling?",
            'market': "Which market or industry are you targeting?",
            'differentiation': "What makes your product unique compared to competitors?",
            'company_size': "What size of companies are you focusing on?",
            'keywords': "Here are some keywords I've generated based on your input. Would you like to edit them?",
            'linkedin': "Would you like to include LinkedIn profiles in your research?",
            'location': "What's your zip code for location-based insights? (Type 'skip' to skip this step)",
            'unknown': "What else would you like to tell me about your needs?"
        }
        
        return fallback_questions.get(step, fallback_questions['unknown'])
    
    async def store_answer(self, step, answer):
        """Store the user's answer for the current step."""
        try:
            if step == 'product':
                self.current_product_line = answer
                # Generate keywords based on the product
                await self._update_keywords()
            elif step == 'market':
                self.current_sector = answer
                # Update keywords based on the market
                await self._update_keywords()
            elif step == 'differentiation':
                # Store the differentiation
                self._add_to_conversation_memory('differentiation', answer)
                # Update keywords based on the differentiation
                await self._update_keywords()
            elif step == 'company_size':
                self.current_segment = answer
                # Update keywords based on the company size
                await self._update_keywords()
            elif step == 'linkedin':
                self.linkedin_consent = 'yes' in answer.lower() or 'sure' in answer.lower() or 'ok' in answer.lower()
                logger.info(f"LinkedIn consent: {self.linkedin_consent}")
            elif step == 'location':
                if 'skip' not in answer.lower():
                    self.zip_code = answer
                    logger.info(f"Zip code: {self.zip_code}")
            
            # Add to conversation memory
            self._add_to_conversation_memory(step, answer)
            
            return True
        except Exception as e:
            logger.error(f"Error storing answer: {str(e)}")
            return False
    
    def _add_to_conversation_memory(self, step, answer):
        """Add a step and answer to the conversation memory."""
        self.conversation_memory.append({
            'step': step,
            'answer': answer
        })
        
        # Update the context summary
        self._update_context_summary()
    
    def _update_context_summary(self):
        """Update the context summary based on the conversation memory."""
        try:
            summary = ""
            for item in self.conversation_memory:
                step = item['step']
                answer = item['answer']
                
                if step == 'product':
                    summary += f"Product/Service: {answer}\n"
                elif step == 'market':
                    summary += f"Target Market: {answer}\n"
                elif step == 'differentiation':
                    summary += f"Unique Value Proposition: {answer}\n"
                elif step == 'company_size':
                    summary += f"Target Company Size: {answer}\n"
                elif step == 'linkedin':
                    summary += f"LinkedIn Consent: {answer}\n"
                elif step == 'location':
                    summary += f"Location: {answer}\n"
            
            self.context_summary = summary
        except Exception as e:
            logger.error(f"Error updating context summary: {str(e)}")
    
    def _build_context(self):
        """Build context from previous answers."""
        context = {}
        
        if self.current_product_line:
            context['product'] = self.current_product_line
        
        if self.current_sector:
            context['market'] = self.current_sector
        
        if self.current_segment:
            context['company_size'] = self.current_segment
        
        # Add differentiation from conversation memory if available
        for item in self.conversation_memory:
            if item['step'] == 'differentiation':
                context['differentiation'] = item['answer']
                break
        
        if self.linkedin_consent:
            context['linkedin_consent'] = True
        
        if self.zip_code:
            context['zip_code'] = self.zip_code
        
        return context
    
    async def _update_keywords(self):
        """Update keywords based on the current context."""
        try:
            # Build context from previous answers
            context = self._build_context()
            
            # Generate keywords using the question engine
            if hasattr(self.question_engine, 'generate_keywords'):
                keywords = await self.question_engine.generate_keywords(context)
                if keywords:
                    self.keywords = keywords
            
            logger.info(f"Updated keywords: {self.keywords}")
            return True
        except Exception as e:
            logger.error(f"Error updating keywords: {str(e)}")
            return False
    
    async def clean_keywords(self):
        """Clean up keywords and return them."""
        # Remove duplicates and empty strings
        cleaned_keywords = list(set([k.strip() for k in self.keywords if k.strip()]))
        
        # Sort alphabetically
        cleaned_keywords.sort()
        
        return cleaned_keywords
    
    async def reset(self):
        """Reset the flow controller."""
        self.current_product_line = ""
        self.current_sector = ""
        self.current_segment = ""
        self.keywords = []
        self.linkedin_consent = False
        self.zip_code = ""
        self.conversation_memory = []
        self.context_summary = ""
        
        return True
