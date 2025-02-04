def calculate_delta_percentage(current, previous):
    """Calculate percentage change between two values"""
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

def calculate_ratio(numerator, denominator, as_percentage=True):
    """
    Calculate ratio between two values, optionally as a percentage
    
    Args:
        numerator (float): The value to be divided
        denominator (float): The value to divide by
        as_percentage (bool): If True, multiply result by 100
        
    Returns:
        float: The calculated ratio (or 0 if denominator is 0)
    """
    if denominator == 0:
        return 0
    ratio = numerator / denominator
    return ratio * 100 if as_percentage else ratio
