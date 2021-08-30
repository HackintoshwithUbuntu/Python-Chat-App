# Python Chat App
A GUI python chat app with encryption, notifications and profile pictures

![image](https://user-images.githubusercontent.com/64008512/131279632-527f0a17-02e2-4857-96f2-a7485bf4c92d.png)
![image](https://user-images.githubusercontent.com/64008512/131279597-0b894364-6011-4d79-91b2-738e3dbc43e2.png)
![image](https://user-images.githubusercontent.com/64008512/131279489-8631b732-489f-4e0d-bf08-33c5fdd7da15.png)

## Features
- Encryption (with tag verification and nonce)
- Profile Pictures
- GUI interface
- Logins saved between srever reboots
- Profile Pictures saved between server reboots
- Server logs
- Native notifications on Windows
- Sounds throughout the app

## Running the files
1. Start the server.py file on a pc
2. Note the IP address of the pc (note you may need to diffrentiate between local and public, use 127.0.0.1 if client is same pc as server)
3. On the client.py file change line 15
```python
host = "Your host ip" # NOTE: If you are hosting the server yourself change the ip to whatever is appropriate
```
4. (If required) change the port on both server and client files, lines 318 and 17 respectively (note 8000 and 8001 will clash with the client webserver, so avoid them). If changing port restart the server.py file
5. Start the client.py file on the client pc
6. Follow screen prompts to sign in and chat!

## Notes
- If the login and profile picture files are not present when the code is run, they will be created. This means that you can reset logins by deleting those files
- Key exchange is not secure, everything after is
- Each client has a unique key
- See requirements.txt for dependencies

## Creating Executables with PyInstaller
1. First download PyInstaller `pip install PyInstaller`
2. Navigate to the directory where the files are saved
3. Run `python -m eel Client.py web`
4. Once you are happy with the output you may run again but with the arguements, `python -m eel Client.py web --onefile --noconsole`

## Acknowledgements
Login page (most design):  
Copyright (c) 2021 by Mehdi Aroui (https://codepen.io/mehdiaroui/pen/jJgPvj)  
Chat windows (only some GUI features):  
Copyright (c) 2021 by Fabio Ottaviani (https://codepen.io/supah/pen/jqOBqp)  
  
If this repository has helped you, consider starring
