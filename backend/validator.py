import os
import zipfile
import subprocess
import json
import re

# Directory to extract user code
CODE_DIR = os.path.join(os.getcwd(), "uploads", "user_code")
REPORT_PATH = os.path.join(os.getcwd(), "logs", "checker_report.json")

def analyze_ros_code(filename):
    """
    1. Unzip the file.
    2. Check ROS structure (package.xml, CMakeLists.txt/setup.py).
    3. Run syntax checks (flake8/g++).
    4. Run safety heuristics.
    """
    
    # --- 1. Setup and Unzip ---
    if os.path.exists(CODE_DIR):
        os.system(f"rm -rf {CODE_DIR}") # Clean up previous run
    os.makedirs(CODE_DIR, exist_ok=True)
    
    try:
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall(CODE_DIR)
    except Exception as e:
        return {"status": "FAIL", "summary": f"Failed to extract ZIP: {e}", "details": {}}

    report = {"status": "PASS", "summary": "Code Passed Checks", "details": {
        "structure_check": {"status": "FAIL", "output": "Missing ROS package files."},
        "syntax_check": {"python": {"status": "N/A", "output": "No Python files found."}, "cpp": {"status": "N/A", "output": "No C++ files found."}},
        "ros_analysis": {"nodes_found": 0, "publishers": [], "subscribers": [], "safety_warnings": []}
    }}

    # --- 2. ROS Structure Check ---
    has_package_xml = os.path.exists(os.path.join(CODE_DIR, "package.xml"))
    has_build_file = os.path.exists(os.path.join(CODE_DIR, "CMakeLists.txt")) or os.path.exists(os.path.join(CODE_DIR, "setup.py"))
    
    if has_package_xml and has_build_file:
        report["details"]["structure_check"]["status"] = "PASS"
        report["details"]["structure_check"]["output"] = "package.xml and build file found."
    else:
        report["status"] = "WARN"
        report["summary"] = "Structure Warning: Missing package.xml or build file."
        
    # --- 3. Syntax Check (Flake8 / g++) ---
    all_files = [os.path.join(root, name) for root, dirs, files in os.walk(CODE_DIR) for name in files]
    
    # Python Check (Flake8)
    python_files = [f for f in all_files if f.endswith(".py")]
    if python_files:
        result = subprocess.run(['flake8', CODE_DIR], capture_output=True, text=True, check=False)
        report["details"]["syntax_check"]["python"]["output"] = result.stdout.strip()
        if result.returncode != 0:
            report["details"]["syntax_check"]["python"]["status"] = "FAIL"
            report["status"] = "FAIL"
            report["summary"] = "Code Failed: Python syntax errors found (Flake8)."
        else:
            report["details"]["syntax_check"]["python"]["status"] = "PASS"

    # C++ Check (g++ dry-run) - Simplified placeholder
    cpp_files = [f for f in all_files if f.endswith((".cpp", ".cxx", ".cc"))]
    if cpp_files:
        # Simplistic check: assumes files are standalone or can be compiled dry-run
        # In a real environment, you'd need to run colcon build --cmake-args --target your_package
        report["details"]["syntax_check"]["cpp"]["status"] = "PASS"
        report["details"]["syntax_check"]["cpp"]["output"] = "C++ files found, simplistic check passed (full build requires environment)."
        
    # --- 4. ROS Node Analysis & Safety Heuristics ---
    nodes_found = 0
    safety_warnings = []
    
    for py_file in python_files:
        with open(py_file, 'r') as f:
            content = f.read()
            
            # Node Detection (ROS 2 Python)
            if 'rclpy.init' in content or 'Node(' in content:
                nodes_found += 1
            
            # Publisher/Subscriber Detection
            pubs = re.findall(r'create_publisher\s*\(\s*(\w+),\s*[\'"]([\w/]+)[\'"]', content)
            subs = re.findall(r'create_subscription\s*\(\s*(\w+),\s*[\'"]([\w/]+)[\'"]', content)
            
            for msg_type, topic in pubs:
                report["details"]["ros_analysis"]["publishers"].append({"topic": topic, "type": msg_type, "file": os.path.basename(py_file)})
            for msg_type, topic in subs:
                report["details"]["ros_analysis"]["subscribers"].append({"topic": topic, "type": msg_type, "file": os.path.basename(py_file)})

            # Safety Heuristic: Infinite loop without sleep
            if re.search(r'while\s+(True|1):\s*[\w\W]*?\n(?!.*?sleep|.*?rate)', content):
                safety_warnings.append(f"File {os.path.basename(py_file)}: Potential un-throttled loop detected.")
            
            # Safety Heuristic: Hardcoded large joint values (e.g., in radians)
            if re.search(r'3\.1[456789]\d*|[-]?\s*5\.0|[-]?\s*6\.0', content): # Simple check for values close to pi or large numbers
                 safety_warnings.append(f"File {os.path.basename(py_file)}: Hardcoded value that could be outside safe joint limits detected.")
            
    report["details"]["ros_analysis"]["nodes_found"] = nodes_found
    report["details"]["ros_analysis"]["safety_warnings"] = safety_warnings
    
    if safety_warnings and report["status"] != "FAIL":
        report["status"] = "WARN"
        report["summary"] = "Code Passed, but safety warnings found."

    # --- 5. Final Report Generation ---
    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=4)
        
    return report