import os
import sqlite3
import google.generativeai as genai
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)

# --- THIS IS THE FINAL UPDATED LINE ---
# This is the most permissive CORS configuration to solve the issue
CORS(app, resources={r"/*": {"origins": "*"}})

try:
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    print(f"Could not configure Gemini API: {e}")
    model = None

DB_NAME = "projects.db"

def get_data_from_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects")
    projects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return projects

@app.route('/analyze', methods=['GET'])
def analyze_performance():
    if not model:
        return jsonify({"error": "Gemini API key is missing or invalid."}), 500
    
    try:
        all_projects_data = get_data_from_db()
        data_summary = []
        for p in all_projects_data[:20]:
             data_summary.append(
                 f"Project {p['request_id']}: Customer '{p['customer_name']}', Assembler '{p['assembler_1']}'"
             )
        data_text = "\n".join(data_summary)

        prompt = f"""
        You are a business process analyst for a panel manufacturing company.
        Based on the following project data, identify 2 potential bottlenecks or areas for improvement in the assembly process.
        For each point, provide a brief, actionable suggestion.
        Present your analysis in simple Persian.

        Here is the data summary:
        {data_text}
        """
        
        response = model.generate_content(prompt)
        return jsonify({ "analysis_html": response.text.replace('\n', '<br>') })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    return "API is running."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
