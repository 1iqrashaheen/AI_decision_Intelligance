import argparse
import json
from pathlib import Path

import pandas as pd

from . import analyze_business_data


def main():
    parser = argparse.ArgumentParser(description="Analyze one sales, expense or inventory dataset.")
    parser.add_argument("file", type=Path)
    parser.add_argument("--kind", choices=["auto", "sales", "expenses", "inventory"], default="auto")
    parser.add_argument("--currency", default=None)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        df = pd.read_csv(args.file, low_memory=False) if args.file.suffix.lower() == ".csv" else pd.read_excel(args.file)
        result = analyze_business_data(df, dataset_id=args.file.stem, kind=args.kind, currency=args.currency)
        content = json.dumps(result, indent=2, allow_nan=False)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Analysis failed: {exc}\n")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
        print(f"Analysis saved to {args.output}")
    else:
        print(content)


if __name__ == "__main__":
    main()
