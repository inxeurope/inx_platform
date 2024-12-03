import sys

def combine_files(keys_file, values_file, output_file):
    with open(keys_file, 'r') as keys_file, open(values_file, 'r') as values_file, open(output_file, 'w') as output_file:
        keys = [line.strip() for line in keys_file]
        values = [line.strip() for line in values_file]

        # Ensure the number of keys matches the number of values
        if len(keys) != len(values):
            print("Error: The number of keys and values must be the same.")
            sys.exit(1)

        # Write the combined dictionary to the output file
        output_file.write("output_dict = {\n")
        for key, value in zip(keys, values):
            output_file.write(f'    "{key}": "{value}",\n')
        output_file.write("}\n")

if __name__ == "__main__":
    # Check if three file names are provided as command-line arguments
    if len(sys.argv) != 4:
        print("Usage: python script.py keys.txt values.txt output_dict.py")
        sys.exit(1)

    keys_file = sys.argv[1]
    values_file = sys.argv[2]
    output_file = sys.argv[3]

    # Combine the contents of the two files into a dictionary and write to the output file
    combine_files(keys_file, values_file, output_file)

    print(f"Combined dictionary written to {output_file}")
