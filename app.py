import os
import time
import pymysql
from flask import Flask, request, jsonify, render_template_string
from google.cloud import storage

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

# GCP Cloud Storage Browser UI Template
GCP_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GCP Cloud Storage 瀏覽器</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Noto+Sans+TC:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --gcp-blue: #4285f4;
            --gcp-red: #ea4335;
            --gcp-yellow: #fbbc05;
            --gcp-green: #34a853;
            --text-color: #f1f5f9;
            --text-muted: #94a3b8;
            --border-color: rgba(255, 255, 255, 0.1);
            --success-color: #34a853;
            --warning-color: #fbbc05;
            --danger-color: #ea4335;
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
            background-image: radial-gradient(circle at top right, rgba(66, 133, 244, 0.15), transparent),
                              radial-gradient(circle at bottom left, rgba(52, 168, 83, 0.08), transparent);
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
            background: linear-gradient(135deg, var(--gcp-blue), var(--gcp-green));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .gcp-logo {
            display: inline-flex;
            gap: 3px;
        }
        .gcp-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        .dot-blue { background-color: var(--gcp-blue); }
        .dot-red { background-color: var(--gcp-red); }
        .dot-yellow { background-color: var(--gcp-yellow); }
        .dot-green { background-color: var(--gcp-green); }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-size: 14px;
            color: var(--text-muted);
        }
        
        .input-group {
            display: flex;
            gap: 10px;
        }
        
        input {
            flex: 1;
            padding: 12px;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-color);
            font-size: 16px;
            transition: all 0.3s;
        }
        
        input:focus {
            outline: none;
            border-color: var(--gcp-blue);
            box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.2);
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            background-color: var(--gcp-blue);
            color: white;
        }
        
        .btn:hover {
            background-color: #2b75eb;
            transform: translateY(-1px);
        }
        
        .divider {
            height: 1px;
            background: var(--border-color);
            margin: 25px 0;
        }
        
        .section-title {
            font-size: 18px;
            font-weight: 600;
            margin-top: 0;
            margin-bottom: 15px;
            color: var(--text-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .badge {
            font-size: 12px;
            padding: 4px 8px;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-muted);
        }
        
        .bucket-list {
            list-style: none;
            padding: 0;
            margin: 0;
            max-height: 350px;
            overflow-y: auto;
        }
        
        .bucket-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px;
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-bottom: 10px;
            transition: all 0.2s;
        }
        
        .bucket-item:hover {
            background: rgba(15, 23, 42, 0.6);
            border-color: rgba(66, 133, 244, 0.3);
            transform: translateX(2px);
        }
        
        .bucket-icon {
            font-size: 20px;
        }
        
        .bucket-name {
            font-weight: 600;
            font-size: 15px;
            word-break: break-all;
        }
        
        .loader {
            display: none;
            text-align: center;
            padding: 30px;
            color: var(--text-muted);
        }
        
        .loader-spinner {
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top: 3px solid var(--gcp-blue);
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            line-height: 1.5;
            display: none;
        }
        
        .alert-danger {
            background: rgba(234, 67, 53, 0.1);
            border: 1px solid rgba(234, 67, 53, 0.2);
            color: #fca5a5;
        }
        
        .alert-info {
            background: rgba(66, 133, 244, 0.1);
            border: 1px solid rgba(66, 133, 244, 0.2);
            color: #93c5fd;
        }
        
        .empty-state {
            text-align: center;
            color: var(--text-muted);
            padding: 30px;
            font-style: italic;
        }
        
        .nav-links {
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
            font-size: 14px;
        }
        
        .nav-links a {
            color: var(--gcp-blue);
            text-decoration: none;
            transition: color 0.2s;
        }
        
        .nav-links a:hover {
            color: #2b75eb;
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>
            <span class="gcp-logo">
                <span class="gcp-dot dot-blue"></span>
                <span class="gcp-dot dot-red"></span>
                <span class="gcp-dot dot-yellow"></span>
                <span class="gcp-dot dot-green"></span>
            </span>
            GCS Bucket 瀏覽器
        </h1>
        
        <div id="errorAlert" class="alert alert-danger"></div>
        <div id="infoAlert" class="alert alert-info"></div>

        <!-- Project ID Form -->
        <div class="form-group">
            <label for="projectId">GCP Project ID</label>
            <div class="input-group">
                <input type="text" id="projectId" placeholder="輸入專案 ID，例如：my-gcp-project-123" required>
                <button class="btn" onclick="fetchBuckets()">查詢 Buckets</button>
            </div>
        </div>
        
        <div class="divider"></div>
        
        <!-- Buckets List -->
        <div class="section-title">
            <span>儲存貯體 (Buckets) 列表</span>
            <span id="bucketCount" class="badge">0 個</span>
        </div>
        
        <div id="loader" class="loader">
            <div class="loader-spinner"></div>
            <span>連線 GCP 查詢中，請稍候...</span>
        </div>
        
        <ul id="bucketList" class="bucket-list">
            <li class="empty-state">請在上方輸入 Project ID 並點擊查詢</li>
        </ul>
        
        <div class="divider"></div>
        
        <div class="nav-links">
            <a href="/user">👤 用戶管理系統</a>
            <a href="/">🏠 回首頁</a>
        </div>
    </div>

    <script>
        // Check if there is a saved project ID in localStorage
        document.getElementById('projectId').value = localStorage.getItem('saved_gcp_project_id') || '';

        async function fetchBuckets() {
            const projectId = document.getElementById('projectId').value.trim();
            const errorAlert = document.getElementById('errorAlert');
            const infoAlert = document.getElementById('infoAlert');
            const loader = document.getElementById('loader');
            const bucketList = document.getElementById('bucketList');
            const bucketCount = document.getElementById('bucketCount');
            
            errorAlert.style.display = 'none';
            infoAlert.style.display = 'none';
            
            if (!projectId) {
                errorAlert.textContent = '請輸入 Project ID！';
                errorAlert.style.display = 'block';
                return;
            }
            
            // Save project ID
            localStorage.setItem('saved_gcp_project_id', projectId);
            
            // Show loader, clear list
            loader.style.display = 'block';
            bucketList.innerHTML = '';
            bucketCount.textContent = '0 個';
            
            try {
                const response = await fetch(`/gcp/buckets?project_id=${encodeURIComponent(projectId)}`);
                const data = await response.json();
                
                loader.style.display = 'none';
                
                if (!response.ok) {
                    throw new Error(data.message || '查詢失敗');
                }
                
                const buckets = data.buckets || [];
                bucketCount.textContent = `${buckets.length} 個`;
                
                if (buckets.length === 0) {
                    bucketList.innerHTML = '<li class="empty-state">該專案內沒有任何 Cloud Storage Bucket</li>';
                    return;
                }
                
                buckets.forEach(bucketName => {
                    const li = document.createElement('li');
                    li.className = 'bucket-item';
                    li.innerHTML = `
                        <span class="bucket-icon">🪣</span>
                        <span class="bucket-name">${bucketName}</span>
                    `;
                    bucketList.appendChild(li);
                });
                
            } catch (error) {
                loader.style.display = 'none';
                errorAlert.innerHTML = `
                    <strong>查詢出錯：</strong> ${error.message}
                    <br><br>
                    <small>💡 提示：請確認：<br>
                    1. 專案 ID 是否正確。<br>
                    2. 本地開發時，是否已執行 <code>gcloud auth application-default login</code>。<br>
                    3. GCP 容器（若是跑在 GCP VM 上）是否綁定了具有 Storage Viewer 權限的服務帳號 (Service Account)。</small>
                `;
                errorAlert.style.display = 'block';
                bucketList.innerHTML = '<li class="empty-state" style="color: var(--danger-color)">查詢發生錯誤</li>';
            }
        }
    </script>
</body>
</html>
"""

# GCP Storage Buckets Route
@app.route('/gcp')
def gcp_page():
    return render_template_string(GCP_TEMPLATE)

@app.route('/gcp/buckets')
def gcp_buckets():
    project_id = request.args.get('project_id')
    if not project_id:
        return jsonify({"status": "error", "message": "Missing project_id parameter"}), 400
    
    try:
        # Initialize Google Cloud Storage client
        # Implicitly uses Application Default Credentials (ADC)
        storage_client = storage.Client(project=project_id)
        buckets = list(storage_client.list_buckets())
        bucket_names = [bucket.name for bucket in buckets]
        return jsonify({"status": "success", "buckets": bucket_names})
    except Exception as e:
        # Return friendly error message
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


