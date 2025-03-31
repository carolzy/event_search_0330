import asyncio
import httpx
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_api():
    """Test the API endpoints of the atom-voice-search application."""
    base_url = "http://localhost:5018"
    
    async with httpx.AsyncClient() as client:
        # Test 1: Get the first question
        logger.info("Test 1: Getting the first question")
        response = await client.get(f"{base_url}/api/get_question?step=product")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Question: {data.get('question')}")
            logger.info(f"Keywords: {data.get('keywords')}")
            logger.info("Test 1: Success")
        else:
            logger.error(f"Test 1 failed: {response.status_code} - {response.text}")
        
        # Test 2: Submit an answer and get the next question
        logger.info("\nTest 2: Submitting an answer")
        payload = {
            "step": "product",
            "answer": "We're building an event discovery platform that helps founders find industry events where they can meet potential customers"
        }
        response = await client.post(
            f"{base_url}/api/onboarding",
            json=payload
        )
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Next step: {data.get('step')}")
            logger.info(f"Next question: {data.get('question')}")
            logger.info("Test 2: Success")
        else:
            logger.error(f"Test 2 failed: {response.status_code} - {response.text}")
        
        # Test 3: Complete the onboarding flow
        logger.info("\nTest 3: Completing the onboarding flow")
        steps = [
            ("market", "Technology and startup events industry"),
            ("differentiation", "We use AI to match founders with events where their target customers will be attending"),
            ("company_size", "Early-stage startups and small businesses"),
            ("linkedin", "Yes"),
            ("location", "94103")
        ]
        
        for step, answer in steps:
            logger.info(f"Submitting answer for step: {step}")
            payload = {
                "step": step,
                "answer": answer
            }
            response = await client.post(
                f"{base_url}/api/onboarding",
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("completed"):
                    logger.info("Onboarding completed!")
                    logger.info(f"Final keywords: {data.get('keywords')}")
                    logger.info(f"Recommendations: {json.dumps(data.get('recommendations'), indent=2)}")
                    break
                else:
                    logger.info(f"Next step: {data.get('step')}")
                    logger.info(f"Next question: {data.get('question')}")
            else:
                logger.error(f"Step {step} failed: {response.status_code} - {response.text}")
        
        logger.info("Test 3: Success")
        
        # Test 4: Get recommendations
        logger.info("\nTest 4: Getting recommendations")
        response = await client.get(f"{base_url}/api/recommendations")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Recommendations count: {len(data)}")
            if data:
                logger.info(f"First recommendation: {json.dumps(data[0], indent=2)}")
            logger.info("Test 4: Success")
        else:
            logger.error(f"Test 4 failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(test_api())
