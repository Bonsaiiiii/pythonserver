from flask import Flask, request, jsonify, session
import signal
import subprocess
import os
import platform
import threading
import uuid
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Important for session security

# Process tracking dictionary
processes = {}
process_lock = threading.Lock()

@app.after_request
def after_request(response):
    response.headers['Content-Type'] = 'text/html; charset=UTF-8'
    return response

@app.route('/')
def index():
    # Generate session token if doesn't exist
    if 'token' not in session:
        session['token'] = str(uuid.uuid4())
    return open("index.html", encoding="utf-8").read()

@app.route('/get_token')
def get_token():
    return jsonify({"token": session.get('token', '')})

@app.route('/run_ntrip', methods=['POST'])
def run_ntrip():
    token = session.get('token')
    if not token:
        return jsonify({"error": "Session token missing"}), 400

    global process

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

    # Stop any existing process for this token
    with process_lock:
        if token in processes:
            old_proc = processes[token]
            if old_proc.poll() is None:  # Process still running
                if platform.system() == "Windows":
                    old_proc.terminate()
                else:
                    os.killpg(os.getpgid(old_proc.pid), signal.SIGTERM)
            del processes[token]

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
        if platform.system() == "Windows":
            new_proc = subprocess.Popen(
                command,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            new_proc = subprocess.Popen(
                command,
                preexec_fn=os.setsid
            )
        
        # Store new process
        with process_lock:
            processes[token] = new_proc

        return jsonify({"message": "NTRIP Client Started!"}), 200

    except Exception as e:
        return jsonify({"error": f"Error starting NTRIP Client: {str(e)}"}), 500

@app.route('/ntrip_status')
def ntrip_status():
    token = session.get('token')
    if not token:
        return jsonify({"error": "Session token missing"}), 400

    with process_lock:
        proc = processes.get(token)
    
    status = "stopped"
    if proc:
        if proc.poll() is None:  # None means still running
            status = "running"
        else:
            # Clean up finished process
            with process_lock:
                if token in processes:
                    del processes[token]
    
    return jsonify({"status": status})

@app.route('/translate_rinex', methods=['POST'])
def translate_rinex():
    global process

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
        if platform.system() == "Windows":
            process = subprocess.Popen(
                command,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            process = subprocess.Popen(
                command,
                preexec_fn=os.setsid
            )

        return jsonify({"message": "Tradução feita"}), 200

    except Exception as e:
        return jsonify({"error": f"Error starting NTRIP Client: {str(e)}"}), 500
    

from flask import send_from_directory

@app.route('/files/<path:filename>')
def download_file(filename):
    documents_folder = '/home/zero/pythonserver/files'
    print("Requested file:", filename)
    return send_from_directory(documents_folder, filename, as_attachment=True)

@app.route('/delete_file', methods=['POST'])
def delete_file():
    data = request.get_json()
    filename = data.get('file').strip()
    print(filename)

    if not filename:
        return jsonify({"error": "File name is required!"}), 400

    file_path = os.path.join('/home/zero/pythonserver/files/' + filename)

    try:
        if os.path.exists(file_path + ".rtcm"):
            print("rtcm apagado")
            os.remove(file_path + ".rtcm")
            if os.path.exists(file_path + "_nav.nav"):
                print("nav apagado")
                os.remove(file_path + "_nav.nav")
            if os.path.exists(file_path + "_obs.25o"):
                print("obs apagado")
                os.remove(file_path + "_obs.25o")
            if os.path.exists(file_path + "_gnav.25g"):
                print("gnav apagado")
                os.remove(file_path + "_gnav.25g")
            if os.path.exists(file_path + "_qnav.25q"):
                print("qnav apagado")
                os.remove(file_path + "_qnav.25q")
            return jsonify({"message": f"File {filename} deleted successfully!"}), 200
        else:
            return jsonify({"error": "File not found!"}), 404

    except Exception as e:
        return jsonify({"error": f"Error deleting file: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)







<!-- Status indicator -->
<div id="statusIndicator" style="margin: 20px;">
    Status: <span id="statusText">Checking...</span>
    <div style="display:inline-block; width:20px; height:20px; border-radius:50%; background:gray; margin-left:10px;" id="statusLight"></div>
</div>

<script>
// Generate or retrieve session token
let token = sessionStorage.getItem('ntripToken');
if (!token) {
    token = crypto.randomUUID();
    sessionStorage.setItem('ntripToken', token);
}

// Function to check status
async function checkStatus() {
    try {
        // Update token in session
        await fetch('/get_token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({token: token})
        });
        
        const response = await fetch('/ntrip_status');
        const data = await response.json();
        
        // Update UI
        document.getElementById('statusText').textContent = 
            data.status === 'running' ? 'RUNNING' : 'STOPPED';
        
        document.getElementById('statusLight').style.background = 
            data.status === 'running' ? 'green' : 'red';
            
    } catch (error) {
        console.error('Status check failed:', error);
    }
}

// Add token to all forms
document.querySelectorAll('form').forEach(form => {
    const tokenInput = document.createElement('input');
    tokenInput.type = 'hidden';
    tokenInput.name = 'token';
    tokenInput.value = token;
    form.appendChild(tokenInput);
});

// Initial status check
checkStatus();

// Check every 5 seconds
setInterval(checkStatus, 5000);
</script>