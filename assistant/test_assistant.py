"""A small example that runs without an API call."""
import pandas as pd

from assistant.ai_assistant import ask_assistant
from assistant.data_connection import prepare_business_data
from business_analysis import analyze_business_data


def main():
    df = pd.DataFrame([{"date":"2024-01-01","product":"Example","units":10,"price":20,
                        "unit_cost":8,"marketing_spend":5,"expenses":15}])
    context = prepare_business_data(analyze_business_data(df,"example"))
    for question in ["What is our revenue?","What is our profit?","Which product has the lowest margin?","What is next month's revenue?"]:
        print(question)
        print(ask_assistant(question,context,mode="off"))


if __name__ == "__main__":
    main()
