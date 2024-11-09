import random
import string
from collections import defaultdict
from pprint import pprint

def generate_random_string(length=6):
    # Generate a random string of specified length
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def run():
    # Initialize the top-level defaultdict
    result = defaultdict(lambda: "")

    # Add first level of keys
    result["customer"] = "Durst"
    result["brands"] = defaultdict(lambda: {"color_groups": defaultdict(lambda: "")})

    # Add second level of keys
    result["brands"]["grand_total_per_customer"] 
    result["brands"]["LED"]
    result["brands"]["POP"]
    
    # Generate 4 random strings and add them as keys in the brands level
    random_keys = [generate_random_string() for _ in range(4)]
    for key in random_keys:
        result["brands"][key]
        
    # Work at clolor_group level

    pprint(result)