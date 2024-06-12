# custom_filters.py
from django import template
import math
import pprint
import django

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

@register.filter
def get_month_total(dictionary, key):
    first_key = next(iter(dictionary))
    key_type_in_dict = type(first_key)
    # print(f"type of the key of dictionary: {key_type_in_dict}")
    # print(f"dictionary: {dictionary} - type: {type(dictionary)}")
    # print(f"key: {key} - type of key passed: {type(key)}")
    
    if key_type_in_dict == int:
        key = int(key)

    returned_v =dictionary.get(key)
    # print(f"returned_v: {returned_v}")
    return returned_v

@register.filter
def get_grand_total(dictionary, key):
    first_key = next(iter(dictionary))
    key_type_in_dict = type(first_key)
    print("GRAND TOTAL")
    print(f"type of the key of dictionary: {key_type_in_dict}")
    print(f"dictionary: {dictionary} - type: {type(dictionary)}")
    print(f"key: {key} - type of key passed: {type(key)}")
    returned_v = dictionary.get(key)
    return returned_v
    
@register.filter
def transform_int(value):
    return int(value)