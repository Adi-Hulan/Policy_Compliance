from flask import Flask, request, jsonify
from orchestrator.controller import Orchestrator
import os

from db.connection import get_db

app = Flask(__name__)
orchestrator = Orchestrator()

@app.route('/process_query', methods=['POST'])
def process_query():
    data = request.json
    response = orchestrator.route(data)
    return jsonify(response)

def fileHandler():
    data = request.json

if __name__ == '__main__':
    app.run(debug=True)