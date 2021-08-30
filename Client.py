import socket   # For communitcation
import pickle   # For serialisation
import eel      # For GUI display server
import threading # For multi threaded - asynchronous sending and receiving
# Attempt import to check if on correct OS
try:
    from win10toast import ToastNotifier # For special OS notifications
except:
    print("DEBUG: You are not on windows 10 (or above), you will not recieve os notifications") # OS does not support, inform and continue
from Crypto.Cipher import AES # For AES encryption
from Crypto.Random import get_random_bytes # For generating random keys

# Setting Host IP
# Currently set to self-hosted remote server
host = "127.0.0.1" # NOTE: If you are hosting the server yourself change the ip to whatever is appropriate
# Setting the host port
port = 443  # NOTE: if you have changed port, change this accordingly, otherwise leave it alone
# Starting the TCP socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Connecting to the host
s.connect((host, port))
# Telling user
print("NETWORK: Connected to server")
print("NETWORK: Attempting handshake")
# Sending and receiving keys
otherkey = s.recv(1024)
key = get_random_bytes(16)
s.send(key)
# Print keys
print("NETWORK: My key: " + str(key) + ", Server key:", str(otherkey))

# Variable for state checking
global loggedin
loggedin = False

# Set web files folder
eel.init('web')

# A custom made function for sending double-layer encyrpted data to server
def serversend(message):
    # encrypt with our own key, they decrypt with ours
    # Serialising message so it can be encrypted
    message = pickle.dumps(message)
    # Creating a new cipher
    cipher = AES.new(key, AES.MODE_EAX)
    # Ciphering the data
    # NOTE: WE ARE USING A RANDOMLY GENERATED NONCE, for second layer encryption
    ciphered_data, tag = cipher.encrypt_and_digest(message)
    # Packing the data together and serialising it again so it can be sent
    tosend = [cipher.nonce, tag, ciphered_data]
    tosend = pickle.dumps(tosend)
    # Send packaged data
    s.send(tosend)
    return

# A custom function to recieve client data, then decrypt, then verify
def server_receive():
    # Receive data
    message = s.recv(2048)
    # Making sure client hasn't disconnected
    if not message:
        return "fail"
    # Deserialising data
    message = pickle.loads(message)
    # Seperating packaged data
    noonce = message[0]
    tag = message[1]
    data = message[2]
    # Creating cipher for decryption
    cipher = AES.new(otherkey, AES.MODE_EAX, noonce)
    # Verifying integrity of data using a tag
    msg = cipher.decrypt_and_verify(data, tag)
    # Deserialising data
    msg = pickle.loads(msg)
    return msg

# Custom function for login code to attempt a sign up
@eel.expose
def attempt_sign_up(username, passw):
    # Correct input
    username = username.replace(" ", "")
    passw = passw.replace(" ", "")
    
    # Create sending string
    tosend = "?" + username + " " + passw
    # Encrypt and send using function
    serversend(tosend)
    # Receive Feedback
    msg = server_receive()
    # Act upon feedback
    if msg == '$success-signup':
        print("NETWORK: Signup Success")
        return True
    else:
        return False

@eel.expose
def attempt_sign_in(username, passw):
    global loggedin
    # Correct input
    username = username.replace(" ", "")
    passw = passw.replace(" ", "")

    # Create sending string
    tosend = "!" + username + " " + passw
    # Encrypt and send using function
    serversend(tosend)
    # Receive Feedback
    msg = server_receive()
    # Act upon feedback
    if msg == '$success-login':
        print("NETWORK: Login Success")
        # Update toggle state variable if needed
        loggedin = True
        return True
    else:
        return False

# Custom function for showing windows notifications but only keeping data in RAM
# Does NOT send to the action / notification center for storage
@eel.expose
def win10notif(username, message, all):
    # Use try to mitigate OS errors
    try:
        toaster = ToastNotifier()
        if all == 0:
            toaster.show_toast("Secret Chat - Everyone Message",
                        username + " sent " + message,
                        icon_path="custom.ico",
                        duration=4)
            return True
        elif all == 1:
            toaster.show_toast("Secret Chat - Message",
                        username + " sent " + message,
                        icon_path="custom.ico",
                        duration=4)
            return True
        elif all == 2:
            toaster.show_toast("Secret Chat - Login",
                        username + " logged on",
                        icon_path="custom.ico",
                        duration=4)
        else:
            toaster.show_toast("Secret Chat - Logout",
                        username + " logged off",
                        icon_path="custom.ico",
                        duration=4)
    except:
        # If errors, dont worry, probably wrong OS
        return True

# List for connected users
global conlist
conlist = []
# Dictionary to store username to profile picture
global pfps
pfps = {}

# Function for logged in chat window to request required data and
# start the listening server on a new thread so the main thread can
# continue to communicate with the front end code
@eel.expose
def request_list():
    # Request and recieve connected user list
    serversend('*')
    global conlist
    conlist = server_receive()
    # Add in the all users option
    conlist.insert(0, "All Users")
    # Request and receive profile pictures
    global pfps
    serversend('=')
    pfps = server_receive()
    # Add in all users
    pfps["All Users"] = 6
    # Start new thread to listen for more stuff as this thread
    # will be used to continue listening for commands from the
    # front end code
    threading.Thread(target=listening).start()
    # Return and send the requested data to front end
    return conlist

# If a user selects a new profile picture
@eel.expose
def new_pfp(tosend):
    # Send it
    serversend(tosend);
    return True

# Function for when front-end wants to find out the profile picture of a certain user
@eel.expose
def query_pfp(index):
    global conlist
    # Find their name from id
    name = conlist[index]
    # Use dicitonary to find picture
    retval = pfps[name]
    # Return found value
    return retval

# Function for front-end to send messages
@eel.expose
def send_msg(msg, index):
    global conlist
    # if all message, prepend appropriately else send direct message
    if index == 0:
        tosend = "^ " + msg
    else:
        tosend = "@" + conlist[index] + " " + msg
    serversend(tosend)

# The function that is called by getlist() in the new thread
# so that it can listen to stuff sent by the main server and
# act upon it
def listening():
    # Use global variables
    global conlist
    global pfps
    # Keep listening unless disconnect
    while True:
        # NOTE: we do not print the received message so user can't retrieve
        # it this way after a log off. This a security feature mentioned on
        # the website
        print("NETWORK: listening...")
        msg = server_receive()
        # Deduce type using table at the top of server code
        if msg[0] == "@":
            # If direct message
            # Split
            data = msg[1:].split(" ", 1)
            sender = data[0]
            # Deduce id
            senderid = conlist.index(sender)
            # Update front end
            eel.pushmsg(senderid, data[1], pfps[sender])
            # Again note no logging of exact message, refer to note above
            print("MESSAGES: Received message from:", sender)
        elif msg[0] == "^":
            # Everyone message
            # Split
            data = msg[1:].split(" ", 1)
            sender = data[0]
            # Find sender (note this is visible on front end)
            senderid = conlist.index(sender)
            # Update front end
            eel.allmsg(senderid, data[1], sender, pfps[sender])
            # Again note no logging of exact message, refer to note above
            print("MESSAGES: Everyone message from:", sender)
        elif msg[0] == "+":
            # If new user
            user = msg[1:]
            conlist.append(user)
            # Update front-end
            eel.pushuser(user)
            print("USERS:", user, "logged on")
            # Try to send a notification
            try:
                win10notif(user, "", 2)
            except:
                pass
        elif msg[0] == "-":
            # On user quit
            if msg[1:] != '':
                # Assuming they were registered
                # Remove them from lists
                removeid = conlist.index(msg[1:])
                conlist.remove(msg[1:])
                # Remove them from front end
                eel.removeuser(removeid)
                # Try to send a notification
                try:
                    win10notif(user, "", 3)
                except:
                    pass
        elif msg[0] == 'p':
            # On change of profile picture
            # THIS CAN BE SELF
            # Deduce user and picture id
            newpid = msg[1]
            user = msg[3:]
            # Update in memory
            pfps[user] = newpid
            # If required now, apply
            if user in conlist:
                senderid = conlist.index(user)
                # Update front-end
                eel.change_pfp(senderid, newpid)
                print("USERS:", user, "changed their profile picture")

# Tracker so that you can only quit from the login window once
global i 
i = 0
# Callback on login window close
def opennext(route, websockets):
    global i
    global loggedin
    # Only open chat windows if already logged in (as non-logged in users should not have access)
    if loggedin == False:
        exit()
    # Stop infinite callbacks by incrementing counter
    i+=1
    if i == 1:
        # If needed start the main chat window
        eel.init('web')
        # Note the use of a different port, so we don't conflict with the login windows webserver
        eel.start('/chatwin/index.html', size=(1300, 700), port=8001)
    else:
        # Else close socket and gracefully shut down
        s.close()
        exit()

# Initialise and start the display server
eel.start('/login/index.html', size=(1080, 900), close_callback=opennext)
