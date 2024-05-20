# custom_filters.py
from django import template
from loguru import logger

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
    logger.info(f"Entered the customer template tag build_query_param")
    logger.info(f"addtional_params: {additional_params}")
    temp_string =''
    if additional_params:
        for k, v in additional_params.items():
            print("key (", k, ") value: ", v)
            if v:
                if isinstance(v, list):
                    for item in v:
                        temp_string += f"&{k}={item}"
                elif isinstance(v, str):
                    temp_string += f"&{k}={v}"

    return_string = temp_string
    logger.info(f"returning value: {return_string}")
    return return_string