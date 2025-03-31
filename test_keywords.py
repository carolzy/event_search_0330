import asyncio
import logging
from flow_controller import FlowController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_keyword_generation():
    """Test the keyword generation functionality."""
    flow_controller = FlowController()
    
    # Test product step
    logger.info("Testing keyword generation for product step...")
    product_answer = "We're building an event discovery platform that helps founders find industry events where they can meet potential customers"
    await flow_controller.store_answer("product", product_answer)
    
    # Wait a moment for the API call to complete
    await asyncio.sleep(2)
    
    # Check if keywords were generated
    logger.info(f"Keywords after product step: {flow_controller.keywords}")
    
    # Test market step
    logger.info("\nTesting keyword generation for market step...")
    market_answer = "Technology and startup events industry"
    await flow_controller.store_answer("market", market_answer)
    
    # Wait a moment for the API call to complete
    await asyncio.sleep(2)
    
    # Check if keywords were updated
    logger.info(f"Keywords after market step: {flow_controller.keywords}")
    
    # Test differentiation step
    logger.info("\nTesting keyword generation for differentiation step...")
    diff_answer = "We use AI to match founders with events where their target customers will be attending"
    await flow_controller.store_answer("differentiation", diff_answer)
    
    # Wait a moment for the API call to complete
    await asyncio.sleep(2)
    
    # Check if keywords were updated
    logger.info(f"Keywords after differentiation step: {flow_controller.keywords}")
    
    # Test company_size step
    logger.info("\nTesting keyword generation for company_size step...")
    size_answer = "Early-stage startups and small businesses"
    await flow_controller.store_answer("company_size", size_answer)
    
    # Wait a moment for the API call to complete
    await asyncio.sleep(2)
    
    # Check if keywords were updated
    logger.info(f"Keywords after company_size step: {flow_controller.keywords}")
    
    # Test clean_keywords
    logger.info("\nTesting clean_keywords method...")
    cleaned_keywords = await flow_controller.clean_keywords()
    logger.info(f"Cleaned keywords: {cleaned_keywords}")

if __name__ == "__main__":
    asyncio.run(test_keyword_generation())
