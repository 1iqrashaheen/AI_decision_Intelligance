"""Extract Samad's published cleaned bundle, at a pinned Git revision.

Run from any directory: python scripts/fetch_team_data.py
No notebook execution or new source downloads are needed.
"""
import io
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = "c6b934c"
BUNDLE = "Dataset_Sourcing_and_Data_Cleaning/preprocessed_datasets/processed_datasets_bundle.zip"


def main():
    try:
        blob = subprocess.check_output(["git", "show", f"{REVISION}:{BUNDLE}"], cwd=ROOT)
    except subprocess.CalledProcessError:
        raise SystemExit("Fetch the source first: git fetch origin Abdul_Samad_Task")
    destination = ROOT / "data" / "team_cleaned"
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        for item in archive.infolist():
            if not item.is_dir() and item.filename.endswith(".csv"):
                target = destination / Path(item.filename).name
                target.write_bytes(archive.read(item))
                print(target.relative_to(ROOT))
    print("The published bundle contains Online Retail, expenses and inventory; Online Retail II is absent.")


if __name__ == "__main__":
    main()
