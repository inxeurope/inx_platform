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
def dict_lookup(dictionary, key):
    try:
        key = int(key)
    except (ValueError, TypeError):
        pass
    return dictionary.get(key, {})


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_bdg_item(dictionary, key):
    try:
        returned_value = dictionary.get(key)
        if returned_value is None:
            key = int(key)
        returned_value = dictionary.get(key)
        return returned_value
    except (TypeError, ValueError, AttributeError) as e:
        return None

@register.filter
def get_month_total(dictionary, key):
    first_key = next(iter(dictionary))
    key_type_in_dict = type(first_key)
    
    if key_type_in_dict == int:
        key = int(key)

    returned_v =dictionary.get(key)

    return returned_v

@register.filter
def get_grand_total(dictionary, key):
    returned_v = dictionary.get(key)
    return returned_v
    
@register.filter
def transform_int(value):
    try:
        return_value = int(value)
        return return_value
    except (ValueError, TypeError):
        return value
    

@register.filter(name="remove_colon")
def remove_colon(label_tag):
    return label_tag.replace(':', '')

@register.filter
def get_month_abbreviated(dict, key):
    return dict.get(key).get('abbreviated_name')


@register.filter
def custom_number_decimal(value):
    """
    Format a number using dots as thousands separators and commas as decimal points.
    """
    try:
        # Convert the value to a float
        value = float(value)
        # Format the number with dot as thousands separator and comma as decimal separator
        return "{:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        # If conversion to float fails, return the original value
        return value

@register.filter
def custom_number_no_decimal(value):
    """
    Format a number using dots as thousands separators and commas as decimal points.
    """
    try:
        # Convert the value to a float
        value = float(value)
        # Format the number with dot as thousands separator and comma as decimal separator
        return "{:,.0f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        # If conversion to float fails, return the original value
        return value


@register.filter
def get_nested_item(dictionary, keys):
    keys = keys.split('.')
    for key in keys:
        dictionary = dictionary.get(key)
        if dictionary is None:
            return None
    return dictionary