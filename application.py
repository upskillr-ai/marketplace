from flask import Flask, jsonify, request, abort
import json

app = Flask(__name__)

# Load JSON file
with open('marketplace.json', 'r') as f:
    data = json.load(f)

@app.route('/marketplace/info', methods=['GET'])
def get_info():
    # Get the topic parameter from the query string
    topic = request.args.get('topic')
    
    # If no topic is provided or the provided topic is not in the data, return a 400 status code
    if not topic or topic not in data:
        abort(400, description="Invalid topic"), 400
    
    # Return the data for the given topic
    return jsonify(data[topic]), 200

if __name__ == "__main__":
    app.run(debug=True)
