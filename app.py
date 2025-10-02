from flask import Flask, request, render_template, jsonify
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ANSI escape codes for terminal colors
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

@app.before_request
def log_ip():
    ip = request.remote_addr
    print(f"{Colors['bright_purple']}[VISITOR] Connected IP: {Colors['bright_yellow']}{ip}{RESET}")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No selected file"}), 400

    # Log "sending..."
    print(f"{Colors['cyan']}[SENDING...] {Colors['white']}Uploading file: {Colors['yellow']}{file.filename}{RESET}")

    # Save file
    file.save(os.path.join(UPLOAD_FOLDER, file.filename))

    # Log "sent!"
    print(f"{Colors['bright_green']}[SENT!] {Colors['yellow']}{file.filename}{RESET}")

    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
