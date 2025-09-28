#!/usr/bin/env python3
"""
Setup script for Crisis-Compass backend dependencies.
Run this script to install required Python packages.
"""

import subprocess
import sys
import os

def install_requirements():
    """Install Python requirements from requirements.txt"""
    try:
        print("Installing Python dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"])
        print("✅ Python dependencies installed successfully!")
        
        # Download spaCy model
        print("Downloading spaCy English model...")
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        print("✅ spaCy model downloaded successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    
    return True

def main():
    print("🚀 Setting up Crisis-Compass backend...")
    
    # Change to backend directory
    os.chdir("backend")
    
    if install_requirements():
        print("\n🎉 Backend setup complete!")
        print("\nTo start the backend server, run:")
        print("  python app.py")
        print("\nTo start the frontend, run (in a new terminal):")
        print("  npm run dev")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
