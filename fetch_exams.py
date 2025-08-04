import requests
import json

# Endpoint with a query parameter to return only exams
url = "https://learn.microsoft.com/api/catalog/?type=exams&locale=en-us"

# Add a user-agent header (many Microsoft endpoints require one)
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(url, headers=headers)
response.raise_for_status()  # Raise an error if the request failed

catalog = response.json()


# Remove retired exams from the catalog
retired_exams = {
    '70-333','70-334','70-339','70-345','70-357','70-410','70-411','70-412','70-413','70-414','70-417','70-461',
    '70-462','70-463','70-464','70-465','70-466','70-467','70-480','70-483','70-486','70-487','70-537','70-705',
    '70-740','70-741','70-742','70-743','70-744','70-745','70-761','70-762','70-764','70-765','70-767','70-768',
    '70-777','70-778','70-779','70-797','77-601','77-602','77-881','77-882','77-883','77-884','77-885','77-887',
    '77-888','98-349','98-361','98-364','98-365','98-366','98-367','98-368','98-375','98-381','98-382','98-383',
    '98-388','AI-100','AZ-100','AZ-101','AZ-102','AZ-103','AZ-200','AZ-201','AZ-202','AZ-203','AZ-220','AZ-300',
    'AZ-301','AZ-302','AZ-303','AZ-304','AZ-600','AZ-720','DA-100','DP-200','DP-201','MB-200','MB-210','MB-220',
    'MB-300','MB-320','MB-340','MB-400','MB-600','MB-900','MB-901','MB2-716','MB6-894','MB6-897','MB6-898','MD-100',
    'MD-101','MS-100','MS-101','MS-200','MS-201','MS-202','MS-203','MS-220','MS-300','MS-301','MS-302','MS-500',
    'MS-600','MS-720','MS-740', 'DU-mmy'
}

# Exclude exams starting with specified prefixes
prefixes = ("MB6", "98", "77", "MO")
catalog['exams'] = [
    exam for exam in catalog.get("exams", [])
    if exam.get("display_name") not in retired_exams
       and not any(exam.get("display_name", "").startswith(p) for p in prefixes)
]

# Print only the code (display_name), title and levels for each exam
for exam in catalog.get("exams", []):
    code = exam.get("display_name")
    title = exam.get("title")
    level = ", ".join(exam.get("levels", []))  # levels is a list
    print(f"{code} | {title} | {level}")