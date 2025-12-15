import subprocess
import time
import os
import signal
from datetime import datetime

# Path constants
UR_LAUNCH_PACKAGE = "ur_simulation_gazebo"
UR_LAUNCH_FILE = "ur_sim_control.launch.py"
LOG_FILE = os.path.join(os.getcwd(), "logs", "sim_output.log")
CUBE_MODEL_PATH = os.path.join(os.getcwd(), "worlds", "task_world.sdf")
USER_CODE_DIR = os.path.join(os.getcwd(), "uploads", "user_code")
ROS_WS_SETUP = "~/workspaces/ur_gazebo/install/setup.bash" # Assumes your workspace is here

def run_simulation(user_package_name="user_pick_place_pkg", user_node_executable="pick_place_node"):
    """
    1. Launch UR5e with custom world.
    2. Wait for Gazebo to be ready.
    3. Run the user's ROS 2 node.
    4. Record logs and check for success.
    """
    
    print("Starting simulation...")
    with open(LOG_FILE, 'w') as log_f:
        log_f.write(f"--- Simulation Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        
        # --- 1. Launch UR5e with custom world ---
        # Note: The UR launch file needs to be modified or sourced properly to load the custom world.
        # For simplicity in the backend script, we will try to pass the custom world as an argument.
        # This assumes the base UR launch file has a 'world' argument, or we write a wrapper launch file.
        # Given the existing setup, we'll use ExecuteProcess to launch the *base* UR launch file,
        # which will load its default empty world, and then we will rely on our SDF to spawn entities.
        
        # A simple, robust way is to source ROS and run a complex command as a single shell process
        # This is a critical step that requires the simulation environment to be correctly sourced.
        
        # This is the actual command to launch the robot and the world.
        launch_cmd = (
            f"source {ROS_WS_SETUP} && "
            f"ros2 launch {UR_LAUNCH_PACKAGE} {UR_LAUNCH_FILE} "
            f"ur_type:=ur5e launch_rviz:=false gazebo_gui:=true "
            f"world_path:={CUBE_MODEL_PATH} " # Assuming the launch file accepts this arg
            f"&" # Run in background
        )
        
        # Start the Gazebo/ROS system
        # We need a robust way to kill the entire process tree later (preexec_fn=os.setsid helps)
        try:
            sim_process = subprocess.Popen(launch_cmd, shell=True, executable='/bin/bash', preexec_fn=os.setsid, stdout=log_f, stderr=log_f)
            log_f.write(f"ROS/Gazebo launched with PID: {sim_process.pid}\n")
            log_f.flush()
        except Exception as e:
            log_f.write(f"ERROR launching simulation: {e}\n")
            return False

        # --- 2. Wait for Gazebo/ROS to be ready (Critical Step) ---
        log_f.write("Waiting 15 seconds for Gazebo to stabilize...\n")
        time.sleep(15)
        log_f.flush()

        # --- 3. Run the user's ROS 2 node ---
        # Note: The user's package must be built in the ROS workspace for 'ros2 run' to work.
        # For this script, we assume the code checker handled building the code with `colcon build`.
        user_run_cmd = (
            f"source {ROS_WS_SETUP} && "
            f"ros2 run {user_package_name} {user_node_executable}"
        )

        user_node_process = subprocess.Popen(user_run_cmd, shell=True, executable='/bin/bash', preexec_fn=os.setsid, stdout=log_f, stderr=log_f)
        log_f.write(f"User node running with PID: {user_node_process.pid}\n")
        log_f.flush()

        # --- 4. Simulation Duration and Monitoring ---
        log_f.write("Running simulation for 20 seconds...\n")
        
        # Poll for joint states (simple success heuristic)
        # In a real environment, you'd check TF or cube/target position via Gazebo services.
        monitor_cmd = (f"source {ROS_WS_SETUP} && ros2 topic echo /joint_states --once")
        
        simulation_time = 20
        motion_detected = False
        for i in range(simulation_time // 5):
            time.sleep(5)
            # Check for joint state messages (indicates controller is running and robot is active)
            try:
                result = subprocess.run(monitor_cmd, shell=True, executable='/bin/bash', capture_output=True, text=True, timeout=3)
                if "position" in result.stdout:
                    log_f.write(f"Joint motion confirmed at time: {i*5}s\n")
                    motion_detected = True
                else:
                    log_f.write(f"No joint state received at time: {i*5}s\n")
            except subprocess.TimeoutExpired:
                log_f.write(f"Joint state echo timed out at time: {i*5}s\n")
            log_f.flush()

        # --- 5. Cleanup ---
        log_f.write("--- Simulation End, Killing processes ---\n")
        
        # Kill all child processes started by the launch process (Gazebo, robot_state_publisher, etc.)
        os.killpg(os.getpgid(sim_process.pid), signal.SIGTERM)
        os.killpg(os.getpgid(user_node_process.pid), signal.SIGTERM)
        time.sleep(2) # Give time for processes to stop
        
        # Determine Success/Failure (Placeholder for actual physics check)
        success_status = "PASS" if motion_detected else "FAIL" 
        log_f.write(f"Simulation Result: {success_status}\n")
        
    return success_status