"""
Patient Explorer Desktop Launcher

Starts the Streamlit server and opens the default browser.
Designed to be packaged with PyInstaller for distribution.

Usage:
    python scripts/launcher.py

Or after PyInstaller build:
    PatientExplorer.exe
"""

import subprocess
import webbrowser
import time
import sys
import os
import signal
import socket
from pathlib import Path
from typing import Optional

# Configuration
PORT = 8501
HOST = "127.0.0.1"
STARTUP_TIMEOUT = 30  # seconds


def get_app_path() -> Path:
    """
    Get the path to the application directory.
    Handles both development and PyInstaller bundled scenarios.
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        return Path(sys._MEIPASS)
    else:
        # Running as script
        return Path(__file__).parent.parent


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except socket.error:
            return True


def wait_for_server(port: int, host: str = "127.0.0.1", timeout: int = 30) -> bool:
    """
    Wait for the Streamlit server to start accepting connections.
    Returns True if server started, False if timeout.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect((host, port))
                return True
        except (socket.error, socket.timeout):
            time.sleep(0.5)
    return False


def find_streamlit_main() -> Optional[Path]:
    """Locate the main.py Streamlit entry point."""
    app_path = get_app_path()

    # Try different possible locations
    candidates = [
        app_path / "app" / "main.py",
        app_path / "main.py",
        Path.cwd() / "app" / "main.py",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def main():
    """Main entry point for the desktop launcher."""
    print("=" * 50)
    print("  Patient Explorer Desktop Launcher")
    print("=" * 50)
    print()

    # Check if already running
    if is_port_in_use(PORT, HOST):
        print(f"Port {PORT} is already in use.")
        print("Opening browser to existing instance...")
        webbrowser.open(f"http://{HOST}:{PORT}")
        return 0

    # Find main.py
    main_py = find_streamlit_main()
    if not main_py:
        print("ERROR: Could not find app/main.py")
        print("Please ensure you're running from the Patient Explorer directory.")
        input("Press Enter to exit...")
        return 1

    print(f"Starting Streamlit server...")
    print(f"  Main file: {main_py}")
    print(f"  Address: http://{HOST}:{PORT}")
    print()

    # Determine Python executable
    if getattr(sys, 'frozen', False):
        # In PyInstaller bundle, use bundled Python
        python_exe = sys.executable
    else:
        # In development, use current Python
        python_exe = sys.executable

    # Build Streamlit command
    streamlit_args = [
        python_exe, "-m", "streamlit", "run",
        str(main_py),
        "--server.port", str(PORT),
        "--server.address", HOST,
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--theme.base", "light",
    ]

    # Set working directory to app root
    app_path = get_app_path()

    # Start Streamlit process
    try:
        process = subprocess.Popen(
            streamlit_args,
            cwd=str(app_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
    except Exception as e:
        print(f"ERROR: Failed to start Streamlit: {e}")
        input("Press Enter to exit...")
        return 1

    print("Waiting for server to start...")

    # Wait for server to be ready
    if wait_for_server(PORT, HOST, STARTUP_TIMEOUT):
        print("Server started successfully!")
        print()
        print("Opening browser...")
        webbrowser.open(f"http://{HOST}:{PORT}")
        print()
        print("-" * 50)
        print("Patient Explorer is running.")
        print("Close this window to stop the server.")
        print("-" * 50)
    else:
        print("WARNING: Server may not have started properly.")
        print("Attempting to open browser anyway...")
        webbrowser.open(f"http://{HOST}:{PORT}")

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\nShutting down...")
        process.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Wait for process to complete (user closes window or Ctrl+C)
    try:
        process.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        process.terminate()

    print("Patient Explorer stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
