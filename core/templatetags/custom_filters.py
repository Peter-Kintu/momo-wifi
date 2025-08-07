# core/templatetags/custom_filters.py

from django import template

# The `register` variable is how you register your custom filters and tags
register = template.Library()

@register.filter
def div(value, arg):
    """
    Divides the value by the argument and returns the result.
    
    Example usage in a template: {{ some_value|div:2 }}
    """
    try:
        # Convert values to floats to handle non-integer division
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        # Handle cases where the value or argument are not valid numbers,
        # or if the argument is zero, to prevent server errors.
        return None

