from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import base64
from PIL import Image
import io
import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import openai

# Load environment variables first
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Scribble Quest Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="Scribble_quest"), name="static")

# Initialize LangChain OpenAI for question generation
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Initialize OpenAI client for vision
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class DrawingRequest(BaseModel):
    image: str
    challenge: str
    level: int
    session_id: str = "default"

def process_image(image_data_url):
    """Convert base64 image to PIL Image and analyze it"""
    try:
        # Remove the data URL prefix
        image_data = image_data_url.split(',')[1]
        
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_data)
        
        # Open as PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Basic analysis - count non-white pixels (drawing strokes)
        pixels = list(image.getdata())
        drawing_pixels = sum(1 for pixel in pixels if sum(pixel[:3]) < 750)  # Not white
        
        return {
            "size": image.size,
            "drawing_density": drawing_pixels / len(pixels),
            "has_drawing": drawing_pixels > 100
        }
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        return {"error": str(e)}

@app.get("/")
async def serve_game():
    """Serve the main game HTML file"""
    return FileResponse("Scribble_quest/index.html")

@app.get("/api/generate-questions")
async def generate_questions():
    """Generate object-based drawing challenges using LangChain"""
    try:
        response = llm.invoke("""Generate 5 simple object drawing challenges for kids. Focus only on concrete objects that can be drawn and recognized:

Examples:
- Draw a cat
- Draw a house
- Draw a car
- Draw a tree
- Draw a flower
- Draw a bird
- Draw a fish
- Draw a sun

Requirements:
- Start with "Draw a" or "Draw an"
- Use simple, concrete objects only (animals, vehicles, buildings, nature items)
- No abstract concepts or emotions
- Keep them very simple
- End with exclamation mark

Generate 5 object-based challenges:""")
        
        # Split response into individual questions
        questions = []
        for line in response.content.split('\n'):
            line = line.strip()
            # Remove numbering and bullets
            line = line.lstrip('123456789.- ')
            
            if line.lower().startswith('draw') and len(line) > 8:
                if not line.endswith('!'):
                    line += '!'
                questions.append(line)
        
        return {"questions": questions}
        
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        # Fallback questions if LangChain fails
        return {
            "questions": [
                "Draw a cat!",
                "Draw a house!",
                "Draw a car!",
                "Draw a tree!",
                "Draw a flower!"
            ]
        }

@app.post("/api/analyze-drawing")
async def analyze_drawing(request: DrawingRequest):
    logger.info(f"Received drawing for challenge: {request.challenge}")
    
    # First do basic image check
    image_analysis = process_image(request.image)
    
    if "error" in image_analysis:
        return {
            "title": "Error!",
            "message": "Could not process your drawing. Try again!",
            "points": 0,
            "success": False
        }
    
    logger.info(f"Image analysis: {image_analysis}")
    
    # Check if there's actually a drawing
    has_drawing = image_analysis.get("has_drawing", False)
    
    if not has_drawing:
        return {
            "title": "No Drawing!",
            "message": "I don't see any drawing. Try drawing something!",
            "points": 0,
            "success": False
        }
    
    # Extract the object from the challenge text
    challenge_text = request.challenge.lower().strip()
    logger.info(f"Original challenge: {request.challenge}")
    
    # Parse different challenge formats
    challenge_object = ""
    if "draw a " in challenge_text:
        challenge_object = challenge_text.split("draw a ")[1].replace("!", "").strip()
    elif "draw an " in challenge_text:
        challenge_object = challenge_text.split("draw an ")[1].replace("!", "").strip()
    elif challenge_text.startswith("draw "):
        challenge_object = challenge_text[5:].replace("!", "").strip()
    else:
        # Fallback - remove common words
        challenge_object = challenge_text.replace("draw", "").replace("something", "").replace("!", "").strip()
    
    logger.info(f"Extracted challenge object: '{challenge_object}'")
    
    # If we couldn't extract a clear object, use the full challenge
    if not challenge_object or len(challenge_object) < 2:
        challenge_object = request.challenge
    
    # Call OpenAI Vision API
    try:
        # Clean up base64 image data
        base64_image = request.image
        if ',' in base64_image:
            base64_image = base64_image.split(',')[1]
        
        logger.info(f"Sending image to OpenAI Vision API for object: {challenge_object}")
        
        # Create a specific prompt for drawing validation
        prompt = f"""
        You are helping judge a drawing game for kids. Look at this drawing carefully.
        
        The child was asked to draw: "{challenge_object}"
        
        Please analyze:
        1. What do you see in this drawing?
        2. Does it reasonably match what they were asked to draw?
        3. Remember this is a child's drawing - be encouraging but honest.
        
        Respond in this exact format:
        MATCH: YES or NO
        DESCRIPTION: [what you see]
        MESSAGE: [encouraging message for the child]
        
        Be generous with simple drawings but honest about completely unrelated drawings.
        """
        
        # Make API call to OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300,
            temperature=0.3  # Lower temperature for more consistent responses
        )
        
        # Parse the AI response
        ai_response = response.choices[0].message.content.strip()
        logger.info(f"OpenAI response: {ai_response}")
        
        # Extract match result
        is_match = False
        description = "I can see your drawing!"
        message = "Great effort on your drawing!"
        
        # Parse the structured response
        lines = ai_response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('MATCH:'):
                match_text = line.replace('MATCH:', '').strip().upper()
                is_match = 'YES' in match_text
            elif line.startswith('DESCRIPTION:'):
                description = line.replace('DESCRIPTION:', '').strip()
            elif line.startswith('MESSAGE:'):
                message = line.replace('MESSAGE:', '').strip()
        
        # Generate game response based on match result
        if is_match:
            response_data = {
                "title": "Perfect!",
                "message": f"{description} {message}",
                "points": 100,
                "success": True
            }
            
            # Generate DALL-E image for successful drawings
            try:
                logger.info(f"Generating DALL-E image for: {description}")
                dalle_prompt = f"A beautiful, professional digital artwork inspired by a child's drawing. The child drew a {challenge_object} and it looks like: {description}. Transform this into a magical, colorful masterpiece while keeping the child's creative vision. Fantasy art style, vibrant colors, whimsical and joyful."
                
                dalle_response = openai_client.images.generate(
                    model="dall-e-3",
                    prompt=dalle_prompt,
                    size="1024x1024",
                    n=1
                )
                
                image_url = dalle_response.data[0].url
                response_data["reward_image"] = image_url
                response_data["message"] += " Check out your masterpiece!"
                logger.info(f"DALL-E image generated successfully: {image_url}")
                
            except Exception as e:
                logger.error(f"DALL-E image generation failed: {e}")
                # Continue without image if DALL-E fails
                
            return response_data
        else:
            return {
                "title": "Try Again!",
                "message": f"{description} {message} You were asked to draw: {challenge_object}",
                "points": 25,
                "success": False
            }
            
    except Exception as e:
        logger.error(f"OpenAI Vision API failed: {e}")
        
        # Fallback response when API fails
        return {
            "title": "Something Magical!",
            "message": f"I can see you drew something creative! The AI is taking a break, but your art is still wonderful!",
            "points": 50,
            "success": True
        }
        

@app.get("/api/health")
async def health_check():
    """Check backend health including API configuration"""
    api_key_configured = bool(os.getenv("OPENAI_API_KEY"))
    
    return {
        "status": "healthy", 
        "message": "Scribble Quest backend is running!",
        "api_key_configured": api_key_configured,
        "openai_model": "gpt-4o"
    }

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)