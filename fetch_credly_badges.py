#!/usr/bin/env python3
"""
Script to fetch Credly digital badges and convert to CSV format.

Usage:
    python fetch_credly_badges.py <username> [--output <output.csv>]

Example:
    python fetch_credly_badges.py guygregory --output credly_badges.csv

If no output filename is provided, the script writes to credly_badges_<username>.csv.

The script makes a GET request to the Credly API endpoint:
https://www.credly.com/users/<username>/badges.json

The API returns JSON containing a `data` array with badge details. The script
writes a CSV file containing the badge title, issuer and the date issued.

Note: Internet access is required for this script to work. The API endpoint is
publicly accessible for public badges.

To test locally, you can start a local web server `python -m http.server 8000` and then open using `http://localhost:8000`.
"""
import argparse
import csv
import os
import sys
from typing import List, Dict
import requests


API_ENDPOINT_TEMPLATE = "https://www.credly.com/users/{username}/badges.json"


def fetch_badges(username: str) -> Dict:
    """Fetch badges JSON from the Credly public API.

    :param username: The Credly username
    :return: Parsed JSON response
    :raises requests.HTTPError: if the HTTP request returned an unsuccessful status code
    :raises ValueError: if the response cannot be decoded as JSON
    """
    url = API_ENDPOINT_TEMPLATE.format(username=username)
    headers = {
        # Provide a User‑Agent to avoid potential filtering of generic requests
        "User-Agent": "Mozilla/5.0 (compatible; CredlyBadgeFetcher/1.0)"
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
    raw_badges = badges_json.get("data", [])
    badges: List[Dict[str, str]] = []
    
    for badge in raw_badges:
        # Extract badge information
        badge_title = badge.get("badge_template", {}).get("name", "")
        
        # Get issuer name - try different locations in the JSON
        issuer_name = ""
        issuer = badge.get("issuer", {})
        if isinstance(issuer, dict):
            # Try issuer.summary first
            issuer_name = issuer.get("summary", "")
            if not issuer_name:
                # Try issuer.entities[0].entity.name
                entities = issuer.get("entities", [])
                if entities and len(entities) > 0:
                    entity = entities[0].get("entity", {})
                    issuer_name = entity.get("name", "")
        
        # Clean up issuer name (remove "issued by" prefix if present)
        if issuer_name.lower().startswith("issued by "):
            issuer_name = issuer_name[10:]  # Remove "issued by " prefix
        
        # Get issue date
        issued_date = badge.get("issued_at_date", "")
        
        badges.append({
            "Badge Title": badge_title,
            "Issuer": issuer_name,
            "Issue Date": issued_date
        })
    
    return badges


def write_csv(badges: List[Dict[str, str]], filename: str) -> None:
    """Write a list of badge dictionaries to a CSV file.

    :param badges: List of badge info dictionaries
    :param filename: Output CSV filename
    """
    fieldnames = ["Badge Title", "Issuer", "Issue Date"]
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
        badges_json = fetch_badges(args.username)
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