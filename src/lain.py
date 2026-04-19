import subprocess
import time
import sys
from datetime import datetime, timedelta

# --- Configuration ---
TARGET_SCRIPT = "ptcgp.py"
INTERVAL_HOURS = 12

def run_task():
    """Executes the target automation script and captures status."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{current_time}] ⚡ Initializing TCGP automation sequence...")
    
    try:
        # Executes the script as a separate process
        result = subprocess.run([sys.executable, TARGET_SCRIPT], check=True)
        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Task completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Critical error in {TARGET_SCRIPT}: {e}")
    except FileNotFoundError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: '{TARGET_SCRIPT}' not found in the current directory.")

def main():
    print("="*50)
    print("    LAIN AUTOMATION - ver. 1.0.0")
    print("="*50)
    print()
    print("="*50)
    print("    Pokemon TCG Pocket Automation scheduler")
    print(f"    Interval: {INTERVAL_HOURS} Hours")
    print("="*50)
    print("System online. Press Ctrl+C to terminate the process.")

    while True:
        # 1. Execute the main script
        run_task()

        # 2. Calculate next execution time
        next_run = datetime.now() + timedelta(hours=INTERVAL_HOURS)
        print(f"[*] Sleeping. Next sync scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

        # 3. Wait for the interval
        # Interval converted to seconds: 12 * 60 * 60 = 43200 seconds
        time.sleep(INTERVAL_HOURS * 3600)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Shutdown signal received. Closing scheduler...")
        sys.exit(0)