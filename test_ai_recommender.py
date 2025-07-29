#!/usr/bin/env python3
"""
Test script for ai_exam_recommender.py
This script validates that all prerequisites are met for the AI exam recommender.
"""

import os
import sys
import json

def test_prerequisites():
    """Test all prerequisites for ai_exam_recommender.py"""
    print("🔍 Testing AI Exam Recommender Prerequisites")
    print("=" * 50)
    
    issues = []
    
    # Test 1: Check if GITHUB_TOKEN is set
    print("1. Checking GITHUB_TOKEN environment variable...")
    if "GITHUB_TOKEN" in os.environ:
        token_length = len(os.environ["GITHUB_TOKEN"])
        print(f"   ✅ GITHUB_TOKEN is set (length: {token_length} characters)")
    else:
        print("   ❌ GITHUB_TOKEN is not set")
        issues.append("GITHUB_TOKEN environment variable is required")
    
    # Test 2: Check if openai package is available
    print("\n2. Checking OpenAI package availability...")
    try:
        import openai
        print(f"   ✅ OpenAI package is available (version: {openai.__version__})")
    except ImportError:
        print("   ❌ OpenAI package is not installed")
        issues.append("Install with: pip install openai")
    
    # Test 3: Check if required CSV files exist
    print("\n3. Checking required CSV files...")
    
    required_files = ["passed_exams.csv", "priority_ARB_exams.csv"]
    for filename in required_files:
        if os.path.exists(filename):
            print(f"   ✅ {filename} exists")
            # Show file size
            size = os.path.getsize(filename)
            print(f"      File size: {size} bytes")
        else:
            print(f"   ❌ {filename} is missing")
            issues.append(f"Required file {filename} is missing")
    
    # Test 4: Validate CSV file contents
    print("\n4. Validating CSV file contents...")
    
    # Check passed_exams.csv format
    try:
        with open("passed_exams.csv", "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.strip().split("\n")
            print(f"   ✅ passed_exams.csv has {len(lines)} lines")
            if len(lines) > 1:
                print(f"      Sample: {lines[1][:50]}...")
    except FileNotFoundError:
        print("   ❌ Cannot read passed_exams.csv")
    except Exception as e:
        print(f"   ⚠️  Error reading passed_exams.csv: {e}")
    
    # Check priority_ARB_exams.csv format
    try:
        with open("priority_ARB_exams.csv", "r", encoding="utf-8") as f:
            content = f.read().strip()
            exam_codes = [exam.strip() for exam in content.split(",")]
            print(f"   ✅ priority_ARB_exams.csv has {len(exam_codes)} exam codes")
            print(f"      Sample codes: {', '.join(exam_codes[:5])}")
    except FileNotFoundError:
        print("   ❌ Cannot read priority_ARB_exams.csv")
    except Exception as e:
        print(f"   ⚠️  Error reading priority_ARB_exams.csv: {e}")
    
    # Test 5: Test script import
    print("\n5. Testing script import...")
    try:
        # This will test if the script has syntax errors
        with open("ai_exam_recommender.py", "r") as f:
            script_content = f.read()
        compile(script_content, "ai_exam_recommender.py", "exec")
        print("   ✅ ai_exam_recommender.py syntax is valid")
    except FileNotFoundError:
        print("   ❌ ai_exam_recommender.py not found")
        issues.append("ai_exam_recommender.py script is missing")
    except SyntaxError as e:
        print(f"   ❌ Syntax error in ai_exam_recommender.py: {e}")
        issues.append("Fix syntax errors in ai_exam_recommender.py")
    except Exception as e:
        print(f"   ⚠️  Error checking ai_exam_recommender.py: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    if not issues:
        print("🎉 All prerequisites are met!")
        print("✅ The ai_exam_recommender.py script is ready to run in GitHub Actions")
        return True
    else:
        print("❌ Issues found:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print("\n💡 Fix these issues before running ai_exam_recommender.py")
        return False

if __name__ == "__main__":
    success = test_prerequisites()
    sys.exit(0 if success else 1)