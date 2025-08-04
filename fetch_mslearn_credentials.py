"""
Python script to fetch all credentials from the Microsoft Learn content browser API
and write the results to a CSV file.

The API returns results in pages (30 items per page by default).  Each response
includes a `@nextLink` field pointing at the next page.  This script follows
those links until there are no more pages and then writes the aggregated
results to a CSV file.  Lists in the JSON response (for example, roles,
products and exams) are converted to semicolon-separated strings in the CSV.

Note: Running this script requires network access to `learn.microsoft.com`.  If
your environment blocks outbound HTTP requests to that host, you will see
HTTP 403 errors.
"""

import csv
import json
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests


def build_initial_query() -> Tuple[str, List[Tuple[str, str]]]:
    """Constructs the initial URL and query parameters for the API request.

    Returns a tuple of `(url, params)` where `url` is the full endpoint and
    `params` is a list of key-value pairs for repeated query parameters.
    """
    base_url = "https://learn.microsoft.com"
    endpoint = "/api/contentbrowser/search/credentials"
    url = f"{base_url}{endpoint}"

    # Use OData syntax to filter by credential type.  Here we pull only
    # examination credentials.  Remove the filter if you want all credential
    # types.
    #filter_expr = "(credential_types/any(c: c eq 'examination'))"
    #filter_expr = "(credential_types/any(c: c eq 'certification'))"
    #filter_expr = "(credential_types/any(c: c eq 'applied skills'))"
    filter_expr = ""

    # Build query parameters.  Some parameters (facet) repeat and must be
    # represented as multiple tuples.
    params: List[Tuple[str, str]] = [
        ("locale", "en-us"),
        ("$filter", filter_expr),
        ("$orderBy", "title"),
        ("$top", "30"),  # request up to 30 items per page
    ]
    # Specify facets to include in the response.  These help control which
    # aggregations are returned but are not strictly required to collect
    # individual credential objects.
    facets = ["roles", "products", "levels", "subjects", "credential_types"]
    for facet in facets:
        params.append(("facet", facet))
    return url, params


def fetch_all_credentials(url: str, params: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    """Iteratively fetches all pages of credentials from the API.

    Args:
        url: The initial API URL (without query string).
        params: List of query parameter tuples to include on the first request.

    Returns:
        A list of credential dictionaries representing all pages of results.
    """
    base_url = "https://learn.microsoft.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MSLearnScraper/1.0)"
    }
    results: List[Dict[str, Any]] = []
    next_url: Optional[str] = url
    # Only include params on the very first request.  Subsequent requests use
    # the `@nextLink` URL which already contains the query string.
    first_call = True
    while next_url:
        if first_call:
            resp = requests.get(next_url, params=params, headers=headers)
            first_call = False
        else:
            resp = requests.get(next_url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("results", []))
        next_link = data.get("@nextLink")
        next_url = f"{base_url}{next_link}" if next_link else None
    return results


def flatten_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Flattens nested and list structures in a credential record.

    List values are converted to semicolon-separated strings.  Nested
    dictionaries are JSON-serialized.  Primitive types are passed through.
    """
    flat: Dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, list):
            # For lists, join simple primitives or extract nested dictionary
            # identifiers to produce a readable string.
            items: List[str] = []
            for elem in value:
                if isinstance(elem, dict):
                    # Use display_name if present, otherwise uid or the
                    # dictionary JSON representation
                    if "display_name" in elem:
                        items.append(str(elem["display_name"]))
                    elif "uid" in elem:
                        items.append(str(elem["uid"]))
                    else:
                        items.append(json.dumps(elem, ensure_ascii=False))
                else:
                    items.append(str(elem))
            flat[key] = ";".join(items)
        elif isinstance(value, dict):
            flat[key] = json.dumps(value, ensure_ascii=False)
        else:
            flat[key] = value
    return flat


def write_csv(records: Iterable[Dict[str, Any]], path: str) -> None:
    """Writes a sequence of flattened credential records to a CSV file."""
    # Flatten all records first so we know the union of all keys
    flattened = [flatten_record(rec) for rec in records]
    # Determine the union of keys across all records.  Order fields
    # alphabetically to provide a consistent header.
    fieldnames: List[str] = sorted({key for rec in flattened for key in rec.keys()})
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flattened)


def main() -> None:
    url, params = build_initial_query()
    try:
        creds = fetch_all_credentials(url, params)
    except Exception as e:
        # If network access fails (e.g., HTTP 403), print the error and exit.
        print(f"Error fetching credentials: {e}")
        return
    print(f"Fetched {len(creds)} credentials. Writing to CSV...")
    out_path = "fetched_credentials.csv"
    write_csv(creds, out_path)
    print(f"Results written to {out_path}")


if __name__ == "__main__":
    main()