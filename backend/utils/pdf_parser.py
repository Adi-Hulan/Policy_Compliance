import PyPDF2
import os
import tempfile
import requests
from urllib.parse import urlparse

def is_supabase_path(path):
    """Check if the path is a Supabase storage path or URL"""
    if path.startswith('uploads/'):
        return True
    
    parsed = urlparse(path)
    return parsed.scheme in ['http', 'https'] and 'supabase' in parsed.netloc

def download_from_supabase(file_path):
    """Download a file from Supabase storage and save it to a temporary file"""
    # Convert storage path to URL if needed
    if file_path.startswith('uploads/'):
        # Get Supabase URL from environment
        from utils.supabase_client import supabase
        
        # Get a temporary URL for the file
        try:
            # If path is just the storage path, get the URL
            result = supabase.storage.from_("documents").get_public_url(file_path)
            file_url = result['publicUrl']
        except Exception as e:
            print(f"Error getting public URL: {e}")
            raise
    else:
        # If it's already a URL, use it directly
        file_url = file_path
    
    # Download the file
    response = requests.get(file_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download file: {response.status_code}")
    
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_file.write(response.content)
    temp_file.close()
    
    return temp_file.name

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file, handling both local and Supabase files"""
    temp_file = None
    
    try:
        # Check if it's a Supabase path and download if needed
        if is_supabase_path(file_path):
            print(f"Downloading file from Supabase: {file_path}")
            file_path = download_from_supabase(file_path)
            temp_file = file_path
        
        # Extract text from the PDF
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
        
        return text
    
    finally:
        # Clean up temporary file if it was created
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
