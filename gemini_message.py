import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MODEL = "gemini-2.5-flash-lite"


def generate_kudos_message(
    receiver_name: str = None,
    giver_name: str = None,
    kudos_message: str = None,
    kudos_count: int = None
) -> str:
    """
    Generate an encouraging, positive, and witty message for a kudos receiver
    using Google Gemini.
    
    Args:
        receiver_name: Name of the person receiving kudos (optional)
        giver_name: Name of the person giving kudos (optional)
        kudos_message: The message accompanying the kudos (optional)
        kudos_count: Total kudos count for the receiver (optional)
    
    Returns:
        A generated encouraging message, or a fallback message if generation fails
    """
    try:
        if not GEMINI_API_KEY:
            print("Warning: GEMINI_API_KEY not set, using fallback message")
            return get_fallback_message()
        
        # Build context for the AI
        context_parts = []
        if giver_name:
            context_parts.append(f"from {giver_name}")
        if receiver_name:
            context_parts.append(f"to {receiver_name}")
        if kudos_message:
            context_parts.append(f"with the message: '{kudos_message}'")
        if kudos_count:
            context_parts.append(f"bringing their total to {kudos_count} kudos")
        
        context = " ".join(context_parts) if context_parts else "for great work"
        
        # Create the prompt
        prompt = f"""Generate a short, encouraging, positive, and witty message (1-2 sentences max) 
to celebrate someone receiving kudos {context}. 

The message should be:
- Uplifting and celebratory
- Professional but friendly
- Include an appropriate emoji
- Be concise (under 100 characters if possible)
- Witty or clever when appropriate

Just return the message itself, nothing else."""

        # Initialize the client
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Generate the message
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        
        if response and response.text:
            return response.text.strip()
        else:
            return get_fallback_message()
            
    except Exception as e:
        print(f"Error generating Gemini message: {e}")
        return get_fallback_message()


def get_fallback_message() -> str:
    """Return a fallback message if Gemini generation fails."""
    import random
    
    fallback_messages = [
        "Keep up the amazing work! 🌟",
        "You're crushing it! 🚀",
        "Excellence recognized! 👏",
        "Your awesomeness is showing! ✨",
        "Making magic happen! 🎯",
        "Stellar performance! ⭐",
        "You're on fire! 🔥",
        "Absolutely brilliant! 💎",
        "Shining bright! 💫",
        "Legendary work! 🏆"
    ]
    
    return random.choice(fallback_messages)


# # For testing
# if __name__ == "__main__":
#     # Test the function
#     message = generate_kudos_message(
#         receiver_name="Alice",
#         giver_name="Bob",
#         kudos_message="Great presentation!",
#         kudos_count=15
#     )
#     print(f"Generated message: {message}")
