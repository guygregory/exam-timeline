#!/usr/bin/env python3
"""
Script to fetch exam data from Microsoft Learn transcripts and Credly badges.

Usage:
    python passed_exams.py <ms_share_id> [--credly-user <username>] [--locale <locale>] [--output <output.csv>]

Example:
    python passed_exams.py d8yjji6kmml5jg0 --credly-user john-doe --locale en-us --output passed_exams.csv
"""
import argparse
import csv
import os
import sys
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime
import requests

MS_API_ENDPOINT = "https://learn.microsoft.com/api/profiles/transcript/share/{share_id}?locale={locale}"
CREDLY_API_ENDPOINT = "https://www.credly.com/users/{username}/badges.json"

# Mapping of Credly badge names to Microsoft exam numbers
# This helps match badges to exams when combining data
CREDLY_TO_EXAM_MAP = {
    "microsoft-certified-azure-fundamentals": "AZ-900",
    "microsoft-certified-azure-administrator-associate": "AZ-104",
    "microsoft-certified-azure-solutions-architect-expert": "AZ-305",
    "microsoft-certified-azure-developer-associate": "AZ-204",
    "microsoft-certified-azure-security-engineer-associate": "AZ-500",
    "microsoft-certified-azure-ai-fundamentals": "AI-900",
    "microsoft-certified-azure-data-fundamentals": "DP-900",
    "microsoft-certified-power-platform-fundamentals": "PL-900",
    "microsoft-365-certified-fundamentals": "MS-900",
    "microsoft-certified-security-compliance-and-identity-fundamentals": "SC-900",
    "microsoft-certified-devops-engineer-expert": "AZ-400",
    "microsoft-certified-identity-and-access-administrator-associate": "SC-300",
    "github-copilot": "GH-300",
    # Add more mappings as needed
}


def fetch_microsoft_transcript(share_id: str, locale: str = "en-us") -> Dict:
    """Fetch transcript JSON from the Microsoft Learn public API."""
    url = MS_API_ENDPOINT.format(share_id=share_id, locale=locale)
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MSFTTranscriptFetcher/1.0)"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_credly_badges(username: str) -> List[Dict]:
    """Fetch badges from Credly public profile."""
    url = CREDLY_API_ENDPOINT.format(username=username)
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; CredlyBadgeFetcher/1.0)",
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"Warning: Could not fetch Credly badges: {e}", file=sys.stderr)
        return []


def extract_microsoft_exams(transcript_json: Dict) -> List[Dict[str, str]]:
    """Extract passed exams from Microsoft Learn transcript."""
    def find_passed_exams(obj: Dict) -> List[Dict[str, str]]:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key.lower() == "passedexams" and isinstance(value, list):
                    return value
                elif isinstance(value, (dict, list)):
                    found = find_passed_exams(value)
                    if found:
                        return found
        elif isinstance(obj, list):
            for item in obj:
                found = find_passed_exams(item)
                if found:
                    return found
        return []

    raw_exams = find_passed_exams(transcript_json)
    exams: List[Dict[str, str]] = []
    for exam in raw_exams:
        exam_title = exam.get("examTitle") or exam.get("ExamTitle") or ""
        exam_number = exam.get("examNumber") or exam.get("ExamNumber") or ""
        exam_date_taken = exam.get("examDateTaken") or exam.get("ExamDateTaken") or ""
        exam_date = exam_date_taken.split("T")[0] if exam_date_taken else ""
        exams.append({
            "Exam Title": exam_title,
            "Exam Number": exam_number,
            "Exam Date": exam_date,
            "Source": "Microsoft Learn"
        })
    return exams


def extract_credly_exams(badges: List[Dict]) -> List[Dict[str, str]]:
    """Extract exam-related badges from Credly data."""
    exams: List[Dict[str, str]] = []
    
    for badge in badges:
        badge_template = badge.get("badge_template", {})
        badge_name = badge_template.get("name", "")
        badge_slug = badge_template.get("badge_template_earnable_id", "")
        issued_at = badge.get("issued_at_date", "")
        
        # Check if this badge corresponds to a known exam
        exam_number = None
        for credly_id, exam_num in CREDLY_TO_EXAM_MAP.items():
            if credly_id in badge_slug.lower():
                exam_number = exam_num
                break
        
        # Only include if we can map it to an exam
        if exam_number:
            exams.append({
                "Exam Title": badge_name,
                "Exam Number": exam_number,
                "Exam Date": issued_at,
                "Source": "Credly"
            })
        elif "microsoft" in badge_name.lower() or "github" in badge_name.lower():
            # Include other Microsoft/GitHub badges even without exact mapping
            exams.append({
                "Exam Title": badge_name,
                "Exam Number": f"Badge: {badge_slug}",
                "Exam Date": issued_at,
                "Source": "Credly"
            })
    
    return exams


def merge_exam_data(ms_exams: List[Dict[str, str]], credly_exams: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Merge exam data from both sources, removing duplicates."""
    # Create a set of (exam_number, exam_date) tuples for deduplication
    seen: Set[Tuple[str, str]] = set()
    merged: List[Dict[str, str]] = []
    
    # First add all Microsoft Learn exams
    for exam in ms_exams:
        key = (exam["Exam Number"], exam["Exam Date"])
        if key not in seen:
            seen.add(key)
            merged.append(exam)
    
    # Then add Credly exams that aren't duplicates
    for exam in credly_exams:
        # For Credly badges without exact exam numbers, use title as part of key
        if exam["Exam Number"].startswith("Badge:"):
            key = (exam["Exam Title"], exam["Exam Date"])
        else:
            key = (exam["Exam Number"], exam["Exam Date"])
        
        if key not in seen:
            seen.add(key)
            merged.append(exam)
    
    # Sort by date
    merged.sort(key=lambda x: x["Exam Date"])
    
    return merged


def write_csv(exams: List[Dict[str, str]], filename: str) -> None:
    """Write exam data to CSV file."""
    fieldnames = ["Exam Title", "Exam Number", "Exam Date", "Source"]
    with open(filename, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for exam in exams:
            writer.writerow(exam)


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract exam data from Microsoft Learn transcripts and Credly badges."
    )
    parser.add_argument("ms_share_id", help="Microsoft Learn transcript share ID")
    parser.add_argument("--credly-user", help="Credly username (optional)")
    
    default_locale = os.environ.get("LOCALE", "en-us")
    parser.add_argument("--locale", default=default_locale, 
                       help=f"Locale for Microsoft API (default: {default_locale})")
    parser.add_argument("--output", help="Output CSV filename")
    args = parser.parse_args(argv)

    # Determine output filename
    output_file = args.output or f"passed_exams_{args.ms_share_id}.csv"

    # Fetch Microsoft Learn data
    try:
        ms_transcript = fetch_microsoft_transcript(args.ms_share_id, locale=args.locale)
        ms_exams = extract_microsoft_exams(ms_transcript)
        print(f"Found {len(ms_exams)} exams from Microsoft Learn")
    except Exception as e:
        print(f"Error fetching Microsoft transcript: {e}", file=sys.stderr)
        return 1

    # Fetch Credly data if username provided
    credly_exams = []
    if args.credly_user:
        badges = fetch_credly_badges(args.credly_user)
        if badges:
            credly_exams = extract_credly_exams(badges)
            print(f"Found {len(credly_exams)} exam-related badges from Credly")

    # Merge data from both sources
    all_exams = merge_exam_data(ms_exams, credly_exams)
    
    if not all_exams:
        print("No exam data found from any source.", file=sys.stderr)
        return 1

    # Write combined data
    write_csv(all_exams, output_file)
    print(f"Wrote {len(all_exams)} total exam records to {output_file}")
    
    # Show source breakdown
    ms_count = sum(1 for e in all_exams if e["Source"] == "Microsoft Learn")
    credly_count = sum(1 for e in all_exams if e["Source"] == "Credly")
    print(f"  - Microsoft Learn: {ms_count}")
    print(f"  - Credly: {credly_count}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
