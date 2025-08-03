#!/usr/bin/env python3
"""
Script to fetch Credly digital badges from a public profile and extract badge information.

Usage:
    python fetch_credly_badges.py <username> [--output <output.csv>]

Example:
    python fetch_credly_badges.py guygregory --output credly_badges.csv

If no output filename is provided, the script writes to credly_badges_<username>.csv.

The script makes a GET request to the Credly API endpoint:
https://www.credly.com/users/<username>/badges.json

The API returns JSON containing a `data` array with badge details. The script
writes a CSV file containing the badge name, issuer, and the date issued.

Note: Internet access is required for this script to work. The API endpoint is
unauthenticated for public profiles.

To test locally, you can start a local web server `python -m http.server 8000` and then open using `http://localhost:8000`.
"""
import argparse
import csv
import sys
from typing import List, Dict
import requests
from collections import Counter

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
    :return: List of dictionaries with badge name, issuer and date
    """
    raw_badges = badges_json.get('data', [])
    badges: List[Dict[str, str]] = []
    
    for badge in raw_badges:
        # Extract badge details
        badge_name = badge.get('badge_template', {}).get('name', '')
        issued_date = badge.get('issued_at_date', '')
        
        # Extract issuer name - it's in the issuer.entities array
        issuer_name = ''
        issuer_info = badge.get('issuer', {})
        entities = issuer_info.get('entities', [])
        if entities:
            # Get the primary entity (usually the first one marked as primary)
            for entity in entities:
                if entity.get('primary', False):
                    issuer_name = entity.get('entity', {}).get('name', '')
                    break
            # If no primary entity found, use the first one
            if not issuer_name and entities:
                issuer_name = entities[0].get('entity', {}).get('name', '')
        
        badges.append({
            "Badge Name": badge_name,
            "Issuer": issuer_name,
            "Issue Date": issued_date
        })
    
    return badges


def write_csv(badges: List[Dict[str, str]], filename: str) -> None:
    """Write a list of badge dictionaries to a CSV file.

    :param badges: List of badge info dictionaries
    :param filename: Output CSV filename
    """
    fieldnames = ["Badge Name", "Issuer", "Issue Date"]
    with open(filename, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for badge in badges:
            writer.writerow(badge)


def print_stats(badges: List[Dict[str, str]]) -> None:
    """Print statistics about the badges.
    
    :param badges: List of badge info dictionaries
    """
    if not badges:
        print("No badges found.")
        return
    
    total_badges = len(badges)
    
    # Calculate years of achievement
    dates = [badge['Issue Date'] for badge in badges if badge['Issue Date']]
    if dates:
        years = {date.split('-')[0] for date in dates}
        years_of_achievement = len(years)
        
        # Find latest badge
        latest_date = max(dates)
        latest_badge = next(badge for badge in badges if badge['Issue Date'] == latest_date)
        
        # Find top issuer
        issuers = [badge['Issuer'] for badge in badges if badge['Issuer']]
        if issuers:
            issuer_counts = Counter(issuers)
            top_issuer = issuer_counts.most_common(1)[0][0]
        else:
            top_issuer = "Unknown"
    else:
        years_of_achievement = 0
        latest_badge = {"Badge Name": "Unknown", "Issuer": "Unknown"}
        top_issuer = "Unknown"
    
    print(f"\n📊 Badge Statistics:")
    print(f"Total Badges Earned: {total_badges}")
    print(f"Years of Achievement: {years_of_achievement}")
    print(f"Latest Issuer: {latest_badge['Issuer']}")
    print(f"Top Issuer: {top_issuer}")


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
    
    # Print statistics
    print_stats(badges)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())