import subprocess
import time
import os
import cv2
import numpy as np
import re
import sys

# --- Configuration ---
ADB_PATH = r'"C:\Program Files\BlueStacks_nxt\HD-Adb.exe"'
PACKAGE_NAME = "jp.pokemon.pokemontcgp"
APP_ACTIVITY = f"{PACKAGE_NAME}/com.unity3d.player.UnityPlayerActivity"

# Image Paths (Templates still need to exist on disk)
IMG_MAIN_PAGE = "pics/main_page.png"
IMG_PACK      = "pics/pack.png"
IMG_2PACKS    = "pics/2packs.png"
IMG_OPEN      = "pics/button_open.png"
IMG_SKIP      = "pics/button_skip.png"
IMG_SKIP_LONG = "pics/button_skip_long.png"
IMG_MISSION   = "pics/button_green_mission.png"
IMG_GET_ALL   = "pics/button_getAll.png"
IMG_OK        = "pics/button_OK.png"
IMG_BACK      = "pics/button_back.png"
IMG_CROSS      = "pics/button_cross.png"

TARGET_DEVICE = None

def get_connected_device():
    """Detects the connected ADB device."""
    try:
        clean_path = ADB_PATH.replace('"', '')
        output = subprocess.check_output([clean_path, "devices"]).decode('utf-8')
        lines = output.strip().split('\n')[1:]
        for line in lines:
            if 'device' in line and not 'offline' in line:
                return line.split()[0]
    except Exception as e:
        print(f"[!] Device detection error: {e}")
    return None

def run_adb(command):
    """Executes ADB commands using the TARGET_DEVICE."""
    if not TARGET_DEVICE: return b""
    full_cmd = f"{ADB_PATH} -s {TARGET_DEVICE} {command}"
    try:
        # Use subprocess.PIPE to capture the binary stream correctly
        return subprocess.check_output(full_cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        return b""

def tap(x, y, wait_time=15):
    """Taps and waits 15 seconds."""
    print(f"[*] Action: Tapping ({x}, {y})...")
    run_adb(f"shell input tap {x} {y}")
    print(f"[*] Waiting {wait_time}s...")
    time.sleep(wait_time)

def close_app():
    """Force stops the application."""
    print(f"[*] Action: Force stopping {PACKAGE_NAME}...")
    run_adb(f"shell am force-stop {PACKAGE_NAME}")
    time.sleep(5)

def find_image(template_path, threshold=0.75, check_saturation=False, min_sat=50):
    """
    Finds an image and optionally checks the MEAN saturation of the entire detected area.
    """
    if not os.path.exists(template_path): return None
    
    # 1. Capture screen data (Memory-only)
    img_bytes = run_adb("exec-out screencap -p")
    if not img_bytes.startswith(b"\x89PNG"): return None
    nparr = np.frombuffer(img_bytes, np.uint8)
    screen = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    template = cv2.imread(template_path)
    
    if screen is None or template is None: return None
    h, w = template.shape[:2]
    
    # 2. Match Template
    res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    
    if max_val >= threshold:
        top_left_x, top_left_y = max_loc
        center_x, center_y = top_left_x + w // 2, top_left_y + h // 2
        
        # --- ROI Mean Saturation Logic ---
        if check_saturation:
            # Crop the detected region from the screen
            roi = screen[top_left_y : top_left_y + h, top_left_x : top_left_x + w]
            hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # Calculate the average saturation of the whole button area
            avg_saturation = np.mean(hsv_roi[:, :, 1])
            
            print(f"[*] Detected {os.path.basename(template_path)}: Sim={max_val:.2f}, Mean Sat={avg_saturation:.2f}")
            
            if avg_saturation < min_sat:
                print(f"[!] Button found but it is GRAY (Mean Sat: {avg_saturation:.2f}). Skipping.")
                return None
            print(f"[+] Button is ACTIVE (Mean Sat: {avg_saturation:.2f})")
            
        return (center_x, center_y)
    return None

def reach_main_page():
    """Navigates to Main Page."""
    for i in range(5):
        print(f"[*] Detecting Main Page - Attempt {i+1}/5")
        if find_image(IMG_MAIN_PAGE):
            print("[+] Main Page reached!")
            return True
        
        pos_back = find_image(IMG_BACK)
        pos_ok = find_image(IMG_OK)
        pos_cross = find_image(IMG_CROSS)
        if pos_back:
            tap(pos_back[0], pos_back[1])
        elif pos_ok:
            tap(pos_ok[0], pos_ok[1])
        elif pos_cross:
            tap(pos_cross[0], pos_cross[1])
        else:
            tap(540, 960)
    return False

def mission_logic():
    print("\n--- Mission Sequence (Saturation Aware) ---")
    # Only IMG_MISSION uses the saturation check here
    pos_mission = find_image(IMG_MISSION, check_saturation=True)
    
    if pos_mission:
        tap(pos_mission[0], pos_mission[1])
        while True:
            # Only IMG_GET_ALL uses the saturation check here
            pos_get_all = find_image(IMG_GET_ALL, check_saturation=True)
            
            if pos_get_all:
                tap(pos_get_all[0], pos_get_all[1])
                pos_ok = find_image(IMG_OK)
                if pos_ok: tap(pos_ok[0], pos_ok[1])
            else:
                print("[-] No more colorful 'Get All' buttons detected.")
                break
    else:
        print("[!] Active Mission button not found.")
    close_app()

def draw_pack_logic():
    """Handles Pack drawing."""
    print("\n--- Pack Sequence ---")
    tap(540, 960)
    tap(540, 960)
    
    pos_open = find_image(IMG_OPEN)
    if pos_open:
        tap(pos_open[0], pos_open[1])
        pos_skip = find_image(IMG_SKIP)
        if pos_skip: tap(pos_skip[0], pos_skip[1])
        
        print("[*] Performing seal swipe...")
        run_adb(f"shell input swipe 100 1110 1000 1110 300")
        time.sleep(15)
        
        pos_long = find_image(IMG_SKIP_LONG)
        if pos_long:
            run_adb(f"shell input swipe {pos_long[0]} {pos_long[1]} {pos_long[0]} {pos_long[1]} 10000")
            time.sleep(15)
        return True
    return False

def main():
    global TARGET_DEVICE
    print("="*50)
    print("    POKEMON TCG POCKET AUTOMATION - ver. 1.0.0")
    print("    Executing 'ptcgp.py' ...")
    print("="*50)

    TARGET_DEVICE = get_connected_device()
    if not TARGET_DEVICE: 
        print("[!] No device found.")
        sys.exit(1)

    close_app()
    run_adb(f"shell am start -n {APP_ACTIVITY}")
    time.sleep(15)
    tap(540, 960)

    # Pack Check Loop
    while True:
        if reach_main_page():
            # Detect single pack or multiple packs icon
            if find_image(IMG_PACK) or find_image(IMG_2PACKS):
                print("[+] Pack detected! Starting draw sequence...")
                draw_pack_logic()
                
                # Restart for clean UI state
                print("[*] Draw finished. Restarting to check for more packs...")
                close_app()
                run_adb(f"shell am start -n {APP_ACTIVITY}")
                time.sleep(15)
                tap(540, 960)
                # Loop continues back to reach_main_page()
            else:
                print("[-] No more packs found. Moving to Missions.")
                mission_logic()
                break # All done, exit the loop
        else:
            print("[!] Failed to reach Main Page. Shutting down.")
            close_app()
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Stopped.")