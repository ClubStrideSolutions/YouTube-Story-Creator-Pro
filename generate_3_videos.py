#!/usr/bin/env python3
"""
Generate 3 specific videos: Mental Health, Sexual Health, Food Security
"""

import os
import sys
import subprocess

# Set API key if not already set
if not os.environ.get('OPENAI_API_KEY'):
    print("Please set your OpenAI API key:")
    api_key = input("Enter OpenAI API key: ")
    os.environ['OPENAI_API_KEY'] = api_key

print("\n" + "="*50)
print("Generating 3 Videos:")
print("1. Mental Health")
print("2. Sexual Health & STI Resources")
print("3. Food Security & Access")
print("="*50 + "\n")

# Run the generation script
result = subprocess.run([
    sys.executable, 
    "local_content_gen.py",
    "--videos", "3"
], capture_output=False, text=True)

if result.returncode == 0:
    print("\n" + "="*50)
    print("SUCCESS! All 3 videos generated.")
    print("Check the generated_content folder for your videos.")
    print("="*50)
else:
    print("\n" + "="*50)
    print("Some videos may have failed. Check content_generation.log for details.")
    print("="*50)

sys.exit(result.returncode)