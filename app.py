import logging
import time
from quart import Quart, render_template, request, jsonify, send_file
from flow_controller import FlowController
from voice_processor import VoiceProcessor
from question_engine import QuestionEngine
from company_recommender import CompanyRecommender
import asyncio


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Quart app
app = Quart(__name__, static_folder="static", template_folder="templates")
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Version for cache busting
VERSION = str(int(time.time()))

# Initialize core components
flow_controller = FlowController()
voice_processor = VoiceProcessor(flow_controller)
question_engine = QuestionEngine()
company_recommender = CompanyRecommender(flow_controller)

@app.route("/")
async def index():
    # Simply use await directly
    await flow_controller.reset()
    greeting = await question_engine.get_question("product")
    first_question = await flow_controller.get_question("product")
    return await render_template("index.html", greeting=greeting, first_question=first_question, version=VERSION)

@app.route("/api/onboarding", methods=["POST"])
async def onboarding_step():
    data = await request.get_json()
    step = data.get("step")
    answer = data.get("answer", "")
    logger.info(f"Onboarding: {step} => {answer}")
    
    await flow_controller.store_answer(step, answer)
    next_step = flow_controller.get_next_step(step)
    
    if next_step == "complete":
        cleaned_keywords = await flow_controller.clean_keywords()
        recommendations = await company_recommender.generate_recommendations()
        return jsonify({
            "success": True,
            "completed": True,
            "keywords": cleaned_keywords,
            "recommendations": recommendations
        })

    question = await flow_controller.get_question(next_step)
    audio_data = await voice_processor.text_to_speech(question)
    return jsonify({
        "success": True,
        "step": next_step,
        "question": question,
        "audio": audio_data,
        "keywords": flow_controller.keywords  # Always include current keywords
    })

@app.route("/api/get_question", methods=["GET"])
async def get_question():
    step = request.args.get("step", "product")
    question = await flow_controller.get_question(step)
    audio_data = await voice_processor.text_to_speech(question)
    return jsonify({
        "success": True,
        "question": question,
        "audio": audio_data,
        "keywords": flow_controller.keywords  # Always include current keywords
    })

@app.route("/api/recommendations", methods=["GET"])
async def get_recommendations():
    recs = await company_recommender.generate_recommendations()
    return jsonify(recs)

@app.route("/api/text_to_speech", methods=["POST"])
async def tts():
    data = await request.get_json()
    text = data.get("text", "")
    audio_data = await voice_processor.text_to_speech(text)
    return jsonify({"audio": audio_data})

@app.route("/api/voice_interaction", methods=["POST"])
async def voice_interaction():
    if not voice_processor:
        return jsonify({"error": "Voice processor not initialized"}), 500
    try:
        data = await request.get_json()
        text = data.get("text")
        step = data.get("step", "product")  # This is the current step
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        logger.info(f"Processing voice interaction for step: {step}, text: {text}")
        
        await flow_controller.store_answer(step, text)
        next_step = await flow_controller.get_next_step(step)
        
        logger.info(f"Next step after {step}: {next_step}")
        
        if next_step == "complete":
            logger.info("Flow complete, generating keywords and recommendations")
            logger.info(f"Current keywords before cleaning: {flow_controller.keywords}")
            cleaned_keywords = await flow_controller.clean_keywords()
            logger.info(f"Cleaned keywords: {cleaned_keywords}")
            recommendations = await company_recommender.generate_recommendations()
            logger.info(f"Generated recommendations: {recommendations}")
            return jsonify({
                "success": True,
                "completed": True,
                "text": "You're all set! Generating your results.",
                "keywords": cleaned_keywords,
                "recommendations": recommendations,
                "show_recommendations_tab": True
            })
        
        question = await flow_controller.get_question(next_step)
        audio = await voice_processor.text_to_speech(question)
        # Always include current keywords in the response
        current_keywords = await flow_controller.clean_keywords()
        
        return jsonify({
            "success": True,
            "text": question,
            "next_step": next_step,
            "audio": audio,
            "keywords": current_keywords  # Always include current keywords
        })
    except Exception as e:
        logger.error(f"Voice interaction failed: {str(e)}")
        return jsonify({"error": "Voice processing failed"}), 500

@app.route("/onboarding_data.csv")
async def download_onboarding_data():
    return await send_file("onboarding_data.csv", as_attachment=True)

@app.after_request
async def add_header(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
    
@app.route("/api/save_interaction", methods=["POST"])
async def save_interaction():
    """Save user interaction data."""
    try:
        data = await request.get_json()
        logger.info(f"Saving interaction data: {data}")
        
        # Here you would typically save this data to a database
        # For now, we'll just log it and return success
        
        return jsonify({
            "success": True,
            "message": "Interaction saved successfully"
        })
    except Exception as e:
        logger.error(f"Error saving interaction: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    
@app.route("/api/keywords", methods=["GET"])
async def get_keywords():
    """Get the current keywords."""
    try:
        # Initialize flow controller if not already done
        global flow_controller
        if flow_controller is None:
            flow_controller = FlowController()
        
        # Return the current keywords
        current_keywords = await flow_controller.clean_keywords()
        return jsonify({
            "success": True,
            "keywords": current_keywords
        })
    except Exception as e:
        logger.error(f"Error getting keywords: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "keywords": []
        }), 500
    
@app.route("/recommendations")
async def recommendations_page():
    return await render_template("recommendations.html")

@app.route("/test_ui.html")
async def test_ui():
    """Serve the test UI HTML file."""
    return await send_file("test_ui.html")

@app.route("/api/search_events", methods=["POST"])
async def search_events():
    """Search for events based on keywords and location."""
    try:
        data = await request.get_json()
        keywords = data.get("keywords", [])
        location = data.get("location", "")
        
        # Import the EventScraper
        from event_scraper import EventScraper
        
        # Initialize the scraper
        scraper = EventScraper()
        
        # Search for events
        events = await scraper.search_events(keywords, location)
        
        return jsonify(events)
    except Exception as e:
        logger.error(f"Error searching for events: {str(e)}")
        return jsonify([]), 500
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9001)
