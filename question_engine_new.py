import random
import logging
import re
import os
import requests
import json
from dotenv import load_dotenv
import httpx
from pathlib import Path
from typing import Dict, List, Optional, Any

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class QuestionEngine:
    """Generates dynamic questions for the onboarding flow based on context"""
    
    def __init__(self):
        """Initialize the QuestionEngine with default templates"""
        self.logger = logging.getLogger(__name__)
        
        # Check if Gemini API key is available
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if self.gemini_api_key:
            self.logger.info("Gemini API key found. Using dynamic LLM-based questions.")
        else:
            self.logger.warning("No Gemini API key found. Using static question templates.")
        
        # Default question templates - adapted for Atom.ai
        self.question_templates = {
            'product': "What product or service does your company offer? Please provide a brief description.",
            'market': "What market or industry sector are you targeting with your product or service?",
            'differentiation': "What makes your product unique compared to competitors?",
            'company_size': "What size of companies are you primarily targeting? (e.g., Small, Medium, Enterprise)",
            'keywords': "Cool! We've generated some target keywords for your product/service. You can edit, remove, or add to these keywords below:",
            'linkedin': "Would you like to connect your LinkedIn account to enhance your company recommendations? This will help us find more relevant matches based on your professional network.",
            'location': "What zip code are you in? This will help us find relevant local events. (You can skip this question if you prefer.)",
            'complete': "Awesome! I've gathered everything I need. Let's find some great companies for you."
        }
        
        # Steps in the onboarding flow
        self.steps = ['product', 'market', 'differentiation', 'company_size', 'linkedin', 'location', 'complete']
        
        # Load workflow patterns if available
        self.patterns_path = Path("workflows/patterns_v1.json")
        self.workflow_patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict[str, Any]:
        """Load workflow patterns from JSON file."""
        try:
            if self.patterns_path.exists():
                with open(self.patterns_path) as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load workflow patterns: {str(e)}")
            return {}
    
    async def get_question(self, step, context=None):
        """
        Generate a question based on the current step and context
        
        Args:
            step (str): The current step in the onboarding flow
            context (dict): Context from previous answers
            
        Returns:
            str: A dynamically generated question
        """
        if context is None:
            context = {}
            
        if step is None or step == 'complete':
            return "Great! We've completed your setup. Let's find some target companies for you!"
        
        # Always try to use the LLM first if we have an API key
        if self.gemini_api_key:
            try:
                llm_response = await self._generate_with_llm(step, context)
                if llm_response:
                    return llm_response
            except Exception as e:
                logger.error(f"Error using LLM for question generation: {str(e)}")
                # Fall through to template-based questions if LLM fails
        
        # Fallback to template-based questions
        if step in self.question_templates:
            return self.question_templates[step]
        else:
            return "Tell me more about your needs."
    
    async def _generate_with_llm(self, step, context):
        """Generate a question using the Gemini API"""
        try:
            # Construct a prompt based on the current step and context
            prompt = self._construct_prompt(step, context)
            
            # Call the Gemini API
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
                    timeout=5.0
                )
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    content = result["candidates"][0]["content"]
                    if "parts" in content and len(content["parts"]) > 0:
                        question = content["parts"][0]["text"]
                        
                        # Clean up the response to ensure it's a single question
                        question = self._clean_llm_response(question)
                        
                        logger.info(f"Generated question with Gemini API: {question}")
                        return question
                
                logger.error(f"Unexpected response format from Gemini API: {result}")
                return self._fallback_question(step, context)
            else:
                logger.error(f"Error calling Gemini API: {response.status_code} - {response.text}")
                # Fall back to template-based questions
                return self._fallback_question(step, context)
                
        except Exception as e:
            logger.error(f"Error generating question with LLM: {str(e)}")
            # Fall back to template-based questions
            return self._fallback_question(step, context)
    
    def _construct_prompt(self, step, context):
        """Construct a prompt for the LLM based on the current step and context"""
        product = context.get('product', '')
        market = context.get('market', '')
        company_size = context.get('company_size', '')
        differentiation = context.get('differentiation', '')
        
        if step == 'product':
            return """
            Generate a friendly, conversational question asking what product or service the user sells.
            Keep it short and engaging. This is for Atom.ai, a tool that helps founders find potential customers.
            """
        elif step == 'market':
            return f"""
            The user sells: {product}
            
            Generate a friendly, conversational question asking what industry or market sector they target.
            Reference their product/service in your question.
            Keep it short and engaging. This is for Atom.ai, a tool that helps founders find potential customers.
            """
        elif step == 'differentiation':
            return f"""
            The user sells: {product}
            They target the {market} industry.
            
            Generate a friendly, conversational question asking what makes their product unique compared to competitors.
            Reference their product/service in your question.
            Keep it short and engaging. This is for Atom.ai, a tool that helps founders find potential customers.
            """
        elif step == 'company_size':
            return f"""
            The user sells: {product}
            They target the {market} industry.
            Their differentiator: {differentiation}
            
            Generate a friendly, conversational question asking what size of companies they typically target 
            (e.g., SMB, Mid-Market, Enterprise).
            Reference their product/service in your question.
            Keep it short and engaging. This is for Atom.ai, a tool that helps founders find potential customers.
            """
        elif step == 'linkedin':
            return f"""
            The user sells: {product}
            They target the {market} industry.
            Their differentiator: {differentiation}
            Their target company size: {company_size}
            
            Generate a friendly, conversational question asking if they would like to connect their LinkedIn account
            to improve recommendations. Explain briefly why this would be helpful.
            Keep it short and engaging. This is for Atom.ai, a tool that helps founders find potential customers.
            """
        elif step == 'location':
            return f"""
            The user sells: {product}
            They target the {market} industry.
            Their differentiator: {differentiation}
            Their target company size: {company_size}
            
            Generate a friendly, conversational question asking for their zip code to help find local events.
            Mention that this is optional and they can skip this step.
            Keep it short and engaging. This is for Atom.ai, a tool that helps founders find potential customers.
            """
        else:
            return f"""
            Generate a friendly, conversational question for the step: {step}
            Context: {context}
            Keep it short and engaging. This is for Atom.ai, a tool that helps founders find potential customers.
            """
    
    def _clean_llm_response(self, response):
        """Clean up the LLM response to ensure it's a single question"""
        # Remove any "AI:" or "Atom:" prefixes
        response = re.sub(r'^(AI:|Atom:|Assistant:)\s*', '', response)
        
        # Remove any thinking process or explanations in brackets or parentheses
        response = re.sub(r'\[.*?\]|\(.*?\)', '', response)
        
        # Remove any lines that don't end with a question mark or aren't questions
        lines = response.split('\n')
        question_lines = []
        for line in lines:
            line = line.strip()
            if line and (line.endswith('?') or re.search(r'what|how|why|when|where|which|can|could|would|will|do|does|is|are', line.lower())):
                question_lines.append(line)
        
        if question_lines:
            return question_lines[0]  # Return the first question
        
        # If no question was found, return the original response
        return response.strip()
    
    def _fallback_question(self, step, context):
        """Fallback to template-based questions if LLM fails"""
        if step in self.question_templates:
            return self.question_templates[step]
        else:
            return "Tell me more about your needs."
    
    def get_next_step(self, current_step):
        """
        Determine the next step based on the current step
        
        Args:
            current_step (str): The current step in the onboarding flow
            
        Returns:
            str: The next step in the onboarding flow
        """
        try:
            current_index = self.steps.index(current_step)
            if current_index < len(self.steps) - 1:
                return self.steps[current_index + 1]
            else:
                return 'complete'
        except ValueError:
            return 'product'  # Default to the first step if current_step is not found
    
    async def generate_keywords(self, context):
        """
        Generate keywords based on user input
        
        Args:
            context (dict): Context from previous answers
            
        Returns:
            list: List of generated keywords
        """
        try:
            # Extract relevant information from context
            product = context.get('product', '')
            market = context.get('market', '')
            differentiation = context.get('differentiation', '')
            company_size = context.get('company_size', '')
            
            # Combine all information for keyword generation
            combined_context = f"""
            Product/Service: {product}
            Target Market/Industry: {market}
            Unique Value Proposition: {differentiation}
            Target Company Size: {company_size}
            """
            
            # Use LLM for keyword generation if available
            if self.gemini_api_key:
                keywords = await self._generate_keywords_with_llm(combined_context)
                if keywords:
                    return keywords
            
            # Fallback to basic keyword extraction
            return self._extract_basic_keywords(combined_context)
            
        except Exception as e:
            logger.error(f"Error generating keywords: {str(e)}")
            return ["B2B", "Sales", "Technology", "Innovation"]
    
    async def _generate_keywords_with_llm(self, context):
        """Generate keywords using the Gemini API"""
        try:
            # Prepare the prompt for keyword generation
            prompt = f"""
            Generate keywords that describe the product offering and target customer based on the following context:
            {context}
            
            Generate only the most relevant keywords that would help find ideal target companies.
            Format your response as a comma-separated list of keywords only, without any additional text or explanations.
            Limit to 15 keywords maximum.
            """
            
            # Call the Gemini API
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
                    timeout=5.0
                )
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    content = result["candidates"][0]["content"]
                    if "parts" in content and len(content["parts"]) > 0:
                        keywords_text = content["parts"][0]["text"]
                        
                        # Parse the keywords from the response
                        keywords_list = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
                        
                        # Limit to 15 keywords
                        keywords_list = keywords_list[:15]
                        
                        logger.info(f"Generated keywords with LLM: {keywords_list}")
                        return keywords_list
            
            logger.error(f"Error or unexpected response from Gemini API")
            return None
                
        except Exception as e:
            logger.error(f"Error generating keywords with LLM: {str(e)}")
            return None
    
    def _extract_basic_keywords(self, text):
        """Extract basic keywords from text using simple rules"""
        # Convert to lowercase and split by common separators
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove common stop words
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'as', 'of', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall', 'should', 'can', 'could', 'may', 'might', 'must', 'that', 'which', 'who', 'whom', 'this', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'been', 'being', 'have', 'has', 'had', 'does', 'did', 'doing', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Count word frequency
        word_counts = {}
        for word in filtered_words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Get the most frequent words as keywords
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, count in sorted_words[:15]]
        
        # Add some common business keywords if we don't have enough
        if len(keywords) < 5:
            common_keywords = ["B2B", "enterprise", "software", "technology", "solution", "platform", "service", "analytics", "automation", "AI", "cloud", "data", "security", "integration", "management"]
            keywords.extend(common_keywords[:10 - len(keywords)])
        
        return keywords
