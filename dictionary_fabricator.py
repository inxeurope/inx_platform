# Define the file names
sql_file = "dictionary_list_sql.txt"
app_file = "dictionary_list_app.txt"
output_file = "dictionary_output.py"

# Initialize an empty dictionary to store the data
result_dict = {}

# Open both files and process them line by line
with open(sql_file, "r") as sql_file, open(app_file, "r") as app_file:
    for sql_line, app_line in zip(sql_file, app_file):
        sql_line = sql_line.strip()
        app_line = app_line.strip()
        result_dict[sql_line] = app_line

# Write the resulting dictionary to the output file
with open(output_file, "w") as output:
    output.write("data = {\n")
    for key, value in result_dict.items():
        key = key.replace(",[", "")
        key = key.replace("[", "")
        key = key.replace("]", "")
        value = value.replace(",[", "")
        value = value.replace("]", "")
        output.write(f"    '{key}': '{value}',\n")
    output.write("}\n")

print(f"Data combined and written to {output_file}")






