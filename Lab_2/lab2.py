# Chris Archibald

import sys

def get_absolute_path():
# Function to calculate the absolute path manually

    # Get the current file path using __file__
    current_path = __file__

    # Get the current working directory
    current_directory = sys.path[0]

    # If the script is run directly from the directory where it's located
    if not current_path.startswith(current_directory):
        absolute_path = current_directory + '/' + current_path
    else:
        # When run from a different directory
        absolute_path = current_path

    # Normalize the path (removing any './' or '../')
    components = absolute_path.split('/')
    stack = []

    for part in components:
        if part == '' or part == '.':
            continue
        elif part == '..':
            if stack:
                stack.pop()
        else:
            stack.append(part)

    # Join the stack to get the absolute path
    normalized_path = '/' + '/'.join(stack)

    return normalized_path

print(f"The absolute path of this script is: {get_absolute_path()}")
