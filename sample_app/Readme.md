Setup
-----

1. Setup the library using the instructions in the Readme document to generate the .whl file. Make sure that the required drivers are also installed.


2. Look through the root directory of the project for a folder called 'dist'. Within it will be a generated **.whl** file. **Make a note of or copy the file name**.


3. To run the gui sample code, create a new virtual environment, activate it, and cd into 'samples\\gui':


4. Once there, **replace** the **.whl** file name with your one and run:

```shell
pip install ..\..\dist\sony_cr-1.7.0-cp311-cp311-win_amd64.whl -r requirements.txt
```

Running
-------

1. Run from the samples/gui folder using:

```shell
python .\app.py
```

2. Connect the camera via USB (and make sure it is setup correctly for remote control)

3. Click 'Connect Control' in the top bar of the window.

4. Once connected, you can take pictures and change certain variables.

5. 'Connect Transfer' will allow... TODO

5. When finished, press 'Disconnect'.