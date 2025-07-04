#!/usr/bin/env python3
"""
AI Novel Generator - Simple Launcher
Direct execution of app.py with enhanced features
"""

import subprocess
import sys
import os

def main():
    print("🚀 AI Novel Generator - Starting...")
    
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run app.py directly
    try:
        subprocess.run([sys.executable, "app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Application failed to start: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n✅ Application stopped by user")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())