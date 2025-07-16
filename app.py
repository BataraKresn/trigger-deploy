from flask import Flask, request, Response, send_from_directory, jsonify, url_for, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime, timedelta
from dotenv import load_dotenv
import subprocess
import os
import time
import psutil
import socket
import json
import traceback

# # # # # # # # # # # # # # # # # #
# # 🔐 Konfigurasi & Inisialisasi #
# # # # # # # # # # # # # # # # # #
load_dotenv()
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

TOKEN = os.getenv("DEPLOY_TOKEN", "SATindonesia2025")
LOG_DIR = "trigger-logs"
SERVERS_FILE = "static/servers.json"
os.makedirs(LOG_DIR, exist_ok=True)

# # # # # # # # # # # # # # # # # #
# # 🧹 clean_old_logs(days=7)    #
# # # # # # # # # # # # # # # # # #
def clean_old_logs(days=7):
    now = datetime.now()
    for filename in os.listdir(LOG_DIR):
        path = os.path.join(LOG_DIR, filename)
        if os.path.isfile(path):
            file_time = datetime.fromtimestamp(os.path.getmtime(path))
            if now - file_time > timedelta(days=days):
                os.remove(path)

# # # # # # # # # # # # # # # # # # # # # # #
# # 🧪 is_process_running(log_file_path)    #
# # # # # # # # # # # # # # # # # # # # # # #
def is_process_running(log_file_path):
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and log_file_path in ' '.join(cmdline):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

# # # # # # # # # # # # # # # # # # # 
# # 🔎 is_valid_server(identifier) #
# # # # # # # # # # # # # # # # # # #
def is_valid_server(identifier, return_details=False):
    try:
        with open(SERVERS_FILE, "r") as f:
            servers = json.load(f)

        for server in servers:
            if server.get("ip") == identifier:
                return server if return_details else True

        return None if return_details else False

    except Exception as e:
        print(f"Error loading servers.json: {e}")
        return None if return_details else False

@app.route('/')
def home():
    return render_template("home.html")


@app.route("/deploy-servers")
def deploy_servers():
    return render_template("deploy_servers.html")


@app.route('/servers', methods=['GET'])
def get_servers():
    try:
        with open(SERVERS_FILE, "r") as f:
            servers = json.load(f)
        return jsonify(servers)
    except Exception as e:
        return jsonify({"error": f"Failed to load servers.json: {str(e)}"}), 500


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/trigger', methods=['GET', 'POST'])
def trigger_deploy():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        token = data.get("token")
        server = data.get("server")
    else:
        token = request.args.get("token")
        server = request.args.get("server")

    if token != TOKEN:
        return jsonify({"error": "Invalid token", "status": 403}), 403

    clean_old_logs()

    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    log_filename = f"trigger-{timestamp}.log"
    log_path = os.path.join(LOG_DIR, log_filename)

     # Tulis awal log
    with open(log_path, "a") as log:
        log.write(f"[{datetime.now()}] 🚀 Deploy trigger received. Server: {server or 'default'}\n")

    if server is not None:
        server = server.strip()
        if server == "":
            server = None
        elif not is_valid_server(server):
            with open(log_path, "a") as log:
                log.write(f"[{datetime.now()}] ❌ Invalid server IP or alias: {server}\n")
            return jsonify({"error": "Invalid server IP or alias", "status": 400}), 400

    try:
        with open(log_path, "a") as log:
            log.write(f"[{datetime.now()}] ✅ Spawning deploy-wrapper.sh process...\n")

        if server:
            subprocess.Popen(["./deploy-wrapper.sh", log_path, server],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        else:
            subprocess.Popen(["./deploy-wrapper.sh", log_path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

        with open(log_path, "a") as log:
            log.write(f"[{datetime.now()}] 🔄 Process started, streaming from log file: {log_filename}\n")

        view_url = url_for('get_log_file', filename=log_filename, _external=True).replace("http://", "https://")
        stream_url = url_for('stream_log', file=log_filename, _external=True).replace("http://", "https://")

        # Respon log stream URL
        return jsonify({
            "status": "success",
            "log_file": log_filename,
            "view_log_url": view_url,
            "stream_log_url": stream_url
        }), 200
    except Exception as e:
        with open(log_path, "a") as log:
            log.write(f"[{datetime.now()}] ❌ Deploy error: {str(e)}\n")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/ping", methods=["POST"])
def ping_server():
    data = request.get_json()
    server_id = data.get("server")
    if not server_id:
        return jsonify({"status": "error", "message": "Missing server ID"}), 400

    # ✅ Gunakan path absolut
    SERVERS_FILE = os.path.join(app.root_path, "static", "servers.json")

    try:
        with open(SERVERS_FILE) as f:
            servers = json.load(f)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to load servers.json: {str(e)}"}), 500

    match = next((s for s in servers if s["ip"] == server_id or s.get("alias") == server_id), None)
    if not match:
        return jsonify({"status": "error", "message": "Server not found"}), 404

    ip = match["ip"]
    user = match.get("user")
    if not user:
        return jsonify({"status": "error", "message": "Missing user in servers.json"}), 400

    try:
        subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", f"{user}@{ip}", "exit"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return jsonify({"status": "ok"})
    except subprocess.CalledProcessError:
        return jsonify({"status": "unreachable"}), 503


@app.route('/logs', methods=['GET'])
def list_logs():
    logs = sorted(os.listdir(LOG_DIR), reverse=True)
    return jsonify(logs)


@app.route('/log-content', methods=['GET'])
def log_content():
    filename = request.args.get("file")
    if not filename:
        return "Missing file param", 400
    path = os.path.join(LOG_DIR, filename)
    if not os.path.exists(path):
        return "File not found", 404
    with open(path, "r") as f:
        return f.read()


@app.route('/stream-log', methods=['GET'])
def stream_log():
    filename = request.args.get("file")
    if not filename:
        return "❌ No log file specified", 400

    full_path = os.path.join(LOG_DIR, filename)
    if not os.path.isfile(full_path):
        return "❌ Log file not found", 404

    def generate():
        with open(full_path, 'r') as f:
            f.seek(0)  # Mulai dari awal log, bukan akhir
            while True:
                line = f.readline()
                if not line:
                    # Cek apakah proses deploy-wrapper sudah selesai
                    if not is_process_running(full_path):
                        yield "data: ✅ Deploy complete.\n\n"
                        break
                    time.sleep(1)
                    continue
                yield f"data: {line.strip()}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/logs/<path:filename>', methods=['GET'])
def get_log_file(filename):
    if not filename.endswith('.log'):
        return "❌ Invalid file type", 403
    return send_from_directory(LOG_DIR, filename)


@app.route('/health', methods=['GET'])
def health():
    target = request.args.get("target") or "google.co.id"
    result = {"target": target, "resolve": None, "ping": None}

    try:
        ip = socket.gethostbyname(target)
        result["resolve"] = f"{target} resolved to {ip}"
    except Exception as e:
        result["resolve"] = f"❌ DNS resolve failed: {str(e)}"

    try:
        param = '-n' if os.name == 'nt' else '-c'
        ping_cmd = ["ping", param, "5", target]
        ping_result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=5)
        result["ping"] = ping_result.stdout if ping_result.returncode == 0 else f"❌ Ping failed: {ping_result.stderr}"
    except Exception as e:
        result["ping"] = f"❌ Ping error: {str(e)}"

    return jsonify(result)
