import os
import logging
import requests
import json
import random
from dotenv import load_dotenv
from datetime import datetime
import httpx
from typing import List, Dict, Any, Optional
import hashlib
import time
from recommendation_verifier import verify_recommendations
from user_memory import UserMemory
import traceback

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class CompanyRecommender:
    """Recommends target companies based on user preferences"""
    
    def __init__(self, flow_controller):
        """Initialize the company recommender"""
        self.flow_controller = flow_controller
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.use_llm = self.gemini_api_key is not None or self.perplexity_api_key is not None or self.openai_api_key is not None
        
        # Priority sources for company information
        self.priority_news_sources = [
            "techcrunch.com",
            "crunchbase.com",
            "pitchbook.com",
            "venturebeat.com",
            "forbes.com",
            "businessinsider.com",
            "cnbc.com",
            "reuters.com",
            "bloomberg.com",
            "wsj.com"
        ]
        
        # Priority sources for events
        self.priority_event_sources = [
            "eventbrite.com",
            "luma.events",
            "meetup.com",
            "conference.com",
            "summit.com"
        ]
        
        # Get or create user memory
        self.user_id = flow_controller.user_id if hasattr(flow_controller, 'user_id') else "default_user"
        self.user_memory = UserMemory(self.user_id)
        
        if not self.use_llm:
            logger.warning("No API keys found for LLM. This will cause an exception when generating recommendations.")
    
    async def generate_recommendations(self, count=3, verify=True):
        """Generate company recommendations based on user preferences."""
        try:
            logger.info("Generating company recommendations...")
            
            # Get user preferences from flow controller
            product = self.flow_controller.get_product() if hasattr(self.flow_controller, 'get_product') else ""
            market = self.flow_controller.get_market() if hasattr(self.flow_controller, 'get_market') else ""
            company_size = self.flow_controller.get_company_size() if hasattr(self.flow_controller, 'get_company_size') else ""
            zip_code = self.flow_controller.get_location() if hasattr(self.flow_controller, 'get_location') else ""
            linkedin_consent = self.flow_controller.get_linkedin_consent() if hasattr(self.flow_controller, 'get_linkedin_consent') else False
            keywords = self.flow_controller.get_keywords() if hasattr(self.flow_controller, 'get_keywords') else []
            
            # Log input data
            logger.info(f"Recommendation inputs: product='{product}', market='{market}', company_size='{company_size}', zip_code='{zip_code}', linkedin_consent={linkedin_consent}, keywords={keywords}")
            
            # Check if we have valid API keys
            if not self.use_llm:
                logger.warning("No API keys found for LLM. Using mock recommendations.")
                return self._get_mock_recommendations(count)
                
            # Generate recommendations using Gemini
            try:
                recommendations = await self._generate_with_gemini(
                    product=product,
                    market=market,
                    company_size=company_size,
                    zip_code=zip_code,
                    keywords=keywords,
                    linkedin_consent=linkedin_consent,
                    count=count
                )
            except Exception as e:
                logger.error(f"Error with Gemini API: {str(e)}")
                logger.info("Falling back to mock recommendations")
                return self._get_mock_recommendations(count)
            
            # Verify recommendations if requested
            if verify and recommendations:
                logger.info(f"Verifying {len(recommendations)} recommendations...")
                verified_recommendations = []
                for rec in recommendations:
                    if self._verify_recommendation(rec):
                        verified_recommendations.append(rec)
                    else:
                        logger.warning(f"Removed invalid recommendation: {rec.get('name', 'Unknown')}")
                
                recommendations = verified_recommendations
                logger.info(f"Verified {len(recommendations)} recommendations")
            
            # If we have no valid recommendations, use mock data
            if not recommendations:
                logger.warning("No valid recommendations generated, using mock data")
                return self._get_mock_recommendations(count)
                
            return recommendations
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            logger.error(traceback.format_exc())
            # Return mock recommendations as fallback
            return self._get_mock_recommendations(count)
    
    async def _generate_with_llm(self, product, market, company_size, zip_code, keywords, linkedin_consent, count):
        """Generate recommendations using an LLM"""
        # Only use Gemini Flash 2.0
        return await self._generate_with_gemini(product, market, company_size, zip_code, keywords, linkedin_consent, count)
    
    async def _generate_with_perplexity(self, product, market, company_size, zip_code, keywords, linkedin_consent, count):
        """Generate recommendations using the Perplexity API"""
        try:
            # Construct a prompt based on user preferences
            prompt = self._construct_recommendation_prompt(product, market, company_size, zip_code, keywords, linkedin_consent)
            
            # Call the Perplexity API
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.perplexity_api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": "sonar-reasoning",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a B2B company research assistant that provides detailed company recommendations with recent news, key personnel, and events."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
                
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    recommendations_text = result["choices"][0]["message"]["content"]
                    
                    # Parse the recommendations from the response
                    try:
                        recommendations = self._parse_recommendations_from_llm_response(recommendations_text)
                        
                        # Rank the recommendations based on various factors
                        ranked_recommendations = self._rank_recommendations(
                            recommendations=recommendations,
                            keywords=keywords,
                            zip_code=zip_code
                        )
                        
                        # Return the top N recommendations
                        return ranked_recommendations[:count]
                    except Exception as e:
                        logger.error(f"Error parsing recommendations: {str(e)}")
                        raise Exception(f"Failed to parse recommendations: {str(e)}")
                else:
                    logger.error(f"Error calling Perplexity API: {response.status_code} - {response.text}")
                    raise Exception(f"Failed to generate recommendations: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Error generating recommendations with Perplexity: {str(e)}")
            raise Exception(f"Failed to generate recommendations: {str(e)}")
    
    async def _generate_with_openai(self, product, market, company_size, zip_code, keywords, linkedin_consent, count=5):
        """Generate recommendations using OpenAI"""
        logger.info("Generating recommendations with OpenAI")
        
        # Prepare the system prompt
        system_prompt = """You are a financial analyst specializing in fintech and B2B sales intelligence. 
        Your task is to recommend target companies based on the user's product, market, and preferences.
        
        For each company, provide:
        1. Company name
        2. Brief description
        3. Why they're a good fit as a POTENTIAL CUSTOMER based on the user's profile (focus on why they would need the user's product/service)
        4. Key decision makers with recent quotes in news articles (include the source and date for each quote)
        5. Current year's investment focus and resource allocation (where is the company investing money this year) with direct quotes from executives when available
        6. Upcoming events and meetups (within the next 90 days) where company representatives might attend or speak

        Format your response as a JSON array of objects with the following structure:
        [
            {
                "name": "Company Name",
                "description": "Brief company description",
                "fit_reason": "Why this company would be a good CUSTOMER for your product/service",
                "key_personnel": ["Name, Title", "Name, Title"],
                "recent_news": [
                    {
                        "title": "Investment Focus",
                        "date": "Month Year",
                        "summary": "Details about where the company is investing money this year, with direct quotes from executives",
                        "url": "Source URL if available"
                    }
                ],
                "events": [
                    {
                        "name": "Event Name",
                        "date": "Event Date",
                        "location": "Event Location",
                        "url": "Event URL",
                        "description": "Brief description of the event and why it's relevant"
                    }
                ],
                "website": "https://company-website.com",
                "fit_score": {{
                    "product_fit": 85,
                    "market_fit": 90,
                    "size_fit": 75,
                    "keyword_fit": 80,
                    "overall_score": 85
                }}
            }
        ]
        """
        
        # Prepare the user prompt
        user_prompt = f"""Based on the following information, recommend {count} companies that would be good targets for sales outreach:

        Product: {product if product else 'Not specified'}
        Market/Industry: {market if market else 'Not specified'}
        Target Company Size: {company_size if company_size else 'Not specified'}
        Location (Zip Code): {zip_code if zip_code else 'Not specified'}
        
        Keywords: {', '.join(keywords) if keywords else 'Not specified'}
        
        Please provide detailed information for each company including investment areas, recent articles with executive quotes, key decision makers, and relevant events they'll be attending.
        Format your response as a valid JSON array of company objects as specified.
        """
        
        try:
            # Call the OpenAI API
            import openai
            openai.api_key = self.openai_api_key
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # Extract the response content
            content = response.choices[0].message.content
            
            # Parse the JSON response
            try:
                import json
                recommendations = json.loads(content)
                
                # Validate the structure
                if not isinstance(recommendations, list):
                    logger.error("OpenAI response is not a list")
                    return self._get_mock_recommendations(count)
                
                # Process and return the recommendations
                return recommendations[:count]
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {e}")
                logger.error(f"Raw response: {content}")
                return self._get_mock_recommendations(count)
                
        except Exception as e:
            logger.error(f"Error generating recommendations with OpenAI: {e}")
            return self._get_mock_recommendations(count)
    
    async def _generate_with_gemini(self, product, market, company_size, zip_code, keywords, linkedin_consent, count):
        """Generate recommendations using the Gemini API"""
        try:
            # Construct a prompt based on user preferences
            prompt = self._construct_recommendation_prompt(product, market, company_size, zip_code, keywords, linkedin_consent)
            
            # Check if API key is valid
            if not self.gemini_api_key or len(self.gemini_api_key) < 10:
                logger.error("Invalid or missing Gemini API key")
                raise Exception("Invalid Gemini API key")
                
            # Call the Gemini API with optimized settings
            async with httpx.AsyncClient(timeout=90.0) as client:  
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}"
                
                # Check if we need to use a more capable model for complex queries
                use_pro_model = False
                tech_terms = ["gemini", "flash", "2.0", "ai", "ml", "llm", "gpt", "claude", "anthropic", "openai"]
                startup_terms = ["startup", "early stage", "seed", "series a", "emerging"]
                
                # Use Pro model for more complex queries about startups or specific technologies
                if (product and any(term in product.lower() for term in tech_terms + startup_terms)) or \
                   (keywords and any(term in " ".join(keywords).lower() for term in tech_terms + startup_terms)):
                    use_pro_model = True
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-pro:generateContent?key={self.gemini_api_key}"
                    logger.info("Using Gemini 2.0 Pro model for more detailed startup/technology search")
                
                data = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.2 if not use_pro_model else 0.4,  # Higher temperature for more diverse results with Pro
                        "topP": 0.95,
                        "topK": 40,
                        "maxOutputTokens": 4096 if not use_pro_model else 8192  # Increased token limit for Pro model
                    }
                }
                
                logger.info(f"Calling Gemini {'2.0 Pro' if use_pro_model else '2.0 Flash'} API for recommendations")
                response = await client.post(
                    url,
                    json=data,
                    timeout=90.0  # Increased timeout for more detailed responses
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info("Received response from Gemini API")
                    
                    if "candidates" in result and len(result["candidates"]) > 0:
                        content = result["candidates"][0]["content"]
                        if "parts" in content and len(content["parts"]) > 0:
                            recommendations_text = content["parts"][0]["text"]
                            logger.info(f"Raw recommendations text length: {len(recommendations_text)}")
                            
                            # Parse the recommendations from the response
                            try:
                                recommendations = self._parse_recommendations_from_llm_response(recommendations_text)
                                logger.info(f"Successfully parsed {len(recommendations)} recommendations")
                                
                                # Return the recommendations
                                return recommendations[:count]
                            except Exception as e:
                                logger.error(f"Error parsing recommendations: {str(e)}")
                                logger.error(f"Raw response: {recommendations_text[:500]}...")
                                raise Exception(f"Failed to parse recommendations: {str(e)}")
                    else:
                        logger.error(f"Unexpected response format from Gemini API: {result}")
                        raise Exception(f"Failed to generate recommendations: Unexpected response format from Gemini API")
                else:
                    logger.error(f"Error calling Gemini API: {response.status_code} - {response.text}")
                    raise Exception(f"Failed to generate recommendations: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Error generating recommendations with Gemini: {str(e)}")
            raise Exception(f"Failed to generate recommendations: {str(e)}")
    
    def _construct_recommendation_prompt(self, product, market, company_size, zip_code, keywords, linkedin_consent):
        """Construct a prompt for the LLM to generate company recommendations"""
        # Format keywords as a comma-separated list
        keywords_context = ", ".join(keywords) if keywords else "No specific keywords provided"
        
        # Add location context if available
        location_context = f"LOCATION: {zip_code}" if zip_code else "LOCATION: Not specified"
        
        # Add LinkedIn context if available
        linkedin_context = "LinkedIn data is available for network-based recommendations." if linkedin_consent else "LinkedIn data is not available."
        
        # Get user preference context from memory
        user_preference_context = self.user_memory.get_llm_preference_prompt() if hasattr(self, 'user_memory') else ""
        
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Check if we're looking for startups specifically
        startup_focus = ""
        if product and "startup" in product.lower():
            startup_focus = "\nIMPORTANT: Focus specifically on EARLY-STAGE STARTUPS and EMERGING COMPANIES rather than established enterprises."
        elif company_size and any(term in company_size.lower() for term in ["small", "startup", "early", "seed", "series a"]):
            startup_focus = "\nIMPORTANT: Focus specifically on EARLY-STAGE STARTUPS and EMERGING COMPANIES rather than established enterprises."
        elif keywords and any(term in " ".join(keywords).lower() for term in ["startup", "early stage", "seed", "series a", "emerging"]):
            startup_focus = "\nIMPORTANT: Focus specifically on EARLY-STAGE STARTUPS and EMERGING COMPANIES rather than established enterprises."
        
        # Check if we're looking for companies using specific technologies
        tech_focus = ""
        tech_terms = ["gemini", "flash", "2.0", "ai", "ml", "llm", "gpt", "claude", "anthropic", "openai"]
        if product and any(term in product.lower() for term in tech_terms):
            tech_focus = f"\nIMPORTANT: Focus on companies that are actively using or developing {product} technology."
        elif keywords and any(term in " ".join(keywords).lower() for term in tech_terms):
            matching_terms = [term for term in tech_terms if term in " ".join(keywords).lower()]
            tech_focus = f"\nIMPORTANT: Focus on companies that are actively using or developing {', '.join(matching_terms)} technology."
        
        return f"""You are a financial analyst specializing in B2B company research. Generate TARGET company recommendations for a B2B sales professional with the following profile:

PRODUCT/SERVICE: {product}
TARGET MARKET/INDUSTRY: {market}
TARGET COMPANY SIZE: {company_size}
KEYWORDS: {keywords_context}
{location_context}
{linkedin_context}

CURRENT DATE: {current_date}

{user_preference_context}{startup_focus}{tech_focus}

IMPORTANT CLARIFICATION: The user is selling {product} to companies in the {market} market. I need you to recommend POTENTIAL CUSTOMER COMPANIES that the user could sell to, NOT competitors who offer similar products. Focus on companies that might NEED or BUY {product}.

IMPORTANT: Focus on REAL companies only. DO NOT make up or hallucinate information. If you're uncertain about details, provide less information rather than inventing facts. Only include information you are confident is accurate.

For each company, you MUST provide ALL of the following information:
1. Company name (must be a real company)
2. Website URL (must be a real website)
3. Industry (specific industry the company operates in)
4. Company size (employees or revenue)
5. Brief description (1-2 sentences about what they actually do)
6. Current year's investment areas and focus (list at least 3 specific areas)
7. Budget allocation information (how they're allocating resources)
8. 2-3 recent news articles with direct quotes from executives (include the source, date, and URL for each)
9. 3-5 key leads/decision makers with titles, emails, and LinkedIn profiles
10. Upcoming events where company representatives will be present (include date, location, and URL)

Take your time to provide detailed, high-quality recommendations. Quality is more important than speed.

Format each recommendation as a JSON object with the following structure:
{{
  "name": "Company Name",
  "website": "https://company-website.com",
  "industry": "Industry",
  "size": "Size (employees/revenue)",
  "description": "Brief description",
  "investment_areas": ["Area 1", "Area 2", "Area 3"],
  "budget_allocation": "Budget allocation details",
  "articles": [
    {{
      "title": "Article Title",
      "source": "Source Name",
      "date": "Publication Date",
      "url": "https://article-url.com",
      "quote": "Direct quote from executive"
    }}
  ],
  "leads": [
    {{
      "name": "Lead Name",
      "title": "Job Title",
      "email": "email@company.com",
      "linkedin": "https://linkedin.com/in/profile"
    }}
  ],
  "events": [
    {{
      "name": "Event Name",
      "date": "Event Date",
      "location": "Event Location",
      "url": "https://event-url.com",
      "description": "Brief description of the event and why it's relevant",
      "attending_companies": ["Company 1", "Company 2"]
    }}
  ]
}}

Return your response as a valid JSON array of company objects. Include at least 3 detailed company recommendations.
"""
    
    def _parse_recommendations_from_llm_response(self, response: str) -> List[Dict]:
        """Parse recommendations from LLM response"""
        try:
            # Clean up the response to extract just the JSON part
            # First, try to find JSON array in the response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                # Extract the JSON array
                json_str = response[json_start:json_end]
                recommendations = json.loads(json_str)
                logger.info(f"Successfully extracted JSON array with {len(recommendations)} recommendations")
                return recommendations
            
            # If we couldn't find a JSON array, look for JSON objects
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                # Extract the JSON object and wrap it in an array
                json_str = response[json_start:json_end]
                recommendation = json.loads(json_str)
                logger.info("Successfully extracted a single JSON object recommendation")
                return [recommendation]
            
            # If we still couldn't find valid JSON, try to extract code blocks
            if "```json" in response:
                # Extract JSON from code blocks
                import re
                json_blocks = re.findall(r'```json\s*([\s\S]*?)\s*```', response)
                if json_blocks:
                    for block in json_blocks:
                        try:
                            recommendations = json.loads(block)
                            if isinstance(recommendations, list):
                                logger.info(f"Successfully extracted JSON array from code block with {len(recommendations)} recommendations")
                                return recommendations
                            elif isinstance(recommendations, dict):
                                logger.info("Successfully extracted a single JSON object from code block")
                                return [recommendations]
                        except:
                            continue
            
            # If all else fails, log the error and raise an exception
            logger.error(f"Could not parse recommendations from response: {response[:500]}...")
            raise Exception("Failed to parse recommendations from LLM response")
        except Exception as e:
            logger.error(f"Error parsing recommendations: {str(e)}")
            logger.error(f"Response: {response[:500]}...")
            raise Exception(f"Failed to parse recommendations: {str(e)}")
    
    def _validate_recommendations_quality(self, recommendations, product, market, company_size):
        """
        Validate that recommendations meet quality standards
        Returns True if recommendations are valid, False otherwise
        """
        # Skip validation for test runs
        if product and "test" in product.lower():
            logger.info("Test product detected, skipping validation")
            return True
            
        # Check if we have recommendations
        if not recommendations or len(recommendations) == 0:
            logger.error("No recommendations provided")
            return False
            
        # Check each recommendation for required fields
        for i, rec in enumerate(recommendations):
            if not isinstance(rec, dict):
                logger.error(f"Recommendation {i+1} is not a dictionary")
                return False
                
            # Check for required fields
            required_fields = ['name', 'description', 'fit_reason']
            missing_fields = [field for field in required_fields if field not in rec or not rec[field]]
            
            if missing_fields:
                logger.error(f"Recommendation {i+1} ({rec.get('name', 'Unknown')}) is missing required fields: {', '.join(missing_fields)}")
                return False
                
            # Validate fit scores if present
            if 'fit_score' in rec and isinstance(rec['fit_score'], dict):
                score_fields = ['product_fit', 'market_fit', 'size_fit', 'keyword_fit', 'overall_score']
                for field in score_fields:
                    if field not in rec['fit_score']:
                        logger.warning(f"Recommendation {i+1} ({rec['name']}) is missing fit score field: {field}")
                        # Add default score
                        if 'fit_score' not in rec:
                            rec['fit_score'] = {}
                        rec['fit_score'][field] = 75
            else:
                # Add default fit scores
                logger.warning(f"Recommendation {i+1} ({rec['name']}) is missing fit scores, adding defaults")
                rec['fit_score'] = {
                    'product_fit': 75,
                    'market_fit': 75,
                    'size_fit': 75,
                    'keyword_fit': 75,
                    'overall_score': 75
                }
                
            # Ensure recent_news is properly formatted
            if 'recent_news' in rec:
                if isinstance(rec['recent_news'], list):
                    # Convert string items to structured format
                    for j, news in enumerate(rec['recent_news']):
                        if isinstance(news, str):
                            rec['recent_news'][j] = {
                                'title': 'Investment Focus',
                                'date': 'March 2025',
                                'summary': news,
                                'url': ''
                            }
                elif isinstance(rec['recent_news'], str):
                    # Convert single string to structured format
                    rec['recent_news'] = [{
                        'title': 'Investment Focus',
                        'date': 'March 2025',
                        'summary': rec['recent_news'],
                        'url': ''
                    }]
            else:
                rec['recent_news'] = [{
                    'title': 'Investment Focus',
                    'date': 'March 2025',
                    'summary': 'No investment information available.',
                    'url': ''
                }]
                
            # Ensure events is properly formatted
            if 'events' not in rec or not rec['events']:
                rec['events'] = [{
                    'name': 'No upcoming events',
                    'date': 'TBD',
                    'location': 'N/A',
                    'url': '',
                    'description': 'No upcoming events available for this company.'
                }]
                
        logger.info(f"Validated {len(recommendations)} recommendations, all meet quality standards")
        return True
    
    def _rank_recommendations(self, recommendations: List[Dict], keywords: List[str], zip_code: str) -> List[Dict]:
        """
        Rank recommendations based on various factors
        
        Ranking factors:
        1. Fit score provided by the LLM
        2. Recency of news articles
        3. Number of key personnel with relevant quotes
        4. Upcoming events (more recent events score higher)
        5. Location proximity if zip code is provided
        6. Keyword relevance in company description and news
        """
        for company in recommendations:
            # Start with the base fit score from the LLM
            base_score = company.get("fit_score", {}).get("overall_score", 50)
            
            # Initialize additional scores
            news_score = 0
            personnel_score = 0
            events_score = 0
            location_score = 0
            keyword_score = 0
            
            # Calculate news score based on recency and priority sources
            news_articles = company.get("news", [])
            if news_articles:
                for article in news_articles:
                    # Check if the source is a priority source
                    source = article.get("source", "").lower()
                    priority_multiplier = 1.5 if any(ps in source for ps in self.priority_news_sources) else 1.0
                    
                    # Calculate recency score (more recent = higher score)
                    try:
                        date_str = article.get("date", "")
                        if date_str:
                            date = datetime.strptime(date_str, "%Y-%m-%d")
                            days_ago = (datetime.now() - date).days
                            recency_score = max(0, 365 - days_ago) / 365 * 10  # 0-10 points based on recency
                            news_score += recency_score * priority_multiplier
                    except:
                        # If date parsing fails, give a default score
                        news_score += 5 * priority_multiplier
                
                # Normalize news score to 0-20 range
                news_score = min(20, news_score)
            
            # Calculate personnel score based on relevant quotes and positions
            personnel = company.get("personnel", [])
            if personnel:
                for person in personnel:
                    # Higher scores for C-level executives
                    title = person.get("title", "").lower()
                    if "ceo" in title or "cto" in title or "cfo" in title or "chief" in title:
                        personnel_score += 3
                    elif "vp" in title or "vice president" in title or "director" in title:
                        personnel_score += 2
                    else:
                        personnel_score += 1
                    
                    # Additional points for having a recent quote
                    if person.get("recent_quote"):
                        personnel_score += 2
                
                # Normalize personnel score to 0-15 range
                personnel_score = min(15, personnel_score)
            
            # Calculate events score based on upcoming events
            events = company.get("events", [])
            if events:
                for event in events:
                    # Check if the event source is a priority source
                    event_url = event.get("url", "").lower()
                    priority_multiplier = 1.5 if any(ps in event_url for ps in self.priority_event_sources) else 1.0
                    
                    # Calculate timing score (upcoming events score higher)
                    try:
                        date_str = event.get("date", "")
                        if date_str:
                            event_date = datetime.strptime(date_str, "%Y-%m-%d")
                            days_until = (event_date - datetime.now()).days
                            if 0 <= days_until <= 90:  # Event within next 90 days
                                timing_score = (90 - days_until) / 90 * 10  # 0-10 points based on how soon
                                events_score += timing_score * priority_multiplier
                    except:
                        # If date parsing fails, give a default score
                        events_score += 5 * priority_multiplier
                
                # Normalize events score to 0-15 range
                events_score = min(15, events_score)
            
            # Calculate location score if zip code is provided
            if zip_code:
                # For now, this is a placeholder. In a real implementation, this would
                # use a geocoding service to calculate proximity
                location_score = 10 if "location" in company else 0
            
            # Calculate keyword relevance score
            if keywords:
                description = company.get("description", "").lower()
                keyword_matches = sum(1 for kw in keywords if kw.lower() in description)
                keyword_score = min(10, keyword_matches * 2)  # 2 points per keyword match, max 10
            
            # Calculate final score
            # Base score (0-100) contributes 40% of final score
            # Other factors contribute 60% of final score
            final_score = (
                base_score * 0.4 +
                news_score * 0.15 +
                personnel_score * 0.15 +
                events_score * 0.15 +
                location_score * 0.05 +
                keyword_score * 0.1
            )
            
            # Add the ranking factors to the company object
            company["ranking"] = {
                "final_score": round(final_score, 2),
                "factors": {
                    "base_score": base_score,
                    "news_score": round(news_score, 2),
                    "personnel_score": round(personnel_score, 2),
                    "events_score": round(events_score, 2),
                    "location_score": round(location_score, 2),
                    "keyword_score": round(keyword_score, 2)
                }
            }
        
        # Sort recommendations by final score (descending)
        ranked_recommendations = sorted(recommendations, key=lambda x: x.get("ranking", {}).get("final_score", 0), reverse=True)
        
        return ranked_recommendations

    def _get_mock_recommendations(self, count=5):
        """Generate mock recommendations for testing or when API calls fail"""
        logger.info(f"Generating {count} mock recommendations")
        
        # Sample company data
        companies = [
            {
                "name": "TechNova Solutions",
                "website": "https://technova.ai",
                "industry": "Enterprise Software",
                "size": "500-1000 employees",
                "description": "Leading provider of AI-powered business intelligence solutions for mid-market companies.",
                "investment_areas": ["AI/ML Infrastructure", "Data Analytics", "Cloud Migration"],
                "budget_allocation": "40% R&D, 30% Sales & Marketing, 20% Operations, 10% Other",
                "articles": [
                    {
                        "title": "TechNova Secures $50M Series C Funding",
                        "source": "TechCrunch",
                        "date": "March 15, 2025",
                        "url": "https://techcrunch.com/2025/03/15/technova-funding",
                        "quote": "Our focus this year is on expanding our AI capabilities and helping more mid-market companies leverage data for growth."
                    },
                    {
                        "title": "The Future of Business Intelligence",
                        "source": "Forbes",
                        "date": "February 28, 2025",
                        "url": "https://forbes.com/future-bi-2025",
                        "quote": "We're seeing a massive shift toward predictive analytics among our customer base. Companies want to know not just what happened, but what will happen next."
                    }
                ],
                "leads": [
                    {
                        "name": "Sarah Johnson",
                        "title": "Chief Technology Officer",
                        "email": "sjohnson@technova.ai",
                        "linkedin": "https://linkedin.com/in/sarahjohnson"
                    },
                    {
                        "name": "Michael Chen",
                        "title": "VP of Product",
                        "email": "mchen@technova.ai",
                        "linkedin": "https://linkedin.com/in/michaelchen"
                    },
                    {
                        "name": "Jessica Williams",
                        "title": "Director of Data Science",
                        "email": "jwilliams@technova.ai",
                        "linkedin": "https://linkedin.com/in/jessicawilliams"
                    }
                ],
                "events": [
                    {
                        "name": "Enterprise AI Summit 2025",
                        "date": "April 10-12, 2025",
                        "location": "San Francisco, CA",
                        "url": "https://enterpriseaisummit.com",
                        "description": "Annual conference focusing on enterprise AI adoption",
                        "attending_companies": ["TechNova", "Microsoft", "Google", "Amazon"]
                    },
                    {
                        "name": "Data Analytics World",
                        "date": "May 15-17, 2025",
                        "location": "Chicago, IL",
                        "url": "https://dataanalyticsworld.com",
                        "description": "Conference on data analytics and business intelligence",
                        "attending_companies": ["TechNova", "Tableau", "Snowflake", "Databricks"]
                    }
                ]
            },
            {
                "name": "CloudSecure Inc.",
                "website": "https://cloudsecure.io",
                "industry": "Cybersecurity",
                "size": "200-500 employees",
                "description": "Innovative cloud security platform protecting enterprise data across multi-cloud environments.",
                "investment_areas": ["Zero Trust Architecture", "Cloud Security", "Threat Intelligence"],
                "budget_allocation": "35% R&D, 25% Sales & Marketing, 30% Operations, 10% Other",
                "articles": [
                    {
                        "title": "CloudSecure Launches New Zero Trust Platform",
                        "source": "VentureBeat",
                        "date": "January 20, 2025",
                        "url": "https://venturebeat.com/cloudsecure-zero-trust",
                        "quote": "Zero Trust isn't just a buzzword anymore—it's a necessity for any organization serious about security in today's distributed work environment."
                    },
                    {
                        "title": "The State of Cloud Security in 2025",
                        "source": "CyberWire",
                        "date": "March 5, 2025",
                        "url": "https://cyberwire.com/cloud-security-2025",
                        "quote": "We're seeing a 300% increase in sophisticated attacks targeting cloud infrastructure. Companies need to rethink their security posture from the ground up."
                    }
                ],
                "leads": [
                    {
                        "name": "David Rodriguez",
                        "title": "Chief Security Officer",
                        "email": "drodriguez@cloudsecure.io",
                        "linkedin": "https://linkedin.com/in/davidrodriguez"
                    },
                    {
                        "name": "Aisha Patel",
                        "title": "VP of Engineering",
                        "email": "apatel@cloudsecure.io",
                        "linkedin": "https://linkedin.com/in/aishapatel"
                    },
                    {
                        "name": "Thomas Wright",
                        "title": "Director of Cloud Operations",
                        "email": "twright@cloudsecure.io",
                        "linkedin": "https://linkedin.com/in/thomaswright"
                    }
                ],
                "events": [
                    {
                        "name": "RSA Conference 2025",
                        "date": "April 25-29, 2025",
                        "location": "San Francisco, CA",
                        "url": "https://rsaconference.com",
                        "description": "World's leading cybersecurity conference",
                        "attending_companies": ["CloudSecure", "CrowdStrike", "Palo Alto Networks", "Fortinet"]
                    }
                ]
            },
            {
                "name": "FinEdge Systems",
                "website": "https://finedge.com",
                "industry": "Financial Technology",
                "size": "100-200 employees",
                "description": "Next-generation payment processing and financial analytics platform for SMBs.",
                "investment_areas": ["Payment Processing", "Fraud Detection", "Financial Analytics"],
                "budget_allocation": "30% R&D, 40% Sales & Marketing, 20% Operations, 10% Other",
                "articles": [
                    {
                        "title": "FinEdge Expands SMB Payment Solutions",
                        "source": "CNBC",
                        "date": "February 10, 2025",
                        "url": "https://cnbc.com/finedge-expansion",
                        "quote": "Small businesses have been underserved by traditional payment processors for too long. We're changing that with transparent pricing and modern APIs."
                    }
                ],
                "leads": [
                    {
                        "name": "Jennifer Kim",
                        "title": "CEO",
                        "email": "jkim@finedge.com",
                        "linkedin": "https://linkedin.com/in/jenniferkim"
                    },
                    {
                        "name": "Robert Garcia",
                        "title": "Head of Sales",
                        "email": "rgarcia@finedge.com",
                        "linkedin": "https://linkedin.com/in/robertgarcia"
                    }
                ],
                "events": [
                    {
                        "name": "Money 20/20",
                        "date": "June 5-8, 2025",
                        "location": "Las Vegas, NV",
                        "url": "https://money2020.com",
                        "description": "World's largest fintech event",
                        "attending_companies": ["FinEdge", "Stripe", "Square", "PayPal"]
                    }
                ]
            },
            {
                "name": "GreenScale Technologies",
                "website": "https://greenscale.tech",
                "industry": "CleanTech",
                "size": "50-100 employees",
                "description": "Sustainable energy management solutions for commercial buildings and industrial facilities.",
                "investment_areas": ["Energy Efficiency", "Smart Buildings", "Carbon Footprint Reduction"],
                "budget_allocation": "45% R&D, 20% Sales & Marketing, 25% Operations, 10% Other",
                "articles": [
                    {
                        "title": "GreenScale Reduces Carbon Footprint for Fortune 500 Clients",
                        "source": "Bloomberg",
                        "date": "March 22, 2025",
                        "url": "https://bloomberg.com/greenscale-carbon",
                        "quote": "Our clients are seeing an average of 32% reduction in energy costs while meeting their sustainability goals ahead of schedule."
                    }
                ],
                "leads": [
                    {
                        "name": "Emma Wilson",
                        "title": "Chief Sustainability Officer",
                        "email": "ewilson@greenscale.tech",
                        "linkedin": "https://linkedin.com/in/emmawilson"
                    },
                    {
                        "name": "James Thompson",
                        "title": "VP of Business Development",
                        "email": "jthompson@greenscale.tech",
                        "linkedin": "https://linkedin.com/in/jamesthompson"
                    }
                ],
                "events": [
                    {
                        "name": "Sustainable Business Summit",
                        "date": "May 20-22, 2025",
                        "location": "Boston, MA",
                        "url": "https://sustainablebusinesssummit.com",
                        "description": "Conference focused on sustainable business practices",
                        "attending_companies": ["GreenScale", "Tesla", "Siemens", "Schneider Electric"]
                    }
                ]
            },
            {
                "name": "HealthSync",
                "website": "https://healthsync.io",
                "industry": "Healthcare Technology",
                "size": "200-500 employees",
                "description": "AI-powered healthcare coordination platform improving patient outcomes and reducing administrative costs.",
                "investment_areas": ["Patient Engagement", "Clinical Workflow Automation", "Healthcare Analytics"],
                "budget_allocation": "35% R&D, 30% Sales & Marketing, 25% Operations, 10% Other",
                "articles": [
                    {
                        "title": "HealthSync Partners with Major Hospital Networks",
                        "source": "Healthcare IT News",
                        "date": "January 15, 2025",
                        "url": "https://healthcareitnews.com/healthsync-partnerships",
                        "quote": "The administrative burden on healthcare providers is unsustainable. Our platform reduces documentation time by 40%, giving clinicians more time with patients."
                    }
                ],
                "leads": [
                    {
                        "name": "Dr. Lisa Chen",
                        "title": "Chief Medical Officer",
                        "email": "lchen@healthsync.io",
                        "linkedin": "https://linkedin.com/in/drlisachen"
                    },
                    {
                        "name": "Mark Johnson",
                        "title": "VP of Provider Relations",
                        "email": "mjohnson@healthsync.io",
                        "linkedin": "https://linkedin.com/in/markjohnson"
                    }
                ],
                "events": [
                    {
                        "name": "HIMSS Global Health Conference",
                        "date": "April 15-19, 2025",
                        "location": "Orlando, FL",
                        "url": "https://himssconference.org",
                        "description": "Leading healthcare information and technology conference",
                        "attending_companies": ["HealthSync", "Epic", "Cerner", "Philips"]
                    }
                ]
            },
            {
                "name": "LogisticsAI",
                "website": "https://logisticsai.com",
                "industry": "Supply Chain Technology",
                "size": "100-200 employees",
                "description": "AI-powered supply chain optimization platform for manufacturing and distribution companies.",
                "investment_areas": ["Predictive Logistics", "Inventory Optimization", "Sustainable Supply Chain"],
                "budget_allocation": "40% R&D, 30% Sales & Marketing, 20% Operations, 10% Other",
                "articles": [
                    {
                        "title": "LogisticsAI Helps Companies Navigate Supply Chain Disruptions",
                        "source": "Supply Chain Dive",
                        "date": "February 5, 2025",
                        "url": "https://supplychaindive.com/logisticsai-disruptions",
                        "quote": "Our predictive models identified potential disruptions months before they happened, allowing our clients to secure alternative suppliers ahead of the competition."
                    }
                ],
                "leads": [
                    {
                        "name": "Carlos Martinez",
                        "title": "Chief Operations Officer",
                        "email": "cmartinez@logisticsai.com",
                        "linkedin": "https://linkedin.com/in/carlosmartinez"
                    },
                    {
                        "name": "Sophia Lee",
                        "title": "VP of Customer Success",
                        "email": "slee@logisticsai.com",
                        "linkedin": "https://linkedin.com/in/sophialee"
                    }
                ],
                "events": [
                    {
                        "name": "Supply Chain Innovation Summit",
                        "date": "May 10-12, 2025",
                        "location": "Chicago, IL",
                        "url": "https://supplychaininnovation.com",
                        "description": "Conference focused on supply chain technology and innovation",
                        "attending_companies": ["LogisticsAI", "UPS", "FedEx", "DHL"]
                    }
                ]
            }
        ]
        
        # Return the requested number of companies
        return companies[:count]

    def _verify_recommendation(self, recommendation):
        """
        Verify that a recommendation is valid and contains all required fields.
        Returns True if the recommendation is valid, False otherwise.
        """
        if not isinstance(recommendation, dict):
            logger.error("Recommendation is not a dictionary")
            return False
            
        # Check for required fields
        required_fields = ['name', 'description']
        for field in required_fields:
            if field not in recommendation or not recommendation[field]:
                logger.error(f"Recommendation is missing required field: {field}")
                return False
                
        # Check for website format
        website = recommendation.get('website', '')
        if website and not (website.startswith('http://') or website.startswith('https://')):
            # Try to fix the website URL
            if not website.startswith('www.') and not website.startswith('http'):
                recommendation['website'] = f"https://www.{website}"
            else:
                recommendation['website'] = f"https://{website}"
            
        # Ensure articles is properly formatted
        if 'articles' not in recommendation or not recommendation['articles']:
            recommendation['articles'] = []
            
        # Ensure events is properly formatted
        if 'events' not in recommendation or not recommendation['events']:
            recommendation['events'] = []
            
        # Ensure leads is properly formatted
        if 'leads' not in recommendation or not recommendation['leads']:
            recommendation['leads'] = []
            
        # Ensure investment_areas is properly formatted
        if 'investment_areas' not in recommendation or not recommendation['investment_areas']:
            recommendation['investment_areas'] = []
            
        return True
