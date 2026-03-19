from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import pymysql
import json

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='0000',
        database='flowtrace',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def create_table_if_not_exists():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS api_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                method VARCHAR(10) NOT NULL,
                url VARCHAR(500) NOT NULL,
                status_code INT NOT NULL,
                request_body TEXT,
                response_body TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(sql)
        connection.commit()
        connection.close()
        print("Table 'api_requests' is ready")
    except Exception as e:
        print(f"Error creating table: {e}")

@app.route('/api/request', methods=['POST'])
def save_api_request():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        required_fields = ['method', 'url', 'status_code']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        method = data.get('method')
        url = data.get('url')
        status_code = data.get('status_code')
        request_body = data.get('request_body', '')
        response_body = data.get('response_body', '')
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO api_requests (method, url, status_code, request_body, response_body)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (method, url, status_code, request_body, response_body))
        
        connection.commit()
        connection.close()
        
        return jsonify({"message": "saved"}), 201
        
    except pymysql.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/requests', methods=['GET'])
def get_api_requests():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            SELECT id, method, url, status_code, request_body, response_body, 
                   DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at
            FROM api_requests
            ORDER BY created_at DESC
            """
            cursor.execute(sql)
            results = cursor.fetchall()
        
        connection.close()
        
        return jsonify(results), 200
        
    except pymysql.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    create_table_if_not_exists()
    print("Starting Flask server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)