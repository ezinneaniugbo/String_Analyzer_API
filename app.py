# importing the necessary libaries
from flask import Flask, request, jsonify
import hashlib, re, os
from collections import Counter
from datetime import datetime, timezone

# App Initialization
app = Flask(__name__)
stored_strings = {}

# Creating a function for the string analysis
def analyze_string(raw_text):
    clean_text = raw_text.lower()
    is_palindrome = clean_text == clean_text[::-1]
    
    properties = {
        "length" : len(clean_text),
        "is_palindrome" : is_palindrome,
        "unique_characters" : len(set(clean_text)),
        "word_count" : len(raw_text.split()),
        "sha256_hash" : hashlib.sha256(clean_text.encode()).hexdigest(),
        "character_frequency_map" : dict(Counter(clean_text))
        }
    return properties

# Creating a POST & GET endpoint to filter all strings
@app.route('/strings', methods=['POST', 'GET'])
@app.route('/strings/', methods=['POST', 'GET'])
def create_string():
    # For POST
   if request.method == 'POST':
        data = request.get_json()
        if not data or 'value' not in data:
            return jsonify({"error": "Invalid body or missing 'value' field"}), 400

        value = data['value']
        if not isinstance(value, str):
            return jsonify({"error": "Invalid data type for 'value' (It must be a string)"}), 422
        if value in stored_strings:
            return jsonify({"error": "The string already exists in the system"}), 409

        properties = analyze_string(value)
        new_entry = {
            "id": properties["sha256_hash"],
            "value": value,
            "properties": properties,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        stored_strings[value] = new_entry
        return jsonify(new_entry), 201
   
   # For GET
   if request.method == 'GET':
        args = request.args
        filters_applied = {}
        filtered_data = list(stored_strings.values())

        try:
            if 'is_palindrome' in args:
                is_palindrome = args['is_palindrome'].lower() == 'true'
                filters_applied['is_palindrome'] = is_palindrome
                filtered_data = [s for s in filtered_data if s['properties']['is_palindrome'] == is_palindrome]

            if 'min_length' in args:
                min_len = int(args['min_length'])
                filters_applied['min_length'] = min_len
                filtered_data = [s for s in filtered_data if s['properties']['length'] >= min_len]

            if 'max_length' in args:
                max_len = int(args['max_length'])
                filters_applied['max_length'] = max_len
                filtered_data = [s for s in filtered_data if s['properties']['length'] <= max_len]

            if 'word_count' in args:
                wc = int(args['word_count'])
                filters_applied['word_count'] = wc
                filtered_data = [s for s in filtered_data if s['properties']['word_count'] == wc]

            if 'contains_character' in args:
                char = args['contains_character']
                filters_applied['contains_character'] = char
                filtered_data = [s for s in filtered_data if char.lower() in s['value'].lower()]

        except (ValueError, TypeError) as e:
            return jsonify({"error": f"Invalid query parameter value: {e}"}), 400

        response = {
            "data": filtered_data,
            "count": len(filtered_data),
            "filters_applied": filters_applied
        }
        return jsonify(response), 200



# Creating a GET endpoint 
@app.route('/strings/<string_value>', methods=['GET', 'DELETE'])
@app.route('/strings/<string_value>/', methods=['GET', 'DELETE'])
def fetch_string(string_value):
    
    if request.method == 'GET':
        if string_value not in stored_strings:
            return jsonify({"error": "The String does not exist in the system"}), 404
        return jsonify(stored_strings[string_value]), 200

    if request.method == 'DELETE':
        if string_value not in stored_strings:
            return jsonify({"error": "The String does not exist in the system"}), 404
        del stored_strings[string_value]
        return '', 204

# Creating a GET endpoint for natural language filtering
@app.route('/strings/filter-by-natural-language', methods=["GET"])
@app.route('/strings/filter-by-natural-language/', methods=['GET'])
def filter_by_NL():
    query = request.args.get("query", "").lower()
    if not query:
        return jsonify({"error": "Missing query"}), 400

    filters = {}
    if 'palindrome' in query or 'palindromic' in query:
        filters['is_palindrome'] = True

    if 'single word' in query:
        filters['word_count'] = 1

    if 'longer than' in query:
        try:
            num = int(re.findall(r'longer than (\d+)', query)[0])
            filters['min_length'] = num + 1
        except (IndexError, ValueError):
            return jsonify({"error": "Unable to parse length from query"}), 400

    if 'contain' in query or 'containing' in query:
        match = re.search(r'contain(?:ing)? (?:the letter )?"?([a-zA-Z0-9])"?', query)
        if match:
            filters['contains_character'] = match.group(1)

    if not filters:
        return jsonify({"error": "Unable to parse natural language query"}), 400

    filtered_data = list(stored_strings.values())
    if 'is_palindrome' in filters:
        filtered_data = [s for s in filtered_data if s['properties']['is_palindrome']]
    if 'word_count' in filters:
        filtered_data = [s for s in filtered_data if s['properties']['word_count'] == filters['word_count']]
    if 'min_length' in filters:
        filtered_data = [s for s in filtered_data if s['properties']['length'] >= filters['min_length']]
    if 'contains_character' in filters:
        char = filters['contains_character']
        filtered_data = [s for s in filtered_data if char in s['value']]

    response = {
        "data": filtered_data,
        "count": len(filtered_data),
        "interpreted_query": {
            "original": request.args.get('query', ''),
            "parsed_filters": filters
        }
    }
    return jsonify(response), 200


#To run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
