from flask import Flask, request, jsonify, send_from_directory, session
import signal
import subprocess
import os
import platform
import uuid  # To generate unique session IDs for each user

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session encryption

# A dictionary to store process status by user_id
user_processes = {}

@app.after_request
def after_request(response):
    response.headers['Content-Type'] = 'text/html; charset=UTF-8'
    return response

@app.route('/')
def index():
    return open("index.html", encoding="utf-8").read()

@app.route('/run_ntrip', methods=['POST'])
def run_ntrip():
    global user_processes

    # Generate or retrieve user session ID
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())  # Unique user ID for the session
    
    user_id = session['user_id']

    # Get form data
    arquivo = request.form.get('arquivo', '').strip()
    user = request.form.get('user', '').strip()
    password = request.form.get('password', '').strip()
    host = request.form.get('host', '').strip()
    port = request.form.get('port', '').strip()
    mountpoint = request.form.get('mountpoint', '').strip()
    latitude = request.form.get('latitude', '').strip()
    longitude = request.form.get('longitude', '').strip()
    altitude = request.form.get('altitude', '').strip()
    ntimer = request.form.get('ntimer', '').strip()
    enviapos = request.form.get('enviapos', '').strip()

    if not user or not password:
        return jsonify({"error": "User and Password are required!"}), 400

    # Prepare the command to run the NtripClient.py
    if enviapos == 'N':
        command = [
            "python3", "NtripClient.py",
            "--user=" + user,
            "--password=" + password,
            "--maxtime=" + ntimer,
            host, port, mountpoint,
            "-f", os.path.join("/home/zero/pythonserver/files/", arquivo + ".rtcm")
        ]
    elif enviapos == 'S':
        command = [
            "python3", "NtripClient.py",
            "--user=" + user,
            "--password=" + password,
            "--latitude=" + latitude,
            "--longitude=" + longitude,
            "--height=" + altitude,
            "--maxtime=" + ntimer,
            host, port, mountpoint,
            "-f", os.path.join("/home/zero/pythonserver/files/", arquivo + ".rtcm")
        ]
    
    try:
        # Start the process
        if platform.system() == "Windows":
            process = subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            process = subprocess.Popen(command, preexec_fn=os.setsid)

        # Update the status for this user
        user_processes[user_id] = {"running": True, "message": "NTRIP Client is running..."}

        return jsonify({"message": "NTRIP Client Iniciado!"}), 200

    except Exception as e:
        return jsonify({"error": f"Error starting NTRIP Client: {str(e)}"}), 500

@app.route('/check_status', methods=['GET'])
def check_status():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "No active session found."}), 400

    # Get the process status for the current user
    process_status = user_processes.get(user_id, {"running": False, "message": "No process running."})

    # Check if the process is still running (only if it's marked as running)
    if process_status["running"]:
        try:
            if process_status["process"].poll() is None:  # Process is still running
                process_status["message"] = "NTRIP Client is still running..."
            else:  # Process has stopped
                user_processes[user_id]["running"] = False
                user_processes[user_id]["message"] = "NTRIP Client has stopped."
        except Exception as e:
            user_processes[user_id]["running"] = False
            user_processes[user_id]["message"] = f"Error checking process: {str(e)}"

    return jsonify(process_status)

@app.route('/translate_rinex', methods=['POST'])
def translate_rinex():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "No active session found."}), 400

    arquivo = request.form.get('arquivo')

    command = [
        "python3", "openRTK.py",
        "--input=" + arquivo,
        "--output=" + arquivo + "_obs",
        "--nav=" + arquivo + "_nav",
        "--gnav=" + arquivo + "_gnav",
        "--qnav=" + arquivo + "_qnav",
    ]

    try:
        # Start the process
        if platform.system() == "Windows":
            process = subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            process = subprocess.Popen(command, preexec_fn=os.setsid)

        # Update the status for this user
        user_processes[user_id] = {"running": True, "message": "Translation is running..."}

        return jsonify({"message": "Tradução feita"}), 200

    except Exception as e:
        return jsonify({"error": f"Error starting translation: {str(e)}"}), 500

@app.route('/files/<path:filename>')
def download_file(filename):
    documents_folder = '/home/zero/pythonserver/files'
    return send_from_directory(documents_folder, filename, as_attachment=True)

@app.route('/delete_file', methods=['POST'])
def delete_file():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "No active session found."}), 400

    data = request.get_json()
    filename = data.get('file').strip()

    if not filename:
        return jsonify({"error": "File name is required!"}), 400

    file_path = os.path.join('/home/zero/pythonserver/files/' + filename)

    try:
        if os.path.exists(file_path + ".rtcm"):
            os.remove(file_path + ".rtcm")
            if os.path.exists(file_path + "_nav.nav"):
                os.remove(file_path + "_nav.nav")
            if os.path.exists(file_path + "_obs.25o"):
                os.remove(file_path + "_obs.25o")
            if os.path.exists(file_path + "_gnav.25g"):
                os.remove(file_path + "_gnav.25g")
            if os.path.exists(file_path + "_qnav.25q"):
                os.remove(file_path + "_qnav.25q")
            return jsonify({"message": f"File {filename} deleted successfully!"}), 200
        else:
            return jsonify({"error": "File not found!"}), 404

    except Exception as e:
        return jsonify({"error": f"Error deleting file: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
