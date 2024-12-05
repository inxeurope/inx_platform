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
    try:
        key = int(key)
    except (ValueError, TypeError):
        pass
    return dictionary.get(key, {})

@register.filter
def get_bdg_item(dictionary, key):
    print("get_bdg_item, values passed in the function:", "-"*40)
    print("key", key, "of type:", type(key))
    print(f"dictionery: {dictionary}")
    try:
        returned_value = dictionary.get(key)
        if returned_value is None:
            key = int(key)
        returned_value = dictionary.get(key)
        print(f"returned_value: {returned_value}")
        print("-"*50)
        return returned_value
    except (TypeError, ValueError, AttributeError) as e:
        print("This combination created an ERROR:")
        print(f"key: {key}")
        print(f"dictionary: {dictionary}")
        print("Exception: ", e)
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
    print("Transform int is run")
    print(f"value: {value}  -  type: {type(value)}")
    try:
        return_value = int(value)
        print(f"transformed value: {return_value}")
        return return_value
    except (ValueError, TypeError):
        print(f"retrning original value: {value}")
        return value
    

@register.filter(name="remove_colon")
def remove_colon(label_tag):
    return label_tag.replace(':', '')


@register.filter(name='add_class')
def add_class(value, arg):
    return value.as_widget(attrs={'class': arg})
    