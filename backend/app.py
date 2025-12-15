import os
import json
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from validator import analyze_ros_code
from simulator import run_simulation, LOG_FILE, CODE_DIR, REPORT_PATH

# Configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
LOG_FOLDER = os.path.join(os.getcwd(), 'logs')
ALLOWED_EXTENSIONS = {'zip'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['LOG_FOLDER'] = LOG_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)
os.makedirs(CODE_DIR, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- API Endpoints ---

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file part", "status": "ERROR"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file", "status": "ERROR"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Always save as a standard name to avoid path issues
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], 'user_code.zip')
        file.save(zip_path)
        
        # Run the Code Checker immediately
        report = analyze_ros_code(zip_path)
        
        # Read the generated JSON report
        with open(REPORT_PATH, 'r') as f:
            report_data = json.load(f)

        return jsonify({"message": f"File uploaded and checked. Status: {report_data['status']}", "status": report_data['status'], "report": report_data}), 200
    
    return jsonify({"message": "File type not allowed", "status": "ERROR"}), 400

@app.route('/api/check_status', methods=['GET'])
def check_status():
    if not os.path.exists(REPORT_PATH):
         return jsonify({"status": "PENDING", "message": "No report found. Upload code first."}), 200
         
    with open(REPORT_PATH, 'r') as f:
        report_data = json.load(f)
        
    return jsonify({"status": report_data['status'], "report": report_data}), 200

@app.route('/api/run_simulation', methods=['POST'])
def run_sim():
    if not os.path.exists(REPORT_PATH):
        return jsonify({"message": "Please run code check first.", "status": "ERROR"}), 400
        
    with open(REPORT_PATH, 'r') as f:
        report_data = json.load(f)
        
    if report_data['status'] == 'FAIL':
        return jsonify({"message": "Simulation aborted: Code checker failed.", "status": "ABORTED"}), 400
        
    # --- Execute Simulation ---
    # NOTE: You MUST update run_simulation with the user's actual package/node name.
    # For a simple demo, we use placeholder names. In production, the checker should extract this.
    final_status = run_simulation(user_package_name="user_package", user_node_executable="user_node_exec")
    
    return jsonify({"message": "Simulation complete.", "status": final_status, "log_file": "sim_output.log"}), 200

@app.route('/api/logs/<filename>', methods=['GET'])
def get_log(filename):
    # Security check to prevent path traversal
    if filename not in ['sim_output.log', 'checker_report.json']:
        return jsonify({"message": "Invalid log file request"}), 400
    
    return send_from_directory(app.config['LOG_FOLDER'], filename)


if __name__ == '__main__':
    # Add your ROS 2 workspace's build directory to the Python path if necessary for local testing
    # os.environ['PYTHONPATH'] = os.path.join(os.path.expanduser('~'), 'workspaces', 'ur_gazebo', 'install', 'lib', 'python3.10', 'site-packages')
    # os.environ['AMENT_PREFIX_PATH'] = os.path.join(os.path.expanduser('~'), 'workspaces', 'ur_gazebo', 'install')
    
    app.run(debug=True, port=5000)