#!/usr/bin/env python3
"""
Script to fetch a public Microsoft Learn transcript and extract passed exam information.

Usage:
    python passed_exams.py <share_id> [--locale <locale>] [--output <output.csv>]

Example:
    python passed_exams.py d8yjji6kmml5jg0 --locale en-us --output passed_exams.csv

If no output filename is provided, the script writes to passed_exams_<share_id>.csv.

The share_id is the identifier at the end of the public transcript URL, e.g., for
https://learn.microsoft.com/en-gb/users/<username>/transcript/<share_id>, use <share_id>.

The script makes a GET request to the transcript API endpoint:
https://learn.microsoft.com/api/profiles/transcript/share/<share_id>?locale=<locale>

The API returns JSON containing a `passedExams` array with exam details. The script
writes a CSV file containing the exam title, exam number and the date taken.

Note: Internet access is required for this script to work. The API endpoint is
unauthenticated for public transcripts, but may block calls if you are not
sending an appropriate User‑Agent header. If you encounter a 403 response,
try adding a User‑Agent or run the script from a network with access to
learn.microsoft.com.

To test locally, you can start a local web server `python -m http.server 8000` and then open using `http://localhost:8000`.
"""
import argparse
import csv
import os
import sys
from typing import List, Dict
import requests

API_ENDPOINT_TEMPLATE = "https://learn.microsoft.com/api/profiles/transcript/share/{share_id}?locale={locale}"


def fetch_transcript(share_id: str, locale: str = "en-us") -> Dict:
    """Fetch transcript JSON from the Microsoft Learn public API.

    :param share_id: The transcript sharing identifier from the URL
    :param locale: Locale parameter for the API (default: en-us)
    :return: Parsed JSON response
    :raises requests.HTTPError: if the HTTP request returned an unsuccessful status code
    :raises ValueError: if the response cannot be decoded as JSON
    """
    url = API_ENDPOINT_TEMPLATE.format(share_id=share_id, locale=locale)
    headers = {
        # Provide a User‑Agent to avoid potential filtering of generic requests
        "User-Agent": "Mozilla/5.0 (compatible; MSFTTranscriptFetcher/1.0)"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def extract_passed_exams(transcript_json: Dict) -> List[Dict[str, str]]:
    """
    Extract a list of passed exams from the transcript JSON.

    Microsoft may evolve the transcript schema over time; exam details
    have been observed under ``certificationData.passedExams`` but could
    appear elsewhere.  This function searches the entire JSON structure
    recursively for a list associated with the key ``passedExams``.

    :param transcript_json: Transcript JSON as returned by the API
    :return: List of dictionaries with exam title, number and date
    """
    def find_passed_exams(obj: Dict) -> List[Dict[str, str]]:
        """Recursively search for 'passedExams' key and return its value when found."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Case-insensitive match in case the schema changes
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
        # Some older schemas may use different key casing; use .get with default
        exam_title = exam.get("examTitle") or exam.get("ExamTitle") or ""
        exam_number = exam.get("examNumber") or exam.get("ExamNumber") or ""
        exam_date_taken = exam.get("examDateTaken") or exam.get("ExamDateTaken") or ""
        # Convert ISO datetime to date only (YYYY‑MM‑DD)
        exam_date = exam_date_taken.split("T")[0] if exam_date_taken else ""
        exams.append({
            "Exam Title": exam_title,
            "Exam Number": exam_number,
            "Exam Date": exam_date
        })
    return exams


def write_csv(exams: List[Dict[str, str]], filename: str) -> None:
    """Write a list of exam dictionaries to a CSV file.

    :param exams: List of exam info dictionaries
    :param filename: Output CSV filename
    """
    fieldnames = ["Exam Title", "Exam Number", "Exam Date"]
    with open(filename, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for exam in exams:
            writer.writerow(exam)


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(description="Extract passed exams from a Microsoft Learn public transcript.")
    parser.add_argument("share_id", help="Transcript share identifier from the URL")
    
    # Get default locale from environment variable or use en-us as fallback
    default_locale = os.environ.get("LOCALE", "en-us")
    parser.add_argument("--locale", default=default_locale, help=f"Locale to request the transcript (default: {default_locale})")
    parser.add_argument("--output", help="Output CSV filename")
    args = parser.parse_args(argv)

    # Determine output filename
    output_file = args.output or f"passed_exams_{args.share_id}.csv"

    try:
        transcript_json = fetch_transcript(args.share_id, locale=args.locale)
    except requests.HTTPError as e:
        print(f"HTTP error fetching transcript: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error decoding JSON: {e}", file=sys.stderr)
        return 1

    exams = extract_passed_exams(transcript_json)
    if not exams:
        print("No passed exams found in the transcript.", file=sys.stderr)
        return 1

    write_csv(exams, output_file)
    print(f"Wrote {len(exams)} exam records to {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
