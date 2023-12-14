## Instalation (Operation-system-independent)

### Automatic
This software can be installed by flit. Follow these steps:
1. Download this repository as a ZIP file.
2. Extract the ZIP to a final path.
3. Open the terminal in the same path.
4. Use the following command.
```
pip install -e .
```
5. Wait to finish installation.
> [!NOTE]
> For more information visit this webpage: https://flit.pypa.io/en/stable/.


### Creating the executable file manually (MS Windows and Mac OS X)
To run this software, Python 3 and the following libraries are required:
- PIL
- openpyxl
- cv2
- numpy
- PyQt6
- platformdirs
  
To install, use the following command:
```
pip install -r requirements.txt
```
It is necessary to have PIP in Python installed. To install, visit this webpage: https://pip.pypa.io/en/stable/installation/.

Then use the following commands to create the exe file:
```
pyinstaller .\gui_script.spec
```
or
```
pyinstaller .\gui_script.spec
```
The spec files are written for Windows. Please take a look at https://pyinstaller.org/en/stable/usage.html to switch to Mac.


