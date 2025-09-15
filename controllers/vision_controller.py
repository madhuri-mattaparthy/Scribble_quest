# app/controllers/vision_controller.py
import base64
import logging
from typing import Dict, Any
import openai
import os
from PIL import Image
import io

logger = logging.getLogger(__name__)

class OpenAIVisionController:
    """Simple OpenAI Vision API controller with DALL-E integration"""
    
    def __init__(self):
        # Load environment variables first
        from dotenv import load_dotenv
        load_dotenv()
        
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Set API key and create client
        openai.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
        
    def analyze_image(self, base64_image: str, challenge_object: str) -> Dict[str, Any]:
        """
        Analyze drawing using OpenAI Vision API
        
        Args:
            base64_image: Base64 encoded image from canvas
            challenge_object: What the user was supposed to draw
            
        Returns:
            Dict with analysis results
        """
        try:
            # Clean up base64 image data
            if ',' in base64_image:
                base64_image = base64_image.split(',')[1]
                
            # Create the prompt
            prompt = f"""
            Look at this drawing. The user was asked to draw a {challenge_object}.
            
            Please respond with:
            1. What you see in the drawing
            2. Whether it matches the challenge (YES/NO)
            3. A fun, encouraging message for the user
            
            Keep it simple and positive for a drawing game.
            """
            
            # Make API call
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
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
                max_tokens=300
            )
            
            # Parse response
            ai_response = response.choices[0].message.content
            
            # Simple parsing to extract if it's a match
            is_match = "YES" in ai_response.upper()
            
            return {
                "success": True,
                "ai_response": ai_response,
                "is_match": is_match,
                "challenge_object": challenge_object,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"OpenAI Vision API failed: {e}")
            return {
                "success": False,
                "ai_response": None,
                "is_match": False,
                "challenge_object": challenge_object,
                "error": str(e)
            }
    
    def generate_reward_image(self, user_drawing_description: str, challenge_object: str) -> Dict[str, Any]:
        """Generate reward image based on description of user's drawing"""
        try:
            # Create detailed prompt based on what the AI saw in the drawing
            prompt = f"A beautiful, professional digital artwork inspired by a child's drawing. The child drew a {challenge_object} and it looks like: {user_drawing_description}. Transform this into a magical, colorful masterpiece while keeping the child's creative vision. Fantasy art style, vibrant colors, whimsical and joyful."
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                n=1
            )
            
            return {
                "success": True,
                "image_url": response.data[0].url
            }
            
        except Exception as e:
            logger.error(f"DALL-E failed: {e}")
            return {
                "success": False,
                "image_url": None
            }
    
    def generate_game_response(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert AI analysis into game response with optional image generation"""
        
        if not analysis_result["success"]:
            return {
                "title": "Oops!",
                "message": "I couldn't analyze your drawing right now. Try again!",
                "points": 0,
                "success": False
            }
        
        ai_response = analysis_result["ai_response"]
        is_match = analysis_result["is_match"]
        
        if is_match:
            # Generate reward image based on what AI saw in the drawing
            reward = self.generate_reward_image(ai_response, analysis_result["challenge_object"])
            
            response = {
                "title": "Amazing!",
                "message": ai_response,
                "points": 100,
                "success": True
            }
            
            # Add image if generation worked
            if reward["success"]:
                response["reward_image"] = reward["image_url"]
                response["message"] += " Check out your masterpiece!"
            else:
                logger.warning("Image generation failed, continuing without image")
                
            return response
        else:
            return {
                "title": "Try Again!",
                "message": ai_response,
                "points": 25,
                "success": False
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Check if OpenAI API is configured properly"""
        api_key_set = bool(os.getenv("OPENAI_API_KEY"))
        
        return {
            "api_key_configured": api_key_set,
            "service": "OpenAI Vision API + DALL-E",
            "model": "gpt-4o + dall-e-3"
        }

# Singleton instance
openai_vision_controller = OpenAIVisionController()