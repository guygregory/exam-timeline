# July 27, 2025

<a href="https://exams.guygregory.com" target="_blank" rel="noopener noreferrer"><img width="2217" height="1503" alt="image" src="https://github.com/user-attachments/assets/708b3d1c-3e3d-48c3-aefb-74d983a85d00" /></a>


A [web application](https://exams.guygregory.com) that automatically tracks and visualizes Microsoft certification exam progress over time using data from Microsoft Learn public transcripts.

## High-Level Overview

This repository creates an automated system that:

1. **Fetches exam data daily** from Microsoft Learn public transcripts using a Python script
2. **Stores the data** in a CSV file that gets automatically updated 
3. **Visualizes the timeline** through an interactive web interface using Plotly.js
4. **Deploys automatically** to Azure Static Web Apps whenever changes are made

The result is a live, always up-to-date timeline showing certification exam achievements with minimal manual intervention.

## How It Works

### Python Script (`passed_exams.py`)

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

### Web Interface (`index.html`)

The visualization component:

- **Loads exam data** from the `passed_exams.csv` file via JavaScript fetch API
- **Parses CSV data** using a custom JavaScript parser that handles quoted fields
- **Creates interactive timeline** using Plotly.js with:
  - Chronological sorting by exam date
  - Color gradient mapping across the timeline
  - Hover tooltips showing exam details
  - Responsive design for different screen sizes
- **Handles errors gracefully** when CSV data cannot be loaded

## GitHub Actions Automation

### Daily Data Updates (`update-transcript.yml`)

This workflow automatically keeps the exam data current:

**Trigger:**
- Runs daily at midnight UTC via cron schedule: `'0 0 * * *'`
- Can also be triggered manually for testing

**Process:**
1. Checks out the repository
2. Sets up Python 3.12 environment
3. Installs required dependencies (`requests` library)
4. Runs the Python script using the `TRANSCRIPT_CODE` repository secret:
   ```bash
   python passed_exams.py "${{ secrets.TRANSCRIPT_CODE }}" \
     --locale en-gb --output passed_exams.csv
   ```
5. Commits and pushes any changes to `passed_exams.csv`

**Repository Secret Required:**
- `TRANSCRIPT_CODE`: The Microsoft Learn transcript share ID
- This secret is stored as a repository secret for easy access across workflows

**Permissions:**
- `contents: write` - Allows pushing changes back to the repository
- `actions: read` - Standard workflow permission

### Azure Static Web Apps Deployment

This workflow automatically deploys the website:

**Triggers:**
- Every push to the `main` branch
- Pull request events (opened, synchronized, reopened, closed)

**Deployment Process:**
1. Checks out the repository with submodules
2. Uses Azure Static Web Apps Deploy action
3. Authenticates using the repository secret, automatically configured by the Azure Static Web App
4. Deploys from root directory (`app_location: "/"`) 
5. No build process required since it's a static site (`output_location: "."`)

The workflow also handles pull request cleanup by closing the associated preview environment when PRs are closed.

## Setup Instructions

### Prerequisites

- Python 3.12+ with `requests` library
- Azure Static Web Apps resource
- GitHub repository with Actions enabled

### Configuration

**Find Your Transcript Share ID:**
   - Go to your Microsoft Learn profile
   - Navigate to your public transcript
   - Copy the share ID from the URL (the part after `/transcript/`)

**Fork this repo into your own GitHub acccount**
   - Brings across index.html, passed-exams.py, and GitHub Actions definitions
   - Also includes passed-exams.csv, but this will be overwritten on by the GitHub Action

**Set up Repository Secrets:**
   - Navigate to your GitHub repository → Settings → Secrets and variables → Actions
   - Add repository secret: `TRANSCRIPT_CODE` with your Microsoft Learn transcript share ID

**Azure Static Web Apps Setup:**
   - Create an Azure Static Web App resource (Free tier should be fine)
   - Connect it to your GitHub repository (see below for details, login required)
   - Deployment token should be automatically added to your repo secrets
   - (Optional) Add a custom domain

<img width="746" height="1002" alt="image" src="https://github.com/user-attachments/assets/5686491a-a54c-468b-abf4-4332a8437748" />


### Local Development

To test locally:

1. **Install dependencies:**
   ```bash
   pip install requests
   ```

2. **Run the Python script:**
   ```bash
   python passed_exams.py YOUR_SHARE_ID --output passed_exams.csv
   ```

3. **Serve the website locally:**
   ```bash
   python -m http.server 8000
   ```
   
4. **Open in browser:**
   ```
   http://localhost:8000
   ```

## File Structure

```
exam-timeline/
├── .github/workflows/
│   ├── update-transcript.yml          # Daily data update automation
│   └── azure-static-web-apps-*.yml    # Azure deployment automation
├── index.html                         # Web interface with timeline visualization
├── passed_exams.csv                   # Exam data (auto-updated)
├── passed_exams.py                    # Python script for data fetching
├── .gitignore                         # Git ignore patterns
└── README.md                          # This file
```

## Dependencies

**Python:**
- `requests` - For HTTP API calls to Microsoft Learn
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
