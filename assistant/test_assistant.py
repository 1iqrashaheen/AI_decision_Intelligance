
from ai_assistant import ask_assistant
from data_connection import prepare_business_data


# Temporary results from other project modules
analysis = """
Total Revenue: £500,000
Total Expenses: £350,000
Total Profit: £150,000
"""

simulation = """
Scenario: Increase product prices by 10%
Original Revenue: £500,000
Estimated Revenue: £550,000
Original Profit: £150,000
Estimated Profit: £200,000
Assumption: Number of products sold and expenses remain unchanged.
"""

forecasting = """
Forecast Period: Next Month
Estimated Revenue: £520,000
Method: Example forecast for testing only.
"""

recommendations = """
Consider testing the new prices before applying them permanently.
Higher prices may reduce customer demand.
The estimated profit increase is not guaranteed.
"""

business_data = prepare_business_data(
    analysis=analysis,
    simulation=simulation,
    forecasting=forecasting,
    recommendations=recommendations
)

questions = [
    "What is my current profit?",
    "What happens if I increase prices by 10%?",
    "What is my expected revenue next month?",
    "What do you recommend?",
    "Which country generated the highest revenue?"
]

for question in questions:
    print(f"\nYou: {question}")

    try:
        answer = ask_assistant(question, business_data)
        print(f"Assistant: {answer}")

    except Exception as error:
        print("Error:", error)
