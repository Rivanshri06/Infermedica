from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import json
import ast
import torch
from transformers import BartForConditionalGeneration, BartTokenizer

# Initialize Flask app
app = Flask(__name__)

model_bart = BartForConditionalGeneration.from_pretrained('fine-tuned-bart')
tokenizer_bart = BartTokenizer.from_pretrained('fine-tuned-bart')

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')  # Update with your MongoDB connection string
db = client['myDb']
collection = db['patients']

# Function to generate MongoDB query from natural language
def generate_query_finetuned(question):
    inputs = tokenizer_bart(question, return_tensors='pt', max_length=512, truncation=True, padding="max_length")
    outputs = model_bart.generate(**inputs, max_length=512, num_beams=4, early_stopping=True)
    query = tokenizer_bart.decode(outputs[0], skip_special_tokens=True)
    print(query)
    return query

# Function to execute the generated MongoDB query
def execute_query(query_string, patient_id=None):
    try:
        if query_string.startswith("db.patients.aggregate"):
            query_start = query_string.find('[')
            query_end = query_string.rfind(']') + 1
            pipeline_str = query_string[query_start:query_end]
            
            try:
                pipeline = json.loads(pipeline_str)
            except json.JSONDecodeError as e:
                print(f"An error occurred while parsing the aggregation pipeline: {e}")
                return None

            if patient_id:
                pipeline.insert(0, {"$match": {"id": patient_id}})
            
            results = list(collection.aggregate(pipeline))
        
        elif query_string.startswith("db.patients.find"):
            query_start = query_string.find('(') + 1
            query_end = query_string.rfind(')')
            query_parts = query_string[query_start:query_end].rsplit('},', 1)

            filter_str = query_parts[0] + '}'
            projection_str = query_parts[1].strip() if len(query_parts) > 1 else None
            
            try:
                filter_query = json.loads(filter_str)
                projection_query = json.loads(projection_str) if projection_str else None
            except json.JSONDecodeError as e:
                print(f"An error occurred while parsing the find query: {e}")
                return None

            if patient_id:
                filter_query['id'] = patient_id

            results = list(collection.find(filter_query, projection_query))
        
        else:
            print("Unsupported query type.")
            return None
        
        print(results)
        return results
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
@app.route('/')
def index():
    return render_template('home.html')  # Render a template for the homepage

@app.route('/ask', methods=['POST'])
def ask():
    try:
        question = request.form.get('question')
        query = generate_query_finetuned(question)
        data = execute_query(query)
        if data is not None:
            # Convert MongoDB documents to JSON-serializable format
            json_data = []
            for record in data:
                # Convert ObjectId to string if necessary and handle other BSON types
                record['_id'] = str(record['_id']) if '_id' in record else None
                json_data.append(record)
            return jsonify({'response': json_data})
        else:
            return jsonify({'response': 'No data found or an error occurred.'})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
