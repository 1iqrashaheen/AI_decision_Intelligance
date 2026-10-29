# Team code used in this branch

The source repository is [AI_decision_Intelligance](https://github.com/1iqrashaheen/AI_decision_Intelligance).

This note records where the shared files came from, so team members can find the original work.

## Source branches

| Team member | Branch | Code or data used |
|---|---|---|
| Abdul Samad | `Abdul_Samad_Task` | Cleaned dataset ZIP, preprocessing notebook and dataset notes |
| Muhammad Arham | `arham-work` | FastAPI backend and `js/api.js` |
| Ahsan Rafique | `Ahsan-Rafique-Task` | Forecasting code and saved results from his ZIP |
| Arayash Noor | `whatif-calculations` | The separate `whatif/` folder |
| Muhammad Waleed Ansari | Website files already present on the assistant branch | Dashboard, upload, What-If and comparison pages |

## What was connected

Fazeela's analysis uses the cleaned data shared by Abdul Samad. Run `python scripts/fetch_team_data.py` from the main project folder to place those files in `data/team_cleaned/`.

The shared ZIP has retail, expense and inventory data. It does not have a cleaned Online Retail II file. The datasets remain separate.

The assistant uses Arham's backend to reach the analysis and scenario results. Ahsan's saved forecast is checked against its original daily sales history before chat can use it.

Arayash's separate calculation module was also copied in. Its percentage inputs and demand assumptions differ from the backend simulator. Check which function you are calling: `10` means 10% in `whatif/`, while `0.10` means 10% in the backend API.

The website now has an assistant page. Newly saved scenarios include a link to their dataset so the assistant can choose the right ones.

Ayesha's comparison and report work is on `codex/ayesha-comparison-reports`. It uses the existing analysis and simulator functions, adds PDF/CSV downloads, and keeps comparisons tied to the current dataset. See [the report notes](../reports/README.md) for the workflow.

Saud's separate Node/PostgreSQL service has not been merged into this FastAPI backend. Database, login and deployment still need to be connected with the rest of the team.

## Small changes made to the shared files

- Backend imports were adjusted so the app runs from the main project folder.
- Analysis and chat now call the completed modules. Upload cleaning no longer guesses missing costs.
- The forecasting script reads data from this project's folders and writes new results to `output/forecasting/`.
- The preprocessing notebook's saved outputs were cleared. Its code and notes were kept.
- Original dataset credits remain in [the dataset notes](datasets/README.md) and notebook. Ahsan's original README is kept in `forecasting/SOURCE_README.md`.

## Exact versions used

These commit IDs identify the source versions. They are useful when comparing a later update with the files used here.

| Branch | Commit |
|---|---|
| `Abdul_Samad_Task` | `c6b934cd0fa8c0877f8b3985d96fe3d9bdabc967` |
| `arham-work` | `6f06f51818ff3ed13ed86d1138b29d9b92d34463` |
| `Ahsan-Rafique-Task` | `3d9f77e787b2bb0ea82eb7abaa0e913f0abe9193` |
| `whatif-calculations` | `60542e6c023a97119c3b9fe907edb3dba17d14b7` |
