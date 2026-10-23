
from business_context import get_business_context


def prepare_business_data(
    analysis=None,
    simulation=None,
    forecasting=None,
    recommendations=None
):
    sections = []

    if analysis is not None:
        sections.append(f"Business Analysis:\n{analysis}")
    else:
        sections.append(
            "Business Analysis:\n" + get_business_context()
        )

    if simulation is not None:
        sections.append(f"What-If Simulation:\n{simulation}")

    if forecasting is not None:
        sections.append(f"Sales Forecasting:\n{forecasting}")

    if recommendations is not None:
        sections.append(f"Recommendations:\n{recommendations}")

    return "\n\n".join(sections)
