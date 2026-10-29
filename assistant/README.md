# AI business assistant - Iqra's part

The assistant answers questions about the selected business file. It uses Fazeela's analysis, available forecasts and calculated scenarios.

Start with the setup steps in the [main README](../README.md). The commands in this file also run from the main project folder.

## Try the chat

1. Start the server and open [AI Assistant](http://127.0.0.1:8001/assistant.html).
2. Click **Try sample sales**, or choose your own CSV or Excel file.
3. Ask a question about the file.

Examples:

- What is our total revenue?
- What is our gross profit?
- Which product has the lowest profit margin?
- What was revenue in 2025-03?
- What unusual values should I review?
- What happens if prices increase by 10%?

Use a month or product name that exists in your data. If the required information is missing, the assistant says it is unavailable.

Each question is handled on its own. Write the product or month again in a follow-up question.

## Ask about a saved scenario

Load data on the **Upload Data** page, enter your changes on **What-If**, and save the scenario. Then open **AI Assistant**, click **Use dashboard data**, and choose the scenario under **Question context**.

The assistant recalculates those changes for the selected dataset before answering. A scenario from a different dataset cannot be used.

For a change to one variable, you can ask directly in chat, such as "What if expenses increase by 15%?" For several changes at once, use the What-If page.

Profit estimates need complete unit costs, marketing spend and expenses. The assistant does not assume these costs from retail sales.

Older saved scenarios without a dataset link need to be saved again.

## Use the assistant in Python

This example creates some sample data and asks a question without making an API call:

```python
import pandas as pd
from business_analysis import analyze_business_data
from assistant.data_connection import prepare_business_data
from assistant.ai_assistant import answer_question

data = pd.DataFrame([
    {
        "date": "2025-01-01",
        "product": "Example product",
        "units": 10,
        "price": 20,
        "unit_cost": 8,
        "marketing_spend": 5,
        "expenses": 15,
    }
])

analysis = analyze_business_data(data, dataset_id="example-sales")
context = prepare_business_data(analysis=analysis)
reply = answer_question("What is our net profit?", context, mode="off")

print(reply["answer"])
```

Use `ask_assistant(question, context)` if you only need the answer as text. Use `answer_question()` when you also need the answer's sources and any warnings.

To use Groq, configure `.env` as shown in the main README and leave out `mode="off"`.

## Send results from another module

`prepare_business_data()` can receive:

| Argument | What to pass |
|---|---|
| `analysis` | The dictionary returned by `analyze_business_data()` |
| `simulation` | Calculated scenario results |
| `forecasting` | Forecast results |
| `recommendations` | Reserved for a future connection; supplied text is not currently used as the chat's advice |

Pass Python dictionaries, not a paragraph containing numbers. Every extra result must include the same `dataset_id` as the analysis. This keeps results from different files separate.

The current advice uses the selected analysis findings. See [the backend schemas](../backend/app/schemas/common.py) for the result fields.

## Backend request

The website sends a request to `POST /api/chat`:

```json
{
  "dataset_id": "the-id-returned-by-upload",
  "question": "What is our profit?",
  "scenario": null
}
```

The response contains:

| Field | Meaning |
|---|---|
| `answer` | Text to display in the chat |
| `context_used` | Which result fields were used |
| `source` | `groq_grounded` for an AI-selected answer, or `grounded_assistant` for a local answer |
| `warnings` | Any notes about the AI service or missing inputs |

When sending a selected scenario, also include `scenario_dataset_id`. It must match `dataset_id`, and the scenario's original figures must match the dataset.

## How the answer is checked

Python calculates the business figures first. Groq chooses which prepared facts answer the question. The app checks that choice before displaying the answer.

The model does not write the displayed amounts. If its choice fails the checks, `auto` mode uses the local answer method and shows a note. In `required` mode, the request returns an error.

The assistant supports the question types listed above, plus units, invoice counts, country results, trends, expense summaries, inventory values and available forecasts. It may not understand every way of asking a question.

If the older dashboard upload page has filled missing expenses with zero, the assistant treats those imported costs as unknown. Upload the original file directly on the assistant page for more accurate information about missing values.

## Try the terminal example

```powershell
python -m assistant.test_assistant
```

To ask questions about a file in the terminal:

```powershell
python -m assistant.ai_assistant --file data/team_cleaned/online_retail_cleaned.csv
```

Add `--offline` to use the local answer method. Type `exit` to finish.

Groq's format for selecting facts is described in [its structured output documentation](https://console.groq.com/docs/structured-outputs).
