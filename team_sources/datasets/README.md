
# AI Decision Intelligence — Preprocessed Datasets

**Contributor:** Abdul Samad  
**Project:** AI Decision Intelligence  
**Workstream:** Dataset Sourcing, Preprocessing & Data Cleaning  
**Branch:** `Abdul_Samad_Task`

## Overview

This directory contains the preprocessed datasets and supporting resources prepared for the AI Decision Intelligence project. The objective is to organize the source data, apply data-cleaning procedures, and prepare structured datasets for business analysis and sales forecasting.

## Directory Contents

| File | Description |
|---|---|
| `Preprocessed_Datasets.zip` | Bundle containing the generated preprocessed datasets. |
| `AI_Decision_Intelligence_Dataset_Preprocessing.ipynb` | Google Colab/Jupyter notebook containing the preprocessing workflow for all four datasets. |
| `README.md` | Documentation describing the datasets and preprocessing workflow. |

## Datasets Processed

### 1. Online Retail

- **Source:** [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/352/online+retail)
- **Original records:** 541,909
- **Purpose:** Sales transaction analysis and forecasting preparation.
- **Key fields:** Invoice number, stock code, description, quantity, invoice date, unit price, customer ID, and country.

### 2. Sample Expenses Dataset

- **Source:** [HowToCSV — Sample Expenses CSV](https://howtocsv.com/sample-expenses-csv/)
- **Purpose:** Business expense analysis and financial decision support.
- **Key fields:** Expense ID, date, category, vendor, amount, payment method, employee, and status.

### 3. Sample Products / Inventory Dataset

- **Source:** [HowToCSV — Sample Products CSV](https://howtocsv.com/sample-products-csv/)
- **Purpose:** Product and inventory analysis.
- **Key fields:** Product ID, name, category, price, cost, stock, SKU, and rating.

### 4. Online Retail II

- **Source:** [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/502/online+retail+ii)
- **Original records:** 1,067,371
- **Purpose:** Large-scale sales transaction analysis and forecasting preparation.
- **Key fields:** Invoice, stock code, description, quantity, invoice date, price, customer ID, and country.

## Preprocessing Workflow

The notebook contains four separate preprocessing blocks, one for each dataset.

The workflow includes:

1. Downloading or loading the original dataset.
2. Standardizing column names.
3. Converting dates and numeric columns to appropriate data types.
4. Identifying missing values and duplicate records.
5. Applying dataset-specific cleaning rules.
6. Preserving important transaction information, including returns and cancellations where applicable.
7. Generating derived fields for analysis.
8. Saving the cleaned datasets and relevant outputs.

For both retail datasets, the workflow also generates daily sales time series for sales analysis and forecasting.

## Expected Output Files

Depending on the notebook configuration, the generated outputs may include:

- Cleaned Online Retail dataset
- Cleaned expenses dataset
- Cleaned products/inventory dataset
- Cleaned Online Retail II dataset
- Daily sales time series for both retail datasets
- Data-quality reports, where generated

Actual output filenames and row counts should be verified after executing the notebook.

## Important Data Notes

- Original source datasets should remain unchanged.
- Cleaning decisions should be documented and reproducible.
- Missing customer IDs should not automatically be treated as invalid transactions.
- Returns and cancellations should remain identifiable when required for analysis.
- Gross positive sales and net sales are different measures and should be selected according to the forecasting objective.
- The expenses and inventory datasets come from separate sources and may not share identifiers with the retail datasets.
- The number of records may change after preprocessing because of duplicate removal and data-quality filtering.

## How to Reproduce the Preprocessing

1. Download `AI_Decision_Intelligence_Dataset_Preprocessing.ipynb`.
2. Open [Google Colab](https://colab.research.google.com/).
3. Upload the notebook.
4. Execute the setup and preprocessing blocks in order.
5. Review the row counts, data-quality summaries, and generated outputs.
6. Package the resulting preprocessed datasets into `Preprocessed_Datasets.zip`.

## Data Sources and Attribution

- [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail)
- [HowToCSV Sample Expenses CSV](https://howtocsv.com/sample-expenses-csv/)
- [HowToCSV Sample Products CSV](https://howtocsv.com/sample-products-csv/)
- [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii)

Review the applicable licensing and attribution requirements before redistributing datasets.

---

**Prepared by:** Abdul Samad  
**Project:** AI Decision Intelligence  
**Status:** Dataset preprocessing and documentation
