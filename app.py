import os
import redis
import socket
import json
import time
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

# Kết nối Redis Server (Biến môi trường REDIS_HOST do Cloud truyền vào)
redis_host = os.environ.get('REDIS_HOST', '127.0.0.1')
r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

# Khởi tạo dữ liệu gốc (Giả lập Database)
def init_db():
    if not r.exists("db:classes"):
        data = {
            "IT4409": {"name": "Kiến trúc hệ thống lớn", "slots": 50},
            "IT4490": {"name": "Chuyên đề DevOps", "slots": 100}
        }
        r.set("db:classes", json.dumps(data))

@app.route('/')
def index():
    init_db()
    start_time = time.time()
    pod_name = socket.gethostname() 
    
    # --- LOGIC CACHING ---
    # Ưu tiên lấy từ Cache (Nhanh)
    cached_data = r.get("cache:view")
    
    if cached_data:
        # Cache HIT
        classes = json.loads(cached_data)
        source = "CACHE (REDIS) - FAST"
    else:
        # Cache MISS -> Gọi DB (Chậm)
        time.sleep(1.5) # Giả lập DB chậm
        raw_db = r.get("db:classes")
        classes_dict = json.loads(raw_db)
        classes = [{"id": k, "name": v["name"], "slots": v["slots"]} for k, v in classes_dict.items()]
        
        # Lưu vào cache 30s
        r.set("cache:view", json.dumps(classes), ex=30)
        source = "DATABASE (SQL) - SLOW"

    duration = round((time.time() - start_time) * 1000, 2)
    return render_template('index.html', classes=classes, source=source, time=duration, pod=pod_name)

@app.route('/register', methods=['POST'])
def register():
    class_id = request.form.get('class_id')
    
    # Distributed Lock để tránh Race Condition giữa các Server
    with r.lock("lock:db_update", timeout=2):
        raw_db = r.get("db:classes")
        db_data = json.loads(raw_db)
        
        if db_data[class_id]['slots'] > 0:
            db_data[class_id]['slots'] -= 1
            r.set("db:classes", json.dumps(db_data)) # Cập nhật DB gốc
            r.delete("cache:view") # Xóa Cache để các server khác cập nhật lại
            return jsonify({"msg": "Đăng ký thành công!", "status": "ok"})
        else:
            return jsonify({"msg": "Hết chỗ!", "status": "fail"}), 400

@app.route('/clear-cache')
def clear_cache():
    r.delete("cache:view")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
