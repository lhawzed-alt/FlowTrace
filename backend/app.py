from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import pymysql
import json
import requests

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

@app.route('/api/replay/<int:id>', methods=['POST'])
def replay_api_request(id):
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            SELECT method, url, request_body
            FROM api_requests
            WHERE id = %s
            """
            cursor.execute(sql, (id,))
            result = cursor.fetchone()
        
        connection.close()
        
        if not result:
            return jsonify({"error": "Record not found"}), 404
        
        method = result['method']
        url = result['url']
        request_body = result['request_body']
        
        try:
            headers = {'Content-Type': 'application/json'} if request_body else {}
            data = None
            
            if request_body:
                try:
                    data = json.loads(request_body)
                except json.JSONDecodeError:
                    data = request_body
                    headers = {'Content-Type': 'text/plain'}
            
            full_url = url
            if url.startswith('/'):
                full_url = f"http://localhost:5000{url}"
            
            if method.upper() == 'GET':
                response = requests.get(full_url, params=data if isinstance(data, dict) else None)
            elif method.upper() == 'POST':
                response = requests.post(full_url, json=data if isinstance(data, dict) else data, headers=headers)
            elif method.upper() == 'PUT':
                response = requests.put(full_url, json=data if isinstance(data, dict) else data, headers=headers)
            elif method.upper() == 'DELETE':
                response = requests.delete(full_url, json=data if isinstance(data, dict) else data, headers=headers)
            else:
                return jsonify({"error": f"Unsupported method: {method}"}), 400
            
            return jsonify({
                "status_code": response.status_code,
                "response_body": response.text
            }), 200
            
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"Request failed: {str(e)}"}), 500
        
    except pymysql.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# 测试API端点 - 用于Replay功能测试
@app.route('/api/test', methods=['GET'])
def test_get_endpoint():
    return jsonify({
        "message": "GET request successful",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/api/test', methods=['POST'])
def test_post_endpoint():
    data = request.get_json()
    return jsonify({
        "message": "POST request successful",
        "received_data": data,
        "timestamp": datetime.now().isoformat()
    }), 201

@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify({
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
        ],
        "count": 3,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Name is required"}), 400
    
    new_user = {
        "id": 100,
        "name": data['name'],
        "email": data.get('email', f"{data['name'].lower()}@example.com")
    }
    
    return jsonify({
        "message": "User created successfully",
        "user": new_user,
        "timestamp": datetime.now().isoformat()
    }), 201

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    create_table_if_not_exists()
    print("Starting Flask server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)