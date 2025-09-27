#!/usr/bin/env python3
"""
Test script to verify environment variables are loading correctly
"""
import os
from dotenv import load_dotenv

def test_env_vars():
    print("=== Environment Variables Test ===")
    
    # Load .env file
    load_dotenv()
    
    # Test all required variables
    required_vars = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "DB_NAME": os.getenv("DB_NAME"),
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_PORT": os.getenv("DB_PORT")
    }
    
    print("\nEnvironment Variables Status:")
    print("-" * 50)
    
    all_good = True
    for var_name, var_value in required_vars.items():
        if var_value:
            if "KEY" in var_name or "PASSWORD" in var_name:
                # Mask sensitive values
                display_value = var_value[:10] + "..." if len(var_value) > 10 else "***"
            else:
                display_value = var_value
            print(f"✅ {var_name}: {display_value}")
        else:
            print(f"❌ {var_name}: NOT SET")
            all_good = False
    
    print("-" * 50)
    if all_good:
        print("🎉 All environment variables are properly set!")
        return True
    else:
        print("⚠️  Some environment variables are missing!")
        return False

if __name__ == "__main__":
    test_env_vars()
