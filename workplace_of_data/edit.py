import os

directory_path = '.'
file_names = os.listdir(directory_path)

for old_file_name in file_names:
    
    new_file_name = old_file_name.replace(":", "_")
    new_file_name = old_file_name.replace("'", "")
    new_file_name = old_file_name.replace("-", "_")
    new_file_name = old_file_name.replace(" ", "_")
    
    hold = ""
    for letter in new_file_name:
        if letter == ":":
            hold+="_"
        elif letter == "-":
            hold+="_"
        else:
            hold+=letter

    new_file_name = hold
    if new_file_name != old_file_name:
        old_file_path = os.path.join(directory_path, old_file_name)
        new_file_path = os.path.join(directory_path, new_file_name)
        os.rename(old_file_path, new_file_path)

