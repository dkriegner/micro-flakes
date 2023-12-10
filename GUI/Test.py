import os
import sys

# Get the path of the executable file
exe_path = sys.executable
print("The path of the executable file is:", exe_path)

# Get the directory name from the path
exe_dir = os.path.dirname(exe_path)
print("The directory of the executable file is:", exe_dir)

input("Press a key!")
