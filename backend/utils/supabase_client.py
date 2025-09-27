import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

# Get environment variables
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# Debug: Print what we're getting
print(f"DEBUG: SUPABASE_URL = {url}")
print(f"DEBUG: SUPABASE_SERVICE_ROLE_KEY = {key[:20] + '...' if key else 'None'}")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables")

# Create Supabase client
supabase: Client = create_client(url, key)