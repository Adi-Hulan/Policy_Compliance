from flask import Flask, jsonify
from utils.supabase_client import supabase

app = Flask(__name__)

@app.route("/")
def index():
    return "Flask backend running! Go to /test to see Supabase data."

@app.route("/test")
def test():
    data = supabase.table("test_table").select("*").execute()
    return jsonify(data.data)

if __name__ == '__main__':
    app.run(debug=True)