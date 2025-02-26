#!/usr/bin/env python3
"""
Test Runner Script for Waveger Backend
--------------------------------------
This script runs all test files in the tests directory
and provides a summary of the results.
"""

import os
import sys
import subprocess
import time
from datetime import datetime

# ANSI color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
BOLD = "\033[1m"
ENDC = "\033[0m"

def print_header(text):
    """Print a formatted header."""
    width = 80
    print(f"\n{BOLD}{BLUE}{'=' * width}{ENDC}")
    print(f"{BOLD}{BLUE}{text.center(width)}{ENDC}")
    print(f"{BOLD}{BLUE}{'=' * width}{ENDC}")

def print_section(text):
    """Print a section divider with text."""
    print(f"\n{BOLD}{YELLOW}{'-' * 40}{ENDC}")
    print(f"{BOLD}{YELLOW}{text}{ENDC}")
    print(f"{BOLD}{YELLOW}{'-' * 40}{ENDC}")

def run_test_file(file_path):
    """Run a single test file and return success status and output."""
    file_name = os.path.basename(file_path)
    print(f"Running {file_name}...")
    
    start_time = time.time()
    
    # Special handling for rate limits test which doesn't use pytest
    if file_name == "test_rate_limits.py":
        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True
        )
    else:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", file_path, "-v"],
            capture_output=True,
            text=True
        )
        
    elapsed_time = time.time() - start_time
    
    success = result.returncode == 0
    
    # Print summary of this test file
    status = f"{GREEN}PASSED{ENDC}" if success else f"{RED}FAILED{ENDC}"
    print(f"  Status: {status}")
    print(f"  Time: {elapsed_time:.2f} seconds")
    
    return success, result.stdout, result.stderr, elapsed_time

def find_test_files():
    """Find all test files in the tests directory."""
    tests_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")
    if not os.path.exists(tests_dir):
        print(f"{RED}Error: Tests directory not found at {tests_dir}{ENDC}")
        return []
    
    test_files = []
    for file in os.listdir(tests_dir):
        if file.startswith("test_") and file.endswith(".py"):
            test_files.append(os.path.join(tests_dir, file))
    
    return sorted(test_files)

def check_for_test_errors():
    """Check for common errors in test files but don't fix them."""
    print_section("Checking for test files")
    
    tests_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")
    if not os.path.exists(tests_dir):
        print(f"{RED}Error: Tests directory not found at {tests_dir}{ENDC}")
        return False
        
    print(f"Found tests directory at {tests_dir}")
    return False

def main():
    """Main function to run all tests."""
    print_header("WaveGer Backend Test Runner")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Just check for test directory
    check_for_test_errors()
    
    # Find all test files
    test_files = find_test_files()
    if not test_files:
        print(f"{RED}No test files found!{ENDC}")
        return 1
    
    print(f"Found {len(test_files)} test files to run.\n")
    
    # Run each test file
    results = []
    total_time = 0
    
    for file_path in test_files:
        print_section(f"Testing {os.path.basename(file_path)}")
        success, stdout, stderr, elapsed = run_test_file(file_path)
        
        results.append({
            'file': os.path.basename(file_path),
            'success': success,
            'stdout': stdout,
            'stderr': stderr,
            'time': elapsed
        })
        
        total_time += elapsed
        
        # Print detailed output for failed tests
        if not success:
            print(f"\n{YELLOW}Test output:{ENDC}")
            if stderr.strip():
                print(f"{RED}{stderr}{ENDC}")
            else:
                print(stdout)
    
    # Print summary
    print_header("Test Results Summary")
    
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    
    print(f"Total test files: {len(results)}")
    print(f"Passed: {GREEN}{passed}{ENDC}")
    print(f"Failed: {RED if failed else GREEN}{failed}{ENDC}")
    print(f"Total time: {total_time:.2f} seconds")
    
    # Print table of results
    print_section("Detailed Results")
    
    print(f"{BOLD}{'Test File':<30} | {'Status':<10} | {'Time (s)':<10}{ENDC}")
    print(f"{'-' * 30}-+-{'-' * 10}-+-{'-' * 10}")
    
    for r in results:
        status = f"{GREEN}PASS{ENDC}" if r['success'] else f"{RED}FAIL{ENDC}"
        print(f"{r['file']:<30} | {status:<10} | {r['time']:<10.2f}")
    
    # Return appropriate exit code
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())