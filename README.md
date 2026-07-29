# Employee Onboarding Automation Agent

A complete Streamlit prototype for Business Analyst onboarding.

## Included

- Employee profile management
- 30-day onboarding milestones
- Weighted onboarding score
- SQLite persistence
- Ticket creation and status history
- Employee and admin ticket views
- Sentiment analysis
- Optional Gemini response generation
- Offline TF-IDF retrieval
- 37 separate policy JSON files

## Policy folders

```text
policies/
├── hr/
├── business_analysis/
├── security/
├── data_governance/
├── learning/
├── workplace/
└── policy_index.json
```

## Run

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## Optional Gemini

```powershell
$env:GEMINI_API_KEY="your-api-key"
python -m streamlit run app.py
```

The application works without Gemini.

## Reset the database

```powershell
Remove-Item .\onboarding.db
```

Restart the app to recreate the database and demo employee.
