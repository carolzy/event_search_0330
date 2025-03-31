import asyncio
import json
import logging
import httpx
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_api_endpoint():
    """Test the voice_interaction endpoint directly."""
    try:
        # First, test the product step
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:9001/api/voice_interaction",
                json={
                    "text": "We're building an event discovery platform that helps founders find industry events",
                    "step": "product"
                }
            )
            logger.info(f"API response for product step: {response.json()}")
            
            # Get the current keywords after product step
            keywords_response = await client.get("http://localhost:9001/api/keywords")
            if keywords_response.status_code == 200:
                logger.info(f"Keywords after product step: {keywords_response.json()}")
            else:
                logger.warning(f"Failed to get keywords after product step: {keywords_response.status_code}")
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Next, test the market step
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:9001/api/voice_interaction",
                json={
                    "text": "Technology and startup events industry",
                    "step": "market"
                }
            )
            logger.info(f"API response for market step: {response.json()}")
            
            # Get the current keywords after market step
            keywords_response = await client.get("http://localhost:9001/api/keywords")
            if keywords_response.status_code == 200:
                logger.info(f"Keywords after market step: {keywords_response.json()}")
            else:
                logger.warning(f"Failed to get keywords after market step: {keywords_response.status_code}")
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Next, test the differentiation step
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:9001/api/voice_interaction",
                json={
                    "text": "We use AI to match founders with events where their target customers will be attending",
                    "step": "differentiation"
                }
            )
            logger.info(f"API response for differentiation step: {response.json()}")
            
            # Get the current keywords after differentiation step
            keywords_response = await client.get("http://localhost:9001/api/keywords")
            if keywords_response.status_code == 200:
                logger.info(f"Keywords after differentiation step: {keywords_response.json()}")
            else:
                logger.warning(f"Failed to get keywords after differentiation step: {keywords_response.status_code}")
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Test the company_size step
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:9001/api/voice_interaction",
                json={
                    "text": "Early-stage startups and small businesses",
                    "step": "company_size"
                }
            )
            logger.info(f"API response for company_size step: {response.json()}")
            
            # Get the current keywords after company_size step
            keywords_response = await client.get("http://localhost:9001/api/keywords")
            if keywords_response.status_code == 200:
                logger.info(f"Keywords after company_size step: {keywords_response.json()}")
            else:
                logger.warning(f"Failed to get keywords after company_size step: {keywords_response.status_code}")
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Test the linkedin step
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:9001/api/voice_interaction",
                json={
                    "text": "Yes",
                    "step": "linkedin"
                }
            )
            logger.info(f"API response for linkedin step: {response.json()}")
            
            # Get the current keywords after linkedin step
            keywords_response = await client.get("http://localhost:9001/api/keywords")
            if keywords_response.status_code == 200:
                logger.info(f"Keywords after linkedin step: {keywords_response.json()}")
            else:
                logger.warning(f"Failed to get keywords after linkedin step: {keywords_response.status_code}")
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Finally, test the location step which should complete the flow
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:9001/api/voice_interaction",
                json={
                    "text": "94105",
                    "step": "location"
                }
            )
            logger.info(f"API response for location step: {response.json()}")
            
            # Get the final keywords after location step
            keywords_response = await client.get("http://localhost:9001/api/keywords")
            if keywords_response.status_code == 200:
                logger.info(f"Final keywords after location step: {keywords_response.json()}")
            else:
                logger.warning(f"Failed to get final keywords after location step: {keywords_response.status_code}")

    except Exception as e:
        logger.error(f"Error testing API endpoint: {str(e)}")

async def main():
    """Run the tests."""
    logger.info("Starting API endpoint test...")
    await test_api_endpoint()

if __name__ == "__main__":
    asyncio.run(main())
