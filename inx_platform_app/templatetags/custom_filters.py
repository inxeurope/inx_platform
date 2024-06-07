# custom_filters.py
from django import template
import math

register = template.Library()

@register.filter(name='format_large_number')
def format_large_number(value):
    """
    Convert an integer to a string representation with commas for thousands.
    """
    try:
        value = int(value)
    except (ValueError, TypeError):
        return value
    return "{:,}".format(value)

@register.filter
def build_query_params(additional_params):
    temp_string =''
    if additional_params:
        for k, v in additional_params.items():
            # print("key (", k, ") value: ", v)
            if v:
                if isinstance(v, list):
                    for item in v:
                        temp_string += f"&{k}={item}"
                elif isinstance(v, str):
                    temp_string += f"&{k}={v}"

    return_string = temp_string
    return return_string

@register.filter
def round_up(value):
    return math.ceil(value)

@register.filter
def get_item(dictionary, key):
    try:
        returned_value = dictionary.get(key)
        if not returned_value:
            key = int(key)
        returned_value = dictionary.get(key)
        # print(f"dictionary: {dictionary}, key: {key}, returned value: {returned_value}")
        return returned_value
    except (TypeError, ValueError, AttributeError):
        return None