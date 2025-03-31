import asyncio
import httpx
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_keyword_generation():
    """Test the keyword generation API endpoint."""
    logger.info("Testing keyword generation...")
    
    # Sample conversation flow data
    conversation_data = [
        {"step": "product", "text": "We're building an event discovery platform that helps founders find industry events"},
        {"step": "market", "text": "Technology and startup events industry"},
        {"step": "differentiation", "text": "We use AI to match founders with events where their target customers will be attending"},
        {"step": "company_size", "text": "Early-stage startups and small businesses"},
        {"step": "linkedin", "text": "yes"},
        {"step": "location", "text": "94105"}
    ]
    
    async with httpx.AsyncClient() as client:
        # Process each step of the conversation
        for data in conversation_data:
            response = await client.post(
                "http://localhost:9001/api/voice_interaction",
                json=data
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"API response for {data['step']} step: {result}")
        
        # Get the generated keywords
        keywords_response = await client.get("http://localhost:9001/api/keywords")
        keywords_response.raise_for_status()
        keywords_data = keywords_response.json()
        logger.info(f"Generated keywords: {keywords_data}")
        
        return keywords_data.get("keywords", [])

async def test_event_search(keywords, location="San Francisco, CA"):
    """Test the event search API endpoint."""
    logger.info(f"Testing event search with keywords: {keywords} and location: {location}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:9001/api/search_events",
            json={
                "keywords": keywords,
                "location": location
            }
        )
        response.raise_for_status()
        events = response.json()
        
        logger.info(f"Found {len(events)} events:")
        for i, event in enumerate(events, 1):
            logger.info(f"\nEvent {i}:")
            logger.info(f"Title: {event['title']}")
            logger.info(f"Date: {event['date']}")
            logger.info(f"Location: {event['location']}")
            logger.info(f"Description: {event['description']}")
            logger.info(f"Matching Keywords: {event['matchingKeywords']}")
            logger.info(f"URL: {event['url']}")
        
        return events

async def main():
    """Main test function."""
    try:
        # First, generate keywords through the conversation flow
        keywords = await test_keyword_generation()
        
        # Then, search for events using those keywords
        if keywords:
            await test_event_search(keywords)
        else:
            logger.error("No keywords generated, cannot test event search.")
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
