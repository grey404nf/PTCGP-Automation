import subprocess
import os
import sys
from datetime import datetime

# --- Configuration ---
ADB_PATH = r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe"

def get_connected_device():
    """Dynamically detects the first available ADB device."""
    try:
        # Get the list of devices
        output = subprocess.check_output([ADB_PATH, "devices"]).decode('utf-8')
        lines = output.strip().split('\n')[1:] # Skip the header
        for line in lines:
            if 'device' in line:
                # Returns the first device ID found (e.g., 'emulator-5554')
                return line.split()[0]
    except Exception as e:
        print(f"[!] Error detecting devices: {e}")
    return None

def take_screenshot():
    # 1. Detect device ID automatically
    device_id = get_connected_device()
    
    if not device_id:
        print("[!] No active device found. Please ensure BlueStacks is open and ADB is enabled.")
        return

    # 2. Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    
    # 3. Use exec-out for high-speed streaming
    # We wrap ADB_PATH in quotes in case there are spaces in the path
    cmd = f'"{ADB_PATH}" -s {device_id} exec-out screencap -p'
    
    print(f"[*] Target Device: {device_id}")
    print(f"[*] Capturing to: {filename}...")
    
    try:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        image_data, _ = process.communicate()
        
        # Validate PNG header
        if image_data.startswith(b"\x89PNG"):
            with open(filename, "wb") as f:
                f.write(image_data)
            print(f"[+] Success! Saved to: {os.path.abspath(filename)}")
        else:
            print("[!] Error: Received invalid data. Try resetting the ADB server.")
            
    except Exception as e:
        print(f"[!] Critical Error: {str(e)}")

if __name__ == "__main__":
    take_screenshot()