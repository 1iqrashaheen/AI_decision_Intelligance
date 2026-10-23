
import os
from dotenv import load_dotenv
from groq import Groq
from data_connection import prepare_business_data

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"


def ask_assistant(question, business_data=None):
    if business_data is None:
        business_data = prepare_business_data()

    system_prompt = """
You are an AI Business Assistant for the AI Decision Intelligence project.

Your job is to answer business questions using the supplied business information.

Rules:
1. Use only the supplied business information for business-specific facts.
2. Never invent sales, revenue, profit, costs, forecasts, or percentages.
3. If information is missing, clearly say it is unavailable.
4. Do not create new financial estimates or calculations yourself.
5. Use the exact figures supplied in the business information.
6. Clearly distinguish actual results, forecasts, and what-if estimates.
7. Explain recommendations using available results and their stated assumptions.
8. Do not invent specific thresholds, testing periods, or numerical advice.
9. Do not assume that a forecast is guaranteed.
10. Keep answers short, clear, and easy to understand.
11. If asked about unsupported information, explain what is missing.
12. Do not mix information from different datasets or scenarios.
13. If the supplied figures are inconsistent, mention the inconsistency
    instead of making up a correction.

Business Information:
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt + str(business_data)
            },
            {
                "role": "user",
                "content": question
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    try:
        business_data = prepare_business_data()
        print("Business data loaded successfully!")
    except Exception as error:
        print("Could not load business data:", error)
        business_data = "No business data available."

    print("\nAI Business Assistant started!")
    print("Type 'exit' to stop.\n")

    while True:
        question = input("You: ").strip()

        if question.lower() == "exit":
            break

        if not question:
            continue

        try:
            answer = ask_assistant(question, business_data)
            print("\nAssistant:", answer, "\n")
        except Exception as error:
            print("Error:", error)
