# AI Recruiter Agent

An intelligent multi-agent system that automates the initial recruitment process using AI and various APIs.

## Features

- Job description analysis
- CV matching and ranking
- Automated WhatsApp communication
- Interview scheduling
- Calendar integration

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following variables:
```
OPENROUTER_API_KEY=your_openrouter_api_key
WHATSAPP_TOKEN=your_whatsapp_token
GOOGLE_CALENDAR_CREDENTIALS=path_to_credentials.json
```

4. Run the application:
```bash
uvicorn main:app --reload
```

## Project Structure

- `main.py`: FastAPI application entry point
- `agents/`: Contains different agent implementations
  - `cv_matcher.py`: CV analysis and matching agent
  - `whatsapp_agent.py`: WhatsApp communication agent
  - `scheduler_agent.py`: Interview scheduling agent
- `utils/`: Utility functions and helpers
- `config.py`: Configuration settings
- `models.py`: Data models and schemas

## Usage

1. Submit a job description through the API
2. The system will:
   - Analyze and match CVs
   - Contact top candidates via WhatsApp
   - Schedule interviews based on availability
   - Send confirmation messages 