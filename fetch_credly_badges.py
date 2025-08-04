#!/usr/bin/env python3
"""
Script to fetch Credly digital badges and convert to CSV format.

Usage:
    python fetch_credly_badges.py <username> [--output <output.csv>]

Example:
    python fetch_credly_badges.py guygregory --output credly_badges.csv

If no output filename is provided, the script writes to credly_badges_<username>.csv.

The script makes a GET request to the Credly badges API endpoint:
https://www.credly.com/users/<username>/badges.json

The API returns JSON containing a `data` array with badge details. The script
writes a CSV file containing the badge title, issuer, and the date earned.

Note: Internet access is required for this script to work. The API endpoint is
public but may require appropriate headers to avoid rate limiting.
"""
import argparse
import csv
import os
import sys
from typing import List, Dict
import requests
from datetime import datetime

API_ENDPOINT_TEMPLATE = "https://www.credly.com/users/{username}/badges.json"


def fetch_credly_badges(username: str) -> Dict:
    """Fetch Credly badges JSON from the public API.

    :param username: The Credly username
    :return: Parsed JSON response
    :raises requests.HTTPError: if the HTTP request returned an unsuccessful status code
    :raises ValueError: if the response cannot be decoded as JSON
    """
    url = API_ENDPOINT_TEMPLATE.format(username=username)
    headers = {
        # Provide a User-Agent to avoid potential filtering of generic requests
        "User-Agent": "Mozilla/5.0 (compatible; CredlyBadgeFetcher/1.0)",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def extract_badges(badges_json: Dict) -> List[Dict[str, str]]:
    """
    Extract a list of badges from the Credly JSON.

    :param badges_json: Badges JSON as returned by the API
    :return: List of dictionaries with badge title, issuer and date
    """
    badges: List[Dict[str, str]] = []
    
    # Credly API typically returns badges in a 'data' array
    raw_badges = badges_json.get('data', [])
    
    for badge in raw_badges:
        # Extract badge information
        badge_name = badge.get('badge_template', {}).get('name', '')
        
        # Extract issuer name from the correct location in the JSON structure
        issuer_entities = badge.get('issuer', {}).get('entities', [])
        issuer_name = ''
        if issuer_entities:
            # Get the first entity's name (typically the primary issuer)
            issuer_name = issuer_entities[0].get('entity', {}).get('name', '')
        
        # Extract earned date - Credly typically uses 'issued_at' or 'earned_at'
        issued_at = badge.get('issued_at', '') or badge.get('earned_at', '')
        
        # Convert ISO datetime to date only (YYYY-MM-DD)
        badge_date = ""
        if issued_at:
            try:
                # Parse ISO datetime and extract date
                dt = datetime.fromisoformat(issued_at.replace('Z', '+00:00'))
                badge_date = dt.strftime('%Y-%m-%d')
            except (ValueError, AttributeError):
                # If parsing fails, try to extract date part directly
                badge_date = issued_at.split("T")[0] if "T" in issued_at else issued_at
        
        if badge_name:  # Only add badges with valid names
            badges.append({
                "Badge Title": badge_name,
                "Issuer": issuer_name,
                "Badge Date": badge_date
            })
    
    return badges


def write_csv(badges: List[Dict[str, str]], filename: str) -> None:
    """Write a list of badge dictionaries to a CSV file.

    :param badges: List of badge info dictionaries
    :param filename: Output CSV filename
    """
    fieldnames = ["Badge Title", "Issuer", "Badge Date"]
    with open(filename, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for badge in badges:
            writer.writerow(badge)


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(description="Extract badges from a Credly public profile.")
    parser.add_argument("username", help="Credly username")
    parser.add_argument("--output", help="Output CSV filename")
    args = parser.parse_args(argv)

    # Determine output filename
    output_file = args.output or f"credly_badges_{args.username}.csv"

    try:
        badges_json = fetch_credly_badges(args.username)
    except requests.HTTPError as e:
        print(f"HTTP error fetching badges: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error decoding JSON: {e}", file=sys.stderr)
        return 1

    badges = extract_badges(badges_json)
    if not badges:
        print("No badges found in the profile.", file=sys.stderr)
        return 1

    write_csv(badges, output_file)
    print(f"Wrote {len(badges)} badge records to {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())