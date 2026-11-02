from business_analysis import analyze_business_data
from assistant.data_loader import load_data


def get_business_context(path=None):
    return analyze_business_data(load_data(path), dataset_id="local-file")
