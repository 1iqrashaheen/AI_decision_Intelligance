"""Prepare uploaded columns with Fazeela's module and keep the quality notes."""
from business_analysis import prepare_dataframe
from backend.app.schemas.common import ColumnInfo, QualityReport


def clean_dataframe(raw_df):
    clean, metadata = prepare_dataframe(raw_df)
    quality = QualityReport(
        rows=len(clean), columns=len(raw_df.columns),
        duplicate_rows=metadata["duplicate_rows_removed"],
        missing_cells=int(raw_df.isna().sum().sum()),
        columns_info=[ColumnInfo(name=str(c), dtype=str(raw_df[c].dtype), missing=int(raw_df[c].isna().sum())) for c in raw_df],
    )
    metadata["dataset_kind"] = clean.attrs["dataset_kind"]
    return clean, quality, metadata
