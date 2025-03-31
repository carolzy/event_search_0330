import logging
import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import json
import re
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventScraper:
    """
    Scraper for Luma Events based on keywords and location.
    Adapts browser automation techniques from OpenManus project.
    """
    
    def __init__(self):
        self.base_url = "https://lu.ma/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
    
    async def search_events(self, keywords, location=None, max_results=10):
        """
        Search for events based on keywords and location.
        
        Args:
            keywords (list): List of keywords to search for
            location (str, optional): Location to search in. Defaults to None.
            max_results (int, optional): Maximum number of results to return. Defaults to 10.
            
        Returns:
            list: List of event dictionaries
        """
        # Select the most relevant keywords (max 5)
        search_keywords = self._select_relevant_keywords(keywords, max_keywords=5)
        logger.info(f"Searching for events with keywords: {search_keywords}")
        
        # Combine keywords into a search query
        search_query = " ".join(search_keywords)
        
        # Add location if provided
        if location:
            search_query += f" {location}"
        
        # Encode the search query for URL
        encoded_query = quote_plus(search_query)
        search_url = f"{self.base_url}?q={encoded_query}"
        
        try:
            # Fetch the search results page
            async with httpx.AsyncClient() as client:
                response = await client.get(search_url, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                
                # Parse the HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract events
                events = self._extract_events_from_html(soup, keywords)
                
                # Limit the number of results
                return events[:max_results]
                
        except Exception as e:
            logger.error(f"Error searching for events: {str(e)}")
            return []
    
    def _select_relevant_keywords(self, keywords, max_keywords=5):
        """
        Select the most relevant keywords for the search.
        
        Args:
            keywords (list): List of all keywords
            max_keywords (int, optional): Maximum number of keywords to select. Defaults to 5.
            
        Returns:
            list: List of selected keywords
        """
        # For now, just take the first few keywords
        # In a more sophisticated implementation, we could use TF-IDF or other relevance metrics
        return keywords[:max_keywords]
    
    def _extract_events_from_html(self, soup, all_keywords):
        """
        Extract events from the HTML soup.
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object of the search results page
            all_keywords (list): List of all keywords to match against event descriptions
            
        Returns:
            list: List of event dictionaries
        """
        events = []
        
        # This is a mock implementation since we don't have the actual HTML structure
        # In a real implementation, we would inspect the HTML and extract the events accordingly
        # For demonstration purposes, we'll generate some mock events based on the keywords
        
        # Mock event data (in a real implementation, this would be extracted from the HTML)
        mock_events = [
            {
                "title": "Tech Startup Networking Event",
                "date": (datetime.now() + timedelta(days=7)).isoformat(),
                "location": "San Francisco, CA",
                "description": "Join us for a networking event for tech startups and founders. Meet investors and potential partners.",
                "url": "https://lu.ma/event/tech-startup-networking",
                "keywords": ["tech", "startup", "networking", "founders", "investors"]
            },
            {
                "title": "AI Innovation Summit",
                "date": (datetime.now() + timedelta(days=14)).isoformat(),
                "location": "Palo Alto, CA",
                "description": "A conference focused on AI innovation and applications in various industries.",
                "url": "https://lu.ma/event/ai-innovation-summit",
                "keywords": ["AI", "innovation", "technology", "machine learning", "startups"]
            },
            {
                "title": "Founder Meetup: Early Stage Funding",
                "date": (datetime.now() + timedelta(days=5)).isoformat(),
                "location": "New York, NY",
                "description": "A meetup for founders looking for early-stage funding. Learn from VCs and angel investors.",
                "url": "https://lu.ma/event/founder-meetup-funding",
                "keywords": ["founder", "funding", "VC", "angel investors", "early-stage", "startup"]
            },
            {
                "title": "Marketing Strategies for Startups",
                "date": (datetime.now() + timedelta(days=10)).isoformat(),
                "location": "Austin, TX",
                "description": "Learn effective marketing strategies for startups with limited budgets.",
                "url": "https://lu.ma/event/startup-marketing-strategies",
                "keywords": ["marketing", "startups", "growth", "customer acquisition", "strategy"]
            },
            {
                "title": "Seed Stage Pitch Competition",
                "date": (datetime.now() + timedelta(days=21)).isoformat(),
                "location": "Boston, MA",
                "description": "Pitch your seed-stage startup to a panel of investors and win funding.",
                "url": "https://lu.ma/event/seed-stage-pitch-competition",
                "keywords": ["pitch", "seed stage", "funding", "investors", "startup", "competition"]
            }
        ]
        
        # Filter and rank mock events based on keyword matches
        for event in mock_events:
            # Count how many keywords match
            matching_keywords = []
            for keyword in all_keywords:
                # Check if the keyword is in the title, description, or event keywords
                keyword_lower = keyword.lower()
                if (keyword_lower in event["title"].lower() or 
                    keyword_lower in event["description"].lower() or 
                    any(keyword_lower in k.lower() for k in event["keywords"])):
                    matching_keywords.append(keyword)
            
            # Only include events with at least one matching keyword
            if matching_keywords:
                events.append({
                    "title": event["title"],
                    "date": event["date"],
                    "location": event["location"],
                    "description": event["description"],
                    "url": event["url"],
                    "matchingKeywords": matching_keywords
                })
        
        # Sort events by number of matching keywords (most matches first)
        events.sort(key=lambda x: len(x["matchingKeywords"]), reverse=True)
        
        return events

# For testing
async def test_scraper():
    scraper = EventScraper()
    keywords = ["startup", "founder", "networking", "tech", "innovation"]
    events = await scraper.search_events(keywords, "San Francisco")
    print(json.dumps(events, indent=2))

if __name__ == "__main__":
    asyncio.run(test_scraper())
