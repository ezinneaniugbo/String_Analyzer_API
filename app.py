#importing the necessary libaries
from flask import Flask, request, jsonify
import hashlib
from collections import Counter
from datetime import datetime, timezone

#App Initialization
app = Flask(__name__)
stored_strings = {}

#Creating a function for the string analysis
def analyze_string(raw_text):
    clean_text = raw_text.strip().lower()

    is_palindrome = clean_text == clean_text[::-1]

    properties = {
        "length" : len(clean_text),
        "is_palindrome" : is_palindrome,
        "unique characters" : len(set(clean_text)),
        "word_count" : len(clean_text.split()),
        "sha256_hash" : hashlib.sha256(clean_text.encode()).hexdigest(),
        "character_frequency_map" : dict(Counter(clean_text))
        }
    return properties

#Creating a POST endpoint 
@app.route('/strings', methods=['POST'])
def create_string():
    data = request.get_json()
    if not data or "value" not in data:
        return jsonify({"error": "Invalid body or missing 'value' field"}), 400
    
    text_value = data["value"]
    if not isinstance(text_value, str):
        return jsonify({"error": "Invalid data type for 'value' (It must be a string)"}), 422
    
    if text_value in stored_strings:
        return jsonify({"error": "The string already exists in the system"}), 409
    
    properties = analyze_string(text_value)
    new_response = {
        "id": properties["sha256_hash"],
        "value": text_value,
        "properties": properties,
        "created_at": datetime.now().isoformat()
        }
    stored_strings[text_value] = new_response
    return jsonify(new_response), 201

#Creating a GET endpoint 
@app.route('/strings/<input_string>', methods=['GET'])
def fetch_string(input_string):
    if input_string not in stored_strings:
        return jsonify({"error": "The String does not exist in the system"}), 404
    
    return jsonify(stored_strings[input_string]), 200

#Creating a GET endpoint to get all strings with Filtering
@app.route('/strings', methods=['GET'])
def all_strings():

    is_palindrome = request.args.get('is_palindrome')
    min_length = request.args.get('min_length')
    max_length = request.args.get('max_length')
    word_count = request.args.get('word_count')
    contains_character = request.args.get('contains_character')

    try:
        if min_length:
            min_length = int(min_length)
        if max_length:
            max_length = int(max_length)
        if word_count:
            word_count = int(word_count)
        if is_palindrome:
            is_palindrome = is_palindrome.lower() == 'true'
    except ValueError:
        return jsonify({"error": "Invalid query parameter values or types"}), 400
    
    filtered = []
    for item in stored_strings.values():
        props = item["properties"]
        text = item["value"]

#Applying the filters
        if is_palindrome is not None and props["is_palindrome"] != is_palindrome:
            continue
        if min_length and props["length"] < min_length:
            continue
        if max_length and props["length"] > max_length:
            continue
        if word_count and props["word_count"] != word_count:
            continue
        if contains_character and contains_character.lower() not in text.lower():
            continue
        
        filtered.append(item)
        
    response = {
        "data": filtered,
        "count": len(filtered),
        "filters_applied": {
            "is_palindrome": is_palindrome,
            "min_length": min_length,
            "max_length": max_length,
            "word_count": word_count,
            "contains_character": contains_character
            }
            }
    return jsonify(response), 200


#To run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
