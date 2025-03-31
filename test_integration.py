import asyncio
import logging
import json
from flow_controller_new import FlowController
from question_engine_new import QuestionEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_question_generation():
    """Test question generation for each step in the flow."""
    print("\n=== Testing Question Generation ===")
    
    question_engine = QuestionEngine()
    
    steps = ['product', 'market', 'differentiation', 'company_size', 'linkedin', 'location', 'complete']
    
    for step in steps:
        question = await question_engine.get_question(step)
        print(f"Step: {step}")
        print(f"Question: {question}")
        print("-" * 50)
    
    # Test with context
    context = {
        'product': 'AI-powered sales automation software',
        'market': 'SaaS companies',
        'differentiation': 'Uses natural language processing to automate outreach',
        'company_size': 'Mid-market (100-1000 employees)'
    }
    
    print("\n=== Testing Question Generation with Context ===")
    for step in steps:
        question = await question_engine.get_question(step, context)
        print(f"Step: {step}")
        print(f"Question: {question}")
        print("-" * 50)

async def test_keyword_generation():
    """Test keyword generation."""
    print("\n=== Testing Keyword Generation ===")
    
    question_engine = QuestionEngine()
    
    # Test with different contexts
    contexts = [
        {
            'product': 'AI-powered sales automation software',
            'market': 'SaaS companies',
            'differentiation': 'Uses natural language processing to automate outreach',
            'company_size': 'Mid-market (100-1000 employees)'
        },
        {
            'product': 'Cybersecurity threat detection platform',
            'market': 'Financial services',
            'differentiation': 'Real-time threat intelligence with AI',
            'company_size': 'Enterprise (1000+ employees)'
        },
        {
            'product': 'HR management software',
            'market': 'Healthcare',
            'differentiation': 'HIPAA compliant with integrated payroll',
            'company_size': 'Small business (10-100 employees)'
        }
    ]
    
    for i, context in enumerate(contexts):
        print(f"\nContext {i+1}:")
        for key, value in context.items():
            print(f"  {key}: {value}")
        
        keywords = await question_engine.generate_keywords(context)
        print("\nGenerated Keywords:")
        for keyword in keywords:
            print(f"  - {keyword}")
        print("-" * 50)

async def test_flow_controller():
    """Test the flow controller."""
    print("\n=== Testing Flow Controller ===")
    
    flow_controller = FlowController()
    
    # Test the flow
    current_step = 'product'
    print(f"Starting step: {current_step}")
    
    # Simulate a conversation
    conversation = [
        ('product', 'We sell an AI-powered sales automation platform that helps B2B companies find and engage with prospects.'),
        ('market', 'We target SaaS companies in the marketing and sales technology space.'),
        ('differentiation', 'Our platform uses natural language processing to personalize outreach at scale, which competitors cannot do.'),
        ('company_size', 'We focus on mid-market companies with 100-1000 employees.'),
        ('linkedin', 'Yes, I would like to connect my LinkedIn account.'),
        ('location', '94103')
    ]
    
    for step, answer in conversation:
        # Get question
        question = await flow_controller.get_question(step)
        print(f"\nStep: {step}")
        print(f"Question: {question}")
        
        # Store answer
        print(f"Answer: {answer}")
        await flow_controller.store_answer(step, answer)
        
        # Get follow-up question
        follow_up = await flow_controller.get_follow_up_question(step, answer)
        print(f"Follow-up: {follow_up}")
        
        # Move to next step
        next_step = flow_controller.get_next_step(step)
        print(f"Next step: {next_step}")
        print("-" * 50)
    
    # Check keywords
    keywords = await flow_controller.clean_keywords()
    print("\nGenerated Keywords:")
    for keyword in keywords:
        print(f"  - {keyword}")

async def test_compatibility():
    """Test compatibility with the existing app.py."""
    print("\n=== Testing Compatibility with app.py ===")
    
    flow_controller = FlowController()
    question_engine = QuestionEngine()
    
    # Test the methods used in app.py
    methods_to_test = [
        "get_question",
        "get_next_step",
        "store_answer",
        "clean_keywords",
        "reset"
    ]
    
    for method in methods_to_test:
        if hasattr(flow_controller, method):
            print(f"FlowController.{method}: ✓")
        else:
            print(f"FlowController.{method}: ✗ - Missing method!")
    
    # Test question engine methods
    qe_methods = [
        "get_question",
        "generate_keywords"
    ]
    
    for method in qe_methods:
        if hasattr(question_engine, method):
            print(f"QuestionEngine.{method}: ✓")
        else:
            print(f"QuestionEngine.{method}: ✗ - Missing method!")
    
    # Test initialization
    await flow_controller.reset()
    greeting = await question_engine.get_question("product")
    first_question = await flow_controller.get_question("product")
    
    print(f"\nGreeting: {greeting}")
    print(f"First question: {first_question}")

async def main():
    """Run all tests."""
    print("Starting integration tests...\n")
    
    await test_question_generation()
    await test_keyword_generation()
    await test_flow_controller()
    await test_compatibility()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
