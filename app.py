from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import joblib
import json
import ast
import torch
from transformers import BartForConditionalGeneration, BartTokenizer, PegasusForConditionalGeneration, PegasusTokenizer

# Load models and tokenizers
model_bart = BartForConditionalGeneration.from_pretrained('fine-tuned-bart')
tokenizer_bart = BartTokenizer.from_pretrained('fine-tuned-bart')
model_pegasus = PegasusForConditionalGeneration.from_pretrained('pegasus_model')
tokenizer_pegasus = PegasusTokenizer.from_pretrained('pegasus_tokenizer')

app = Flask(__name__)

# MongoDB connection details
client = MongoClient('mongodb://localhost:27017/')
db = client['myDb']
collection = db['patients']

# Function to generate MongoDB query from natural language
def generate_query(question):
    inputs = tokenizer_bart(question, return_tensors='pt', max_length=512, truncation=True, padding="max_length")
    outputs = model_bart.generate(**inputs, max_length=512, num_beams=4, early_stopping=True)
    query = tokenizer_bart.decode(outputs[0], skip_special_tokens=True)
    return query

# Function to execute the generated MongoDB query
def execute_query(query_string):
    try:
        query_start = query_string.find('(') + 1
        query_end = query_string.rfind(')')
        query_parts = query_string[query_start:query_end].split('},')

        filter_query = ast.literal_eval(query_parts[0] + '}')
        projection_query = ast.literal_eval(query_parts[1].strip()) if len(query_parts) > 1 else None

        results = list(collection.find(filter_query, projection_query))
        return results
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Function to convert data into natural language using PEGASUS
def convert_to_natural_language(data):
    input_text = json.dumps(data)
    inputs = tokenizer_pegasus(input_text, return_tensors='pt', truncation=True, padding=True)
    summary_ids = model_pegasus.generate(inputs['input_ids'])
    output = tokenizer_pegasus.decode(summary_ids[0], skip_special_tokens=True)
    return output

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question')
    query = generate_query(question)
    data = execute_query(query)
    if data:
        natural_language_output = convert_to_natural_language(data)
        return jsonify({'response': natural_language_output})
    else:
        return jsonify({'response': 'No data found or an error occurred.'})

if __name__ == '__main__':
    app.run(debug=True)
