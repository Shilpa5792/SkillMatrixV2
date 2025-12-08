#!/usr/bin/env python
"""
Simple test runner script for functionsV2 APIs.
Run this from the functionsV2 directory.
"""
import sys
import subprocess
import os

def main():
    """Run pytest tests."""
    # Get the directory where this script is located
    test_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(test_dir)
    
    # Change to parent directory (functionsV2) so imports work correctly
    os.chdir(parent_dir)
    
    # Add parent directory to Python path
    sys.path.insert(0, parent_dir)
    
    # Run pytest
    result = subprocess.run(
        ['pytest', 'tests', '-v'],
        cwd=parent_dir
    )
    
    sys.exit(result.returncode)

if __name__ == '__main__':
    main()

