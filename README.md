# QA Agent - AI-Powered Test Case Generator

An automated test case generation system that creates comprehensive test cases from user stories using Azure OpenAI and syncs them to TestRail.

## Overview

This application generates test cases from user stories and JIRA tickets using Azure OpenAI GPT-4.1 It exports test cases to Excel and automatically syncs them to TestRail using a file watcher service.

## Features

- AI-powered test case generation from user stories
- Automatic extraction of features from documentation
- Excel export with metadata and TestRail sync columns
- Automated TestRail synchronization via file watcher
- Rate-limited API calls with retry logic
- Docker containerization for production deployment

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for containerized deployment)
- Azure OpenAI API access
- TestRail instance with API enabled

## Configuration

Create a `.env` file with the following variables:

```env
# Azure OpenAI
AZURE_INFERENCE_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_INFERENCE_CREDENTIAL=your-api-key
AZURE_DEPLOYMENT_NAME=gpt-4.1

# TestRail
TESTRAIL_URL=https://your-instance.testrail.io
TESTRAIL_USERNAME=your-email@company.com
TESTRAIL_API_KEY=your-api-key
```

### Documentation Paths

Configure paths to your product and feature documentation:

- Product documentation: Place PDF files in `Related_docs/` folder (absolute path: `/path/to/qa-agent/Related_docs`)
- Feature documentation: Use the folder containing your release notes and feature PDFs (e.g., `MR-releaseNotes/`)

The application expects:
- Absolute paths to folders containing PDF documentation files
- Read access to these directories for document processing and feature extraction

## Running with Docker

### Setup Documentation Access

Docker containers can only access files that are either copied into the image or mounted as volumes. Choose one option:

**Option 1: Copy Files to Mounted Directories (Recommended)**

Copy your documentation files to the `Related_docs/` folder:
- Product documentation: `Related_docs/product.pdf`
- Feature documentation: `Related_docs/Features/`

In the Streamlit UI, use relative paths: `Related_docs/product.pdf`

**Option 2: Add Volume Mounts**

Edit `docker-compose.yml` to mount your documentation directories:

```yaml
volumes:
  - ./test_cases_output:/app/test_cases_output
  - ./Related_docs:/app/Related_docs
  - C:/path/to/your/docs:/app/CustomDocs:ro
```

In the Streamlit UI, use container paths: `/app/CustomDocs/product.pdf`

### Start Services

1. Configure environment variables in `.env` file
2. Start the services:

```bash
docker-compose up -d
```

3. Access the application at http://localhost:8501

The Docker deployment includes:
- `qa-agent-app`: Streamlit UI for test case generation (port 8501)
- `qa-agent-watcher`: File watcher service for automatic TestRail sync

To stop the services:

```bash
docker-compose down
```

View logs:

```bash
docker-compose logs -f
docker-compose logs qa-agent-app
docker-compose logs qa-agent-watcher
```

## Running without Docker

1. Create and activate a virtual environment:

```bash
python -m venv qa-ag
.\env\Scripts\Activate  # Windows
source env/bin/activate  # Linux/Mac
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the Streamlit application:

```bash
streamlit run app/st.py
```

4. In a separate terminal, start the file watcher service:

```bash
python -m services.file_watcher
```

The application will be available at http://localhost:8501

## Usage

### Generate Test Cases

1. Open the web interface at http://localhost:8501
2. Select a TestRail project from the dropdown
3. Enter or paste your user story
4. Click "Generate Test Cases"
5. Test cases are saved to `test_cases_output/` as Excel files

### Sync to TestRail

#### Automatic Sync

Move the Excel file to the `reviewed/` folder:

```bash
Move-Item test_cases_output/your_file.xlsx test_cases_output/reviewed/
```

The file watcher will automatically:
- Detect the new file
- Sync test cases to TestRail
- Update the Excel file with TestRail IDs and URLs
- Move the file to `processed/` folder

#### Manual Sync

```bash
python manual_sync.py test_cases_output/your_file.xlsx
```

## Project Structure

```
qa-agent/
├── app/                       # Streamlit application
│   ├── st.py                 # Main UI
│   └── test_case_exporter.py # Excel export
├── llm/                      # Azure OpenAI integration
│   ├── connector.py          # API client
│   └── prompt.py             # Prompt templates
├── integrations/             # TestRail integration
│   ├── testrail_client.py    # API client
│   └── testrail_mapper.py    # Data mapping
├── services/                 # Background services
│   ├── file_watcher.py       # Auto-sync service
│   └── sync_service.py       # TestRail sync logic
├── test_cases_output/        # Generated test cases
│   ├── reviewed/             # Files to sync
│   ├── processed/            # Successfully synced
│   └── errors/               # Failed syncs
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Troubleshooting

**Test cases not generating**
- Verify Azure OpenAI credentials in `.env`
- Check API endpoint accessibility
- Review application logs

**TestRail sync failing**
- Verify TestRail URL and credentials
- Ensure Project_ID is set in Excel metadata sheet
- Check API key permissions
- Review file watcher logs

**File watcher not detecting files**
- Ensure file is in `test_cases_output/reviewed/` folder
- Verify file format is `.xlsx`
- Check file is not locked by another process
- Review Docker logs: `docker-compose logs qa-agent-watcher`