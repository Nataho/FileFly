from flask import Flask, request, render_template, jsonify, abort, redirect, url_for
from werkzeug.utils import secure_filename
import time
import os, sys
import json
import subprocess
import logging

log = logging.getLogger('werkzeug')


# ==================== Helper: Persistent Path ====================
def resource_path(filename):
    """Return absolute path to resource (works for PyInstaller and normal runs)."""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)  # Executable directory
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, filename)

# ---------------- VLC Setup (KEPT AS-IS) ----------------
try:
    import vlc
    VLC = vlc.Instance()
    Audio = VLC.media_player_new()
    vlc_available = True
except Exception as e:
    print("[WARNING] VLC not available, sound effects disabled.")
    VLC = None
    Audio = None
    vlc_available = False

# ---------------- ANSI Colors (KEPT) ----------------
Colors = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "purple": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bright_black": "\033[90m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_purple": "\033[95m",
    "bright_cyan": "\033[96m",
    "bright_white": "\033[97m"
}
RESET = "\033[0m"

version = "0.0.6"
link = "https://github.com/nataho/FileFly"

# ---------------- Paths ----------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# dynamic_dir = os.path.join(BASE_DIR, "dynamic")
dynamic_dir = resource_path("dynamic")
os.makedirs(dynamic_dir, exist_ok=True)

PAIRS_FILE = os.path.join(dynamic_dir, "pairs.json")      # approved pairs
PENDING_FILE = os.path.join(dynamic_dir, "pending.json")  # pending requests
LOG_FILE = os.path.join(dynamic_dir, "logs.json")        # plain logs (max 100)
UPLOAD_FOLDER = resource_path("uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- Sound helpers (KEPT) ----------------
sounds_dir = os.path.join(BASE_DIR, "static", "sounds")

def loadSound(sound):
    if not vlc_available:
        return None
    sound_path = os.path.join(sounds_dir, sound)
    return VLC.media_new(sound_path)

sounds = {}
if vlc_available:
    sounds = {
        "open": loadSound("Home.wav"),
        "sent": loadSound("Controller.wav"),
        "request" : loadSound("Bing.wav")
    }

def doSFX(sound):
    if not vlc_available or sound is None:
        return
    try:
        Audio.set_media(sound)
        Audio.play()
    except Exception:
        pass

# ---------------- Simple logging (plain json + colored terminal) ----------------
def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def add_log(entry):
    if entry.get("action") == "VISITOR":
        return
    
    logs = load_json(LOG_FILE, [])
    logs.append(entry)
    logs = logs[-100:]  # keep last 100
    save_json(LOG_FILE, logs)

def log_event(ip, action, details="", mac=None, sender=None):
    if action == "VISITOR":
        return  # skip visitors entirely

    # if mac is missing, try to reuse from pairs.json
    if not mac:
        pairs = load_pairs()
        if ip in pairs:
            mac = pairs[ip].get("mac") or "None"
        else:
            mac = get_mac_from_arp(ip) or "None"

    entry = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ip": ip,
        "mac": mac,
        "sender": sender or "noname",
        "action": action,
        "details": details
    }
    add_log(entry)
    term_log(f"[{action}] from {ip} mac={mac} sender={entry['sender']} {details}", "bright_green")



def term_log(msg, color="white"):
    print(f"{Colors.get(color, Colors['white'])}{msg}{RESET}")

# ---------------- MAC lookup helper ----------------
def get_mac_from_arp(ip):
    """
    Try to get MAC address from arp table (returns None if not found).
    Works on many Linux distros using `arp -n`. If unreachable, returns None.
    """
    try:
        p = subprocess.run(["arp", "-n", ip], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=2)
        out = p.stdout.strip()
        for line in out.splitlines():
            if ip in line:
                parts = line.split()
                # typical: IP HWtype Flags MAC ...
                # many formats; attempt to find a mac-like token
                for token in parts:
                    if ":" in token and len(token) >= 11:
                        return token
    except Exception:
        return None
    return None

# ---------------- Pairing helpers ----------------
def load_pairs():
    return load_json(PAIRS_FILE, {})

def save_pairs(pairs):
    save_json(PAIRS_FILE, pairs)

def load_pending():
    return load_json(PENDING_FILE, {})

def save_pending(pending):
    save_json(PENDING_FILE, pending)

def is_ip_approved(ip):
    pairs = load_pairs()
    return ip in pairs and pairs[ip].get("status") == "approved"

def is_ip_pending(ip):
    pend = load_pending()
    return ip in pend

# ---------------- Startup banner (kept) ----------------
def start():
    term_log("========== FileFly ==========", "cyan")
    term_log(version, "bright_blue")
    term_log(link, "bright_yellow")
    print()
    term_log("to connect to this server: connect to the same network and open the server IP", "bright_blue")
    term_log("it should be the second network address shown (if you have multiple).", "bright_green")
    print()
    term_log("links:", "yellow")
    term_log("hosted link")
    term_log("http://localhost:5000","bright_yellow")
    term_log("admin")
    term_log("http://localhost:5000/admin","bright_yellow")
    term_log("=================================================================", "cyan")
    print()
    if vlc_available and "open" in sounds:
        # time.sleep(1)
        doSFX(sounds["open"])
        time.sleep(1)

start()

# ---------------- Flask app ----------------
app = Flask(__name__)

# @app.before_request
# def log_visitor():
    # ip = request.remote_addr
#     # terminal colored
    # term_log(f"[VISITOR] Connected IP: {ip}", "bright_purple")
#     # store plain log
#     # add_log({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "ip": ip, "action": "VISITOR", "details": ""})

@app.before_request
def mute_logs():
    ip = request.remote_addr
    if request.path.startswith("/admin/"):
        log.setLevel(logging.ERROR)   # silence all admin API
    else:
        log.setLevel(logging.INFO)
        term_log(f"[VISITOR] Connected IP: {ip}", "bright_yellow")


# Serve client page
@app.route("/")
def index():
    return render_template("client.html")

# Admin page (LOCAL ONLY)
@app.route("/admin")
def admin_panel():
    if request.remote_addr not in ("127.0.0.1", "::1"):
        abort(403)
    # pass approved pairs, pending requests, and logs (plain) to template
    pairs = load_pairs()
    pending = load_pending()
    logs = load_json(LOG_FILE, [])
    return render_template("admin.html", pairs=pairs, pending=pending, logs=logs)

# API: status check - tells client whether this IP is approved/denied/pending
@app.route("/status", methods=["GET"])
def status():
    ip = request.remote_addr
    pairs = load_pairs()
    pending = load_pending()
    if ip in pairs and pairs[ip].get("status") == "approved":
        return jsonify({"paired": True, "status": "approved"})
    if ip in pending:
        return jsonify({"paired": False, "status": "pending"})
    return jsonify({"paired": False, "status": "none"})

# API: pair request (client calls this). We'll try to get MAC automatically.
@app.route("/pair", methods=["POST"])
def pair_request():
    ip = request.remote_addr
    data = {}
    try:
        data = request.get_json(silent=True) or {}
    except Exception:
        data = {}
    sender = (data.get("sender") or "").strip() or None

    # if already approved, return success immediately
    pairs = load_pairs()
    if ip in pairs and pairs[ip].get("status") == "approved":
        term_log(f"[PAIR] {ip} already approved", "bright_green")
        return jsonify({"success": True, "message": "Already paired"}), 200

    # check pending: if already requested, just return pending
    pending = load_pending()
    if ip in pending:
        term_log(f"[PAIR] {ip} already pending", "yellow")
        return jsonify({"success": False, "pending": True, "message": "Already pending"}), 200

    # try get mac
    mac = get_mac_from_arp(ip)
    # store pending request (keep sender if provided)
    pending[ip] = {"mac": mac, "sender": sender, "time": time.strftime("%Y-%m-%d %H:%M:%S")}
    save_pending(pending)

    # terminal + log
    term_log(f"[{ip}] added to pair request (mac={mac})", "bright_yellow")
    add_log({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "ip": ip, "mac": mac , "sender" : sender, "action": "PAIR_REQUEST", "details": f"request pair"})

    if vlc_available and "request" in sounds:
        doSFX(sounds["request"])

    return jsonify({"success": False, "pending": True, "message": "Pair request created; waiting admin approval"}), 200

# Admin API: list pending (local-only)
@app.route("/admin/pending", methods=["GET"])
def admin_pending():
    if request.remote_addr not in ("127.0.0.1", "::1"):
        abort(403)
    pending = load_pending()
    return jsonify(pending)

# Admin API: approve
@app.route("/admin/approve", methods=["POST"])
def admin_approve():
    if request.remote_addr not in ("127.0.0.1", "::1"):
        abort(403)
    data = request.form or request.get_json(silent=True) or {}
    ip = data.get("ip")
    if not ip:
        return jsonify({"success": False, "error": "missing ip"}), 400

    pending = load_pending()
    pairs = load_pairs()

    if ip in pending:
        entry = pending.pop(ip)
        pairs[ip] = {"mac": entry.get("mac"), "status": "approved", "time": time.strftime("%Y-%m-%d %H:%M:%S"), "sender": entry.get("sender")}
        save_pairs(pairs)
        save_pending(pending)

        term_log(f"[{ip}] pair approved", "bright_green")
        add_log({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "ip": ip, "mac" : pairs[ip].get('mac'), "sender" : pairs[ip].get('sender'), "action": "PAIR_APPROVED", "details": f"approve pair"})

        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "error": "not found in pending"}), 404

# Admin API: deny
@app.route("/admin/deny", methods=["POST"])
def admin_deny():
    if request.remote_addr not in ("127.0.0.1", "::1"):
        abort(403)
    data = request.form or request.get_json(silent=True) or {}
    ip = data.get("ip")
    if not ip:
        return jsonify({"success": False, "error": "missing ip"}), 400

    pending = load_pending()
    if ip in pending:
        entry = pending.pop(ip)
        save_pending(pending)
        term_log(f"[{ip}] pair denied", "red")
        add_log({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "ip": ip, "action": "PAIR_DENIED", "details": f"mac={entry.get('mac')} sender={entry.get('sender') or '—'}"})
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "error": "not found in pending"}), 404

# Upload route: checks approval
@app.route("/upload", methods=["POST"])
def upload():
    ip = request.remote_addr
    pairs = load_pairs()
    if ip not in pairs or pairs[ip].get("status") != "approved":
        term_log(f"[{ip}] denied upload attempt (not approved)", "red")
        log_event(ip, "UPLOAD_DENIED", "not approved")
        return jsonify({"success": False, "error": "Not paired or not approved"}), 403

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400

    file = request.files["file"]
    sender = request.form.get("sender", "noname") or "noname"

    if file.filename == "":
        return jsonify({"success": False, "error": "No selected file"}), 400

    safe_filename = secure_filename(file.filename)
    sender_folder = os.path.join(UPLOAD_FOLDER, secure_filename(sender))
    os.makedirs(sender_folder, exist_ok=True)
    filepath = os.path.join(sender_folder, safe_filename)
    file.save(filepath)

    term_log(f"[RECEIVED!] {safe_filename} by {sender} from {ip}", "bright_green")

    # use log_event so MAC is included
    log_event(ip, "UPLOAD", f"{safe_filename}", sender=sender)

    if vlc_available and "sent" in sounds:
        doSFX(sounds["sent"])

    return jsonify({"success": True, "filename": safe_filename})


# Admin API: get logs (plain)
@app.route("/admin/logs", methods=["GET"])
def admin_logs_api():
    if request.remote_addr not in ("127.0.0.1", "::1"):
        abort(403)

    logs = load_json(LOG_FILE, [])
    # take last 100, newest first
    logs = list(reversed(logs[-100:]))  

    # skip VISITOR logs
    filtered = [log for log in logs if log.get("action") != "VISITOR"]

    return jsonify([
        {
            "time": log.get("time"),
            "ip": log.get("ip"),
            "mac": log.get("mac", "None"),
            "sender": log.get("sender", "noname"),
            "action": log.get("action"),
            "details": log.get("details", "")
        }
        for log in filtered
    ])

@app.route("/admin/logs", methods=["POST"])
def admin_logs_post():
    if request.remote_addr not in ("127.0.0.1", "::1"):
        abort(403)

    # Get JSON data from the request
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400

    # Ensure required fields exist
    required_fields = ["action", "ip", "sender"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # Add timestamp if not provided
    from datetime import datetime
    log_entry = {
        "time": data.get("time", datetime.utcnow().isoformat()),
        "ip": data["ip"],
        "mac": data.get("mac", "None"),
        "sender": data["sender"],
        "action": data["action"],
        "details": data.get("details", "")
    }

    # Load existing logs
    logs = load_json(LOG_FILE, [])
    logs.append(log_entry)

    # Save back to the file
    with open(LOG_FILE, "w") as f:
        import json
        json.dump(logs, f, indent=2)

    return jsonify({"status": "success", "log": log_entry}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
