import os
import time
import pymysql
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Database configuration
# When running locally: defaults to localhost and port 8625
# When running in docker container: gets values from docker-compose environment variables (mysql.cki101:3306)
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 8625))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'rootpassword')
DB_NAME = os.environ.get('DB_NAME', 'cki101_db')

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    print(f"Connecting to database at {DB_HOST}:{DB_PORT}...")
    # Retry a few times in case the MySQL service is still starting up
    for i in range(15):
        try:
            # We first connect without database name to ensure we can create it if not exists
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD
            )
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            conn.commit()
            conn.close()

            # Now connect to the database to create table
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        age INT NOT NULL
                    )
                """)
            conn.commit()
            conn.close()
            print("Database initialized successfully!")
            return True
        except Exception as e:
            print(f"Database connection failed, retrying ({i+1}/15)... Error: {e}")
            time.sleep(3)
    return False

# Initialize database on startup
# Note: If running inside container, MySQL might take some seconds to boot
init_db()

@app.route('/')
def index():
    return "我是功能一的文字"

# HTML Template for user management interface
USER_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>用戶管理系統</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Noto+Sans+TC:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --primary-color: #3b82f6;
            --primary-hover: #2563eb;
            --text-color: #f1f5f9;
            --text-muted: #94a3b8;
            --border-color: rgba(255, 255, 255, 0.1);
            --danger-color: #ef4444;
            --danger-hover: #dc2626;
            --success-color: #10b981;
        }
        
        body {
            font-family: 'Inter', 'Noto Sans TC', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            box-sizing: border-box;
            background-image: radial-gradient(circle at top right, rgba(59, 130, 246, 0.1), transparent),
                              radial-gradient(circle at bottom left, rgba(16, 185, 129, 0.05), transparent);
        }
        
        .container {
            width: 100%;
            max-width: 650px;
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }
        
        h1 {
            font-size: 28px;
            font-weight: 700;
            margin-top: 0;
            margin-bottom: 25px;
            text-align: center;
            background: linear-gradient(135deg, #3b82f6, #10b981);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-size: 14px;
            color: var(--text-muted);
        }
        
        input {
            width: 100%;
            padding: 12px;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-color);
            font-size: 16px;
            transition: all 0.3s;
            box-sizing: border-box;
        }
        
        input:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
        }
        
        .btn {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background-color: var(--primary-color);
            color: white;
        }
        
        .btn-primary:hover {
            background-color: var(--primary-hover);
            transform: translateY(-1px);
        }
        
        .divider {
            height: 1px;
            background: var(--border-color);
            margin: 30px 0;
        }
        
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .search-box input {
            flex: 1;
        }
        
        .user-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .user-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-bottom: 10px;
            transition: all 0.3s;
        }
        
        .user-item:hover {
            background: rgba(15, 23, 42, 0.6);
            border-color: rgba(59, 130, 246, 0.3);
        }
        
        .user-info {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        
        .user-name {
            font-weight: 600;
            font-size: 16px;
        }
        
        .user-age {
            font-size: 14px;
            color: var(--text-muted);
        }
        
        .btn-danger {
            background-color: transparent;
            border: 1px solid var(--danger-color);
            color: var(--danger-color);
            padding: 6px 12px;
            font-size: 14px;
            border-radius: 6px;
            width: auto;
        }
        
        .btn-danger:hover {
            background-color: var(--danger-color);
            color: white;
        }
        
        .empty-state {
            text-align: center;
            color: var(--text-muted);
            padding: 20px;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>👤 用戶管理系統 (DB: {{ host }}:{{ port }})</h1>
        
        <!-- Add User Form -->
        <form id="addUserForm" onsubmit="addUser(event)">
            <div class="form-group">
                <label for="name">姓名</label>
                <input type="text" id="name" required placeholder="例如：張小明">
            </div>
            <div class="form-group">
                <label for="age">年紀</label>
                <input type="number" id="age" required min="0" max="150" placeholder="例如：25">
            </div>
            <button type="submit" class="btn btn-primary">新增用戶</button>
        </form>
        
        <div class="divider"></div>
        
        <!-- Search and List Section -->
        <div class="search-box">
            <input type="text" id="searchName" placeholder="輸入姓名即時搜尋..." oninput="loadUsers()">
        </div>
        
        <ul id="userList" class="user-list">
            <!-- Dynamic Users -->
        </ul>
    </div>

    <script>
        async function loadUsers() {
            const searchQuery = document.getElementById('searchName').value;
            const url = searchQuery ? `/user?name=${encodeURIComponent(searchQuery)}` : '/user';
            
            try {
                const response = await fetch(url, {
                    headers: {
                        'Accept': 'application/json'
                    }
                });
                const users = await response.json();
                
                const userList = document.getElementById('userList');
                userList.innerHTML = '';
                
                if (users.length === 0) {
                    userList.innerHTML = '<li class="empty-state">目前無符合條件的用戶資料</li>';
                    return;
                }
                
                users.forEach(user => {
                    const li = document.createElement('li');
                    li.className = 'user-item';
                    li.innerHTML = `
                        <div class="user-info">
                            <span class="user-name">${user.name}</span>
                            <span class="user-age">${user.age} 歲</span>
                        </div>
                        <button class="btn btn-danger" onclick="deleteUser(${user.id})">刪除</button>
                    `;
                    userList.appendChild(li);
                });
            } catch (error) {
                console.error('載入用戶失敗:', error);
            }
        }

        async function addUser(event) {
            event.preventDefault();
            const name = document.getElementById('name').value;
            const age = parseInt(document.getElementById('age').value);
            
            try {
                const response = await fetch('/user', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name, age })
                });
                
                if (response.ok) {
                    document.getElementById('addUserForm').reset();
                    loadUsers();
                } else {
                    const err = await response.json();
                    alert('新增失敗: ' + err.message);
                }
            } catch (error) {
                console.error('新增用戶失敗:', error);
            }
        }

        async function deleteUser(id) {
            if (!confirm('確定要刪除此用戶嗎？')) return;
            
            try {
                const response = await fetch(`/user/${id}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    loadUsers();
                } else {
                    const err = await response.json();
                    alert('刪除失敗: ' + err.message);
                }
            } catch (error) {
                console.error('刪除用戶失敗:', error);
            }
        }

        // Initial Load
        loadUsers();
    </script>
</body>
</html>
"""

# User API Endpoint
@app.route('/user', methods=['GET', 'POST'])
def manage_users():
    if request.method == 'GET':
        # If request is from browser address bar (asking for HTML), return UI
        if 'text/html' in request.headers.get('Accept', ''):
            return render_template_string(USER_TEMPLATE, host=DB_HOST, port=DB_PORT)
        
        # Otherwise, process as API call (Query)
        name_filter = request.args.get('name')
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                if name_filter:
                    sql = "SELECT id, name, age FROM users WHERE name LIKE %s"
                    cursor.execute(sql, (f"%{name_filter}%",))
                else:
                    sql = "SELECT id, name, age FROM users"
                    cursor.execute(sql)
                users = cursor.fetchall()
            conn.close()
            return jsonify(users)
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    elif request.method == 'POST':
        # Create (新增)
        data = request.get_json(silent=True) or request.form
        name = data.get('name')
        age = data.get('age')

        if not name or age is None:
            return jsonify({"status": "error", "message": "Missing name or age"}), 400

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                sql = "INSERT INTO users (name, age) VALUES (%s, %s)"
                cursor.execute(sql, (name, int(age)))
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "message": "User added successfully"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Delete (刪除)
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "DELETE FROM users WHERE id = %s"
            cursor.execute(sql, (user_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "User deleted successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

