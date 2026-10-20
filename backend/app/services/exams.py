from app.models import GradeBand


def grade_for_percentage(bands: list[GradeBand], percentage: float) -> str:
    """Top-down matching: the highest band whose boundary is met wins."""
    ordered = sorted(bands, key=lambda b: b.min_percentage, reverse=True)
    for band in ordered:
        if percentage >= band.min_percentage:
            return band.grade
    return ordered[-1].grade if ordered else ""
