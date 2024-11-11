import random
import string
import json
from datetime import datetime
from collections import defaultdict
from pprint import pprint

def generate_random_string(length=6):
    # Generate a random string of specified length
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Define deeply nested defaultdicts
def nested_dict():
    return defaultdict(nested_dict)

def run():
    forecast_year = datetime.now().year
    budget_year = forecast_year + 1
    
    # Initialize the top-level defaultdict
    result = nested_dict()

    # Add first level of keys
    result["customer"] = "Durst"
    result["brands"]["grand_total_per_customer"]
    result["brands"]["RD1272"]
    result["brands"]["POP"]
    
    result["brands"]["grand_total_per_customer"]["scenarios"]["Forecast"][str(forecast_year)]["grand_total_per_customer"]
    
    
    for m in range(1, 13):
        result["brands"]["RD1272"]["color_groups"]["CMYK"]["scenarios"]["Forecast"][str(forecast_year)]["months"][str(m)] = {"volume": 100, "price": 10, "value": 1000}
        result["brands"]["RD1272"]["color_groups"]["CMYK"]["scenarios"]["Budget"][str(budget_year)]["months"][str(m)] = {"volume": 0, "price": 0, "value": 0}
        
        result["brands"]["RD1272"]["color_groups"]["Lights"]["scenarios"]["Forecast"][str(forecast_year)]["months"][str(m)] = {"volume": 0, "price": 0, "value": 0}
        result["brands"]["RD1272"]["color_groups"]["Lights"]["scenarios"]["Budget"][str(budget_year)]["months"][str(m)] = {"volume": 0, "price": 0, "value": 0}
    
        result["brands"]["grand_total_per_customer"]["scenarios"]["Forecast"][str(forecast_year)]["months"][str(m)] = {"volume": 400, "price": 10, "value": 4000}
        result["brands"]["grand_total_per_customer"]["scenarios"]["Budget"][str(forecast_year)]["months"][str(m)] = {"volume": 600, "price": 10, "value": 6000}
    
    pprint(result)
    # Convert the nested defaultdict to a regular dictionary for JSON serialization
    result_dict = json.loads(json.dumps(result, default=lambda x: dict(x) if isinstance(x, defaultdict) else x))

    # Output to a JSON file
    with open("output_test.json", "w") as f:
        json.dump(result_dict, f, indent=4)