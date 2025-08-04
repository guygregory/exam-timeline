<a href="https://exams.guygregory.com"><img width="2217" height="1503" alt="image" src="https://github.com/user-attachments/assets/3aef88b7-aa2e-4d25-9d3b-b0d76bdd7766" /></a>




A [web application](https://exams.guygregory.com) that automatically tracks and visualizes certification progress over time using data from Microsoft Learn public transcripts and Credly digital badges.

<img width="411" height="143" alt="image" src="https://github.com/user-attachments/assets/cc54bb0e-6c02-4177-b93f-d6b552b275dd" />


## High-Level Overview

This repository creates an automated system that:

1. **Fetches exam and badge data daily** from Microsoft Learn public transcripts and Credly public profiles using Python scripts
2. **Stores the data** in CSV files that get automatically updated 
3. **Generates AI-powered exam recommendations** using OpenAI's gpt-4o model to suggest the next logical certification based on the learner's progress
4. **Visualizes the timeline** through an interactive web interface using Plotly.js with intelligent data source selection
5. **Deploys automatically** to Azure Static Web Apps whenever changes are made

The result is a live, always up-to-date timeline showing certification achievements from multiple sources (Microsoft exams, Credly badges, or both) with AI-powered recommendations for next steps, all with minimal manual intervention. The dashboard intelligently displays only the data sources where information is available.

## How It Works

### Python Script (`passed_exams.py`)

> Disclaimer: The use of the Microsoft Learn API in this way is **not officially supported or documented**, and while suitable for a simple hobby project, is **not appropriate for a production application**. Future API availability is not guaranteed. For commercial integrations, please contact your Microsoft representative.

The core functionality is powered by a Python script that:

- **Fetches transcript data** from Microsoft Learn's public API endpoint:
  ```
  https://learn.microsoft.com/api/profiles/transcript/share/{share_id}?locale={locale}
  ```

- **Extracts exam information** by searching the JSON response for a `passedExams` array, which contains:
  - Exam title
  - Exam number  
  - Date taken

- **Outputs to CSV format** with columns: `Exam Title`, `Exam Number`, `Exam Date`

- **Handles various data formats** robustly by searching recursively through the JSON structure and accommodating different key casings

#### Usage
```bash
python passed_exams.py <share_id> [--locale <locale>] [--output <output.csv>]
```

**Example:**
```bash
python passed_exams.py d8yjji6kmml5jg0 --locale en-gb --output passed_exams.csv
```

The `share_id` is the identifier from the end of a Microsoft Learn public transcript URL:
```
https://learn.microsoft.com/en-gb/users/<username>/transcript/<share_id>
```

### Credly Badge Script (`fetch_credly_badges.py`)

The Credly integration is powered by a Python script that:

- **Fetches badge data** from Credly's public API endpoint:
  ```
  https://www.credly.com/users/{username}/badges.json
  ```

- **Extracts badge information** by parsing the JSON response for badge details including:
  - Badge title
  - Issuer name
  - Date earned

- **Outputs to CSV format** with columns: `Badge Title`, `Issuer`, `Badge Date`

- **Handles API responses robustly** by navigating the nested JSON structure and converting dates to consistent format

#### Usage
```bash
python fetch_credly_badges.py <username> [--output <output.csv>]
```

**Example:**
```bash
python fetch_credly_badges.py guygregory --output credly_badges.csv
```

The `username` can be found by logging into Credly and taking the last part of your profile URL:
```
https://www.credly.com/users/guygregory → username is "guygregory"
```

### AI Exam Recommender (`ai_exam_recommender.py`)

The AI recommendation system suggests the next logical Microsoft exam based on the learner's transcript:

- **Analyzes transcript data** from the `passed_exams.csv` file to understand the learner's certification journey
- **Uses OpenAI's gpt-4o model** hosted by GitHub Models (on Azure AI) for intelligent recommendations
- **Leverages structured outputs** with enum type constraints to ensure recommendations come only from the [prioritized exam list](priority_ARB_exams.csv)
- **Avoids duplicate recommendations** by ensuring the suggested exam is not already completed
- **Outputs JSON format** with the recommendation: `{"exam_code":"AZ-305"}`
- **Updates the dashboard** by writing the result to `partials/ai-recommendation.html` for display

The system prompt guides the AI to consider recent exams, current technology trends, and logical progression paths when making recommendations. Authentication works seamlessly through GitHub Actions with the `models: read` permission, utilizing the free quota included with GitHub Copilot plans.

### Web Interface (`index.html`)

The visualization component:

- **Loads data from multiple sources** including `passed_exams.csv` and `credly_badges.csv` via JavaScript fetch API
- **Intelligently selects data sources** by checking data availability and:
  - Shows a dropdown to switch between Microsoft exams and Credly badges when both are available
  - Automatically displays Microsoft exams when only exam data is available
  - Automatically displays Credly badges when only badge data is available
  - Gracefully handles cases where no data is available
- **Parses CSV data** using a custom JavaScript parser that handles quoted fields
- **Creates interactive timeline** using Plotly.js with:
  - Chronological sorting by date
  - Color gradient mapping across the timeline
  - Hover tooltips showing details (exam/badge information)
  - Responsive design for different screen sizes
- **Handles errors gracefully** when CSV data cannot be loaded

## GitHub Actions Automation

### Daily Data Updates (`update-transcript.yml`)

This workflow automatically keeps both exam and badge data current:

**Trigger:**
- Runs daily at midnight UTC via cron schedule: `'0 0 * * *'`
- Can also be triggered manually for testing

**Process:**
1. Checks out the repository
2. Sets up Python 3.12 environment
3. Installs required dependencies (`requests` library)
4. Runs the Microsoft Learn script using the `TRANSCRIPT_CODE` repository secret:
   ```bash
   python passed_exams.py "${{ secrets.TRANSCRIPT_CODE }}" \
     --locale en-gb --output passed_exams.csv
   ```
5. Runs the Credly script using the `CREDLY_USERNAME` repository secret:
   ```bash
   python fetch_credly_badges.py "${{ secrets.CREDLY_USERNAME }}" \
     --output credly_badges.csv
   ```
6. Generates an AI exam recommendation using the transcript data:
   ```bash
   python ai_exam_recommender.py
   ```
7. Commits and pushes any changes to `passed_exams.csv`, `credly_badges.csv`, and `partials/ai-recommendation.html`

**Repository Secrets Required:**
- `TRANSCRIPT_CODE`: The Microsoft Learn transcript share ID
- `CREDLY_USERNAME`: Your Credly username (found in your Credly profile URL)
- Both secrets are stored as repository secrets for easy access across workflows

**Permissions:**
- `contents: write` - Allows pushing changes back to the repository
- `actions: read` - Standard workflow permission
- `models: read` - Enables access to GitHub Models for AI recommendations

### Azure Static Web Apps Deployment

This workflow automatically deploys the website:

**Triggers:**
- Every push to the `main` branch
- Pull request events (opened, synchronized, reopened, closed)

**Deployment Process:**
1. Checks out the repository with submodules
2. Sets up Node.js and installs npm dependencies (plotly.js-dist-min)
3. Uses Azure Static Web Apps Deploy action
4. Authenticates using the repository secret, automatically configured by the Azure Static Web App
5. Deploys from root directory (`app_location: "/"`) with build artifacts (`output_location: "."`)

The workflow also handles pull request cleanup by closing the associated preview environment when PRs are closed.

## Setup Instructions

### Prerequisites

- Python 3.12+ with `requests` library
- Node.js 18+ with npm (for local development)
- Azure Static Web Apps resource
- GitHub repository with Actions enabled

### Configuration

**Find Your Microsoft Learn Transcript Share ID:**
   - Go to your Microsoft Learn profile
   - Navigate to your public transcript
   - Copy the share ID from the URL (the part after `/transcript/`)

**Find Your Credly Username:**
   - Log into Credly
   - Go to your profile page
   - Copy the username from the URL (e.g., `https://www.credly.com/users/guygregory` → username is `guygregory`)

**Fork this repo into your own GitHub account**
   - Brings across index.html, Python scripts, and GitHub Actions definitions
   - Also includes CSV data files, but these will be overwritten by the GitHub Action

**Set up Repository Secrets:**
   - Navigate to your GitHub repository → Settings → Secrets and variables → Actions
   - Add repository secret: `TRANSCRIPT_CODE` with your Microsoft Learn transcript share ID
   - Add repository secret: `CREDLY_USERNAME` with your Credly username
   - Note: Both secrets are optional - the system will work with just one data source if only one secret is provided

<img width="1125" height="813" alt="image" src="https://github.com/user-attachments/assets/43188a0e-2ca3-491d-b3b7-44f27933cc09" />


**Azure Static Web Apps Setup:**
   - Create an Azure Static Web App resource (Free tier should be fine)
   - Connect it to your GitHub repository (see below for details, login required)
   - Deployment token should be automatically added to your repo secrets
   - (Optional) Add a custom domain

<img width="746" height="1002" alt="image" src="https://github.com/user-attachments/assets/5686491a-a54c-468b-abf4-4332a8437748" />


### Local Development

To test locally:

1. **Install Python dependencies:**
   ```bash
   pip install requests openai
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Run the Python scripts:**
   ```bash
   # Fetch Microsoft Learn exam data
   python passed_exams.py YOUR_SHARE_ID --output passed_exams.csv
   
   # Fetch Credly badge data
   python fetch_credly_badges.py YOUR_CREDLY_USERNAME --output credly_badges.csv
   ```

4. **Serve the website locally:**
   ```bash
   python -m http.server 8000
   ```
   
5. **Open in browser:**
   ```
   http://localhost:8000
   ```

## File Structure

```
exam-timeline/
├── .github/workflows/
│   ├── update-transcript.yml          # Daily data update automation
│   └── azure-static-web-apps-*.yml    # Azure deployment automation
├── partials/
│   ├── ai-recommendation.html         # AI exam recommendation output
│   └── last-updated.html              # Last update timestamp
├── index.html                         # Web interface with timeline visualization
├── package.json                       # Node.js dependencies (plotly.js)
├── passed_exams.csv                   # Microsoft exam data (auto-updated)
├── passed_exams.py                    # Python script for Microsoft Learn data fetching
├── credly_badges.csv                  # Credly badge data (auto-updated)
├── fetch_credly_badges.py             # Python script for Credly data fetching
├── ai_exam_recommender.py             # Python script for AI exam recommendations
├── priority_ARB_exams.csv             # Prioritized exam list for AI recommendations
├── plotly.min.js                      # Plotly.js library (fallback)
├── .gitignore                         # Git ignore patterns
└── README.md                          # This file
```

## Dependencies

**Python:**
- `requests` - For HTTP API calls to Microsoft Learn and Credly
- `openai` - For AI exam recommendations using GitHub Models
- `csv` - For CSV file operations (built-in)
- `argparse` - For command-line interface (built-in)

**Web Interface:**
- `plotly.js` (v3.0.1) - For interactive timeline visualization
- Vanilla JavaScript - No additional frameworks required

**GitHub Actions:**
- `actions/checkout@v4` - Repository checkout
- `actions/setup-python@v4` - Python environment setup  
- `Azure/static-web-apps-deploy@v1` - Azure deployment

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally using the development setup
5. Submit a pull request

The automated workflows will handle testing and deployment of your changes.
