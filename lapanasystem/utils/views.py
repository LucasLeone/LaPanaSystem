from datetime import datetime, timedelta


def iso_year_week_to_range(iso_year: int, iso_week: int):
    """
    Return the start and end date of a week in ISO format.
    """

    monday = datetime.strptime(f"{iso_year}-W{iso_week}-1", "%G-W%V-%u").date()
    sunday = monday + timedelta(days=6)
    return monday, sunday
