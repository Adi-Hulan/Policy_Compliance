from flask import jsonify
from supabase_client import supabase
from flask import Blueprint

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/messages", methods=["GET"])
def get_messages():
    try:
        print("Fetching messages from Supabase")
        response = supabase.table("messages").select("*").execute()
        return jsonify(response.data)  # Access data directly
    except Exception as e:
        print("Error fetching messages")
        # If Supabase fails, catch the exception
        return jsonify({"error": str(e)}), 500
