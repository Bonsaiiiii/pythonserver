from flask import Flask, request, jsonify
import signal
import subprocess
import os
import platform
import psutil  # Add this import

app = Flask(__name__)

process = None
is_running = False  # Global status flag

@app.after_request
def after_request(response):
    response.headers['Content-Type'] = 'text/html; charset=UTF-8'
    return response

@app.route('/')
def index():
    return open("index.html", encoding="utf-8").read()

@app.route('/run_ntrip', methods=['POST'])
def run_ntrip():
    global process, is_running
    
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
            process = subprocess.Popen(
                command,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            process = subprocess.Popen(
                command,
                preexec_fn=os.setsid
            )
        is_running = True
        return jsonify({
            "message": "NTRIP Client Iniciado!",
            "status": "running"
        }), 200

    except Exception as e:
        return jsonify({"error": f"Error starting NTRIP Client: {str(e)}"}), 500
        
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
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

