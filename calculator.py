from datetime import datetime

non_claimer_lookup = {
    "Red": 1,
    "Amber": 1,
    "Purple": 1,
    "Green": 1,
    "New": 1,
    "Blue": 1,
    "Grey": 1
}

claimer_lookup = {
    "Red": 1,
    "Amber": 1,
    "Purple": 1,
    "Green": 1,
    "New": 1,
    "Blue": 1,
    "Grey": 0
}

def calculate_months(total_annual_subs, registration, arrears, financial_distress, mf_last_year, mf_this_year, segment, claims_paid):
    """
    Calculate the eligibility or score based on various criteria.

    Parameters:
    total_annual_subs (float): Total annual subscription including IPT.
    registration (str): Registration number.
    arrears (int): Number of months in arrears.
    financial_distress (int): Indicator of financial distress.
    mf_last_year (str): Months free received last year ('Yes' or 'No').
    mf_this_year (int): Number of months free in the current contract year.
    segment (str): Colour segment category.
    claims_paid (str): Value of claims paid in the last year.

    Returns:
    int: Eligibility score or result based on input criteria.
    """

    if total_annual_subs is None:
        print("Failed at total_annual_subs check")
        return 0
    if registration is None:
        print("Failed at registration check")
        return 0
    if arrears is None:
        print("Failed at arrears check")
        return 0
    if financial_distress is None:
        print("Failed at financial_distress check")
        return 0
    if mf_last_year is None:
        print("Failed at mf_last_year check")
        return 0
    if segment == "Missing" or claims_paid == "More Than £1000":
        print("Failed at segment or claims_paid check (segment missing or claims more than £1000)")
        return 0
    if int(mf_this_year) > 0:
        print("Failed at mf_this_year check (greater than 0)")
        return 0
    if claims_paid is None:
        print("Failed at claims_paid check")
        return 0
    if claims_paid == "Less Than £500" and mf_last_year == "Yes":
        print("Passed at claims_paid less than £500 and mf_last_year is Yes")
        return 1
    if claims_paid == "Between £500 and £1000" and mf_last_year == "Yes" and segment != "Grey":
        print("Passed at claims_paid between £500 and £1000, mf_last_year is Yes, and segment is not Grey")
        return 1
    if mf_last_year == "Yes":
        print("Failed at mf_last_year check (is Yes)")
        return 0
    if claims_paid == "Less Than £500":
        months_free = non_claimer_lookup.get(segment, 0)
        print(f"Result from non_claimer_lookup: {result}")
        return months_free
    else:
        months_free = claimer_lookup.get(segment, 0)
        print(f"Result from claimer_lookup: {result}")
        return months_free

def calculate_value(total_annual_subs, payment_frequency, renewal, months_free):

    final_value = float(total_annual_subs) - round(
        (float(total_annual_subs)/12 * months_free)
        if payment_frequency == "Monthly"
        else (float(total_annual_subs)/((renewal + datetime.timedelta(days=365)) - renewal).days * months_free * 31),2
    )

    return final_value