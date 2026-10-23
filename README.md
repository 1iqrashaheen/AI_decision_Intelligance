# AI Business Assistant

This module is part of the AI Decision Intelligence project.

It uses the Groq API to answer business questions using sales data, analysis results, what-if simulations, forecasts, and recommendations.

## Setup

1. Clone or download the project.
2. Open the project folder in VS Code.
3. Create a Python virtual environment:

   python -m venv .venv

4. Activate the environment on Windows:

   .\.venv\Scripts\Activate.ps1

5. Install the libraries:

   pip install -r requirements.txt

## Groq API Key

Groq offers a free API tier with usage limits.

1. Visit https://console.groq.com/
2. Create a free account.
3. Open the API Keys section.
4. Generate your own API key.
5. Create a `.env` file in the project folder and add:

   GROQ_API_KEY=your_api_key_here

Replace the example value with your own key. Do not upload the `.env` file to GitHub.

## Run the Assistant

For testing with the Online Retail II dataset, place the Excel file inside the `data` folder.

Run:

python assistant/ai_assistant.py

## Test Module Integration

To test the assistant with sample results instead of the retail dataset, run:

python assistant/test_assistant.py

## Backend Integration

The main backend can use:

- `ask_assistant()` from `ai_assistant.py`
- `prepare_business_data()` from `data_connection.py`

These functions allow the assistant to receive business information from other project modules.

The sample dataset will be replaced with the cleaned dataset and actual results from the team.
