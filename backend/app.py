from flask import Flask, request, jsonify
from orchestrator.controller import Orchestrator

app = Flask(__name__)
orchestrator = Orchestrator()

@app.route('/process_query', methods=['POST'])
def process_query():
    data = request.json
    response = orchestrator.route(data)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)