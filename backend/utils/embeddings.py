import google.generativeai as genai

# Configure Gemini API key
genai.configure(api_key="YOUR_API_KEY")

def get_text_embedding(text: str) -> list:
    """
    Get embedding for a given text using Gemini API
    """
    response = genai.embed_content(
        model="models/embedding-001",  # correct embedding model
        content=text
    )
    return response["embedding"]