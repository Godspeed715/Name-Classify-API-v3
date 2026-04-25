#!/usr/bin/env python3
"""
Vercel build script for downloading spacy model and dependencies.
This runs during the Vercel build phase.
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a shell command and report status."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"\n❌ ERROR: {description} failed!")
        sys.exit(1)
    print(f"\n✅ {description} completed successfully!")

# Step 1: Install dependencies
run_command(
    f"{sys.executable} -m pip install -r requirements.txt",
    "Installing Python dependencies"
)

# Step 2: Download spacy model
run_command(
    f"{sys.executable} -m spacy download en_core_web_sm",
    "Downloading spacy English model"
)

print("\n" + "="*60)
print("  🎉 Build completed successfully!")
print("="*60 + "\n")
