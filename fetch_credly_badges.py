import requests
import json
import csv
from datetime import datetime

def fetch_credly_badges(username):
    """
    Fetch Credly badges for a given username and convert to CSV format
    similar to the Microsoft exams structure
    """
    url = f"https://www.credly.com/users/{username}/badges.json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        badges = []
        for badge in data.get('data', []):
            # Extract relevant information
            badge_info = {
                'Badge Title': badge.get('badge_template', {}).get('name', 'Unknown Badge'),
                'Badge ID': badge.get('id', ''),
                'Issue Date': badge.get('issued_at_date', ''),
                'Issuer': get_primary_issuer(badge.get('issuer', {}))
            }
            badges.append(badge_info)
        
        return badges
        
    except requests.RequestException as e:
        print(f"Error fetching Credly badges: {e}")
        return []

def get_primary_issuer(issuer_data):
    """Extract the primary issuer name from the issuer data structure"""
    entities = issuer_data.get('entities', [])
    for entity in entities:
        if entity.get('primary', False):
            return entity.get('entity', {}).get('name', 'Unknown Issuer')
    
    # Fallback: get first entity if no primary found
    if entities:
        return entities[0].get('entity', {}).get('name', 'Unknown Issuer')
    
    return 'Unknown Issuer'

def save_badges_to_csv(badges, filename='credly_badges.csv'):
    """Save badges to CSV file in the same format as Microsoft exams"""
    if not badges:
        print("No badges to save")
        return
        
    # Sort badges by date (newest first, like the exam data)
    badges.sort(key=lambda x: datetime.strptime(x['Issue Date'], '%Y-%m-%d') if x['Issue Date'] else datetime.min, reverse=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Badge Title', 'Badge ID', 'Issue Date', 'Issuer']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for badge in badges:
            # Use similar format to exams CSV: Title, Number/ID, Date, plus Issuer
            writer.writerow({
                'Badge Title': badge['Badge Title'],
                'Badge ID': badge['Badge ID'][:8] + '...' if len(badge['Badge ID']) > 8 else badge['Badge ID'],  # Truncate long IDs
                'Issue Date': badge['Issue Date'],
                'Issuer': badge['Issuer']
            })
    
    print(f"Saved {len(badges)} badges to {filename}")

def main():
    # Default username - can be changed or made configurable
    username = "guygregory"  # From the issue example
    
    print(f"Fetching Credly badges for user: {username}")
    badges = fetch_credly_badges(username)
    
    if badges:
        save_badges_to_csv(badges)
        print(f"Successfully processed {len(badges)} badges")
        
        # Print summary statistics
        issuers = {}
        years = set()
        
        for badge in badges:
            issuer = badge['Issuer']
            issuers[issuer] = issuers.get(issuer, 0) + 1
            
            if badge['Issue Date']:
                year = datetime.strptime(badge['Issue Date'], '%Y-%m-%d').year
                years.add(year)
        
        print(f"\nSummary:")
        print(f"Total badges: {len(badges)}")
        print(f"Years of achievement: {len(years)}")
        print(f"Latest badge: {badges[0]['Badge Title'] if badges else 'None'}")
        print(f"Top issuer: {max(issuers.items(), key=lambda x: x[1])[0] if issuers else 'None'}")
        
    else:
        print("No badges found or error occurred")

if __name__ == "__main__":
    main()