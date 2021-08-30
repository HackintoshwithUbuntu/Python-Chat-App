# Imports
import socket   # Communication
import threading    # Communication with multiple users at once
import pickle   # Serialising data
import hashlib  # Hashing passwords
from Crypto.Cipher import AES   # AES encryption algorithms
from Crypto.Random import get_random_bytes  # For generating random keys and nonces

# A list of codes used in this program to prefix messages, so client knows their meaning
'''
______________________________________
|  CODE   |        MEANING           |
|____________________________________|
?         |        Signup            |
!         |        Signin            |
$         |        Control           |
@         |        Direct Message    |
^         |        Everyone Message  |
*         |        Request list      |
+         |        New user online   |
-         |        User logged off   |
=         |        Request pics dict |
p         |        New profile pic   |
_____________________________________|
'''


# A dictionary storing usernames and passwords
logins = {}

# dictionary to store corresponding socket to username
record = {}
# dictionary to username to socket
records = {}
# dictionary to store username to server key
keys = {}

# Dictionary storing profile pictures
pics = {}

# List to keep track of socket descriptors
connected_list = []

# A dictionary for working with logins (note: this is just so we can use the data in the file)
loginss = {}

# Starting the server socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Note: code skips to end as these function are not used until later

# A custom made function for sending double-layer encyrpted data to clients
def send_to_client(clientsocket, message, key):
    # encrypt with our own key, they decrypt with ours
    # Serialising message so it can be encrypted
    msg = pickle.dumps(message)
    # Creating a new cipher
    cipher = AES.new(key, AES.MODE_EAX)
    # Ciphering the data
    # NOTE: WE ARE USING A RANDOMLY GENERATED NONCE, for second layer encryption
    ciphered_data, tag = cipher.encrypt_and_digest(msg)
    # Packing the data together and serialising it again so it can be sent
    tosend = [cipher.nonce, tag, ciphered_data]
    tosend = pickle.dumps(tosend)
    # Send packaged data
    clientsocket.send(tosend)
    return

# A custom function to recieve client data, then decrypt, then verify
def client_receive(clientsocket, otherkey):
    # Receive data
    msg = clientsocket.recv(2048)
    # Making sure client hasn't disconnected
    if not msg:
        return "disconnect"
    else:
        # Seperating packaged data
        msg = pickle.loads(msg)
        noonce = msg[0]
        tag = msg[1]
        data = msg[2]
        # Creating cipher for decryption
        cipher = AES.new(otherkey, AES.MODE_EAX, noonce)
        # Verifying integrity of data using a tag
        msg = cipher.decrypt_and_verify(data, tag)
        # Deserialising data
        msg = pickle.loads(msg)
        return msg

# A custom function for sending data to all clients, except sender
def send_all(sender, message):
    for i in connected_list:
        if i == sender:
            continue
        # Finding the socket
        receiversoc = records[i]
        # Send data using above function
        send_to_client(receiversoc, message, keys[i])

# A custom function for sending a message to all users
def msg_all(message, sender):
    # Constructing so client knows what this message is
    construct = "^"+ sender + " " + message
    # Send data using above function
    send_all(sender, construct)

# A custom function for telling all clients about a new logon
def new_online(user):
    # Construciting
    construct = '+' + user
    # Sending to all using function
    send_all(user, construct)

# A custom function to check if a file exists without throwing errors
def file_exists(name):
    filename = name + ".txt"
    try:
        my_file = open(filename)
        my_file.close()
        return True
    except:
        return False

# A utility function to allow quick updating of saved passwords and profile pictures
def updatefile(name, obj):
    # Open file
    with open(name, 'wb+') as file:
        # Dump new data
        pickle.dump(obj, file)

# The main function for communicating with clients on a new thread
# This handles most work and messaging duties
# NOTE: this is run on one thread per client
def on_new_client(clientsocket,addr):
    # A string for storing username
    username = ''
    # Encryption Handshake
    print("NETOWRK: Attempting handshake with: " + addr[0] + ":" + str(addr[1]))
    # Generating a new COMPLETELY RANDOM key
    key = get_random_bytes(16)
    # Exchanging (not secure)
    clientsocket.send(key)
    # Receiving other key
    otherkey = clientsocket.recv(1024)
    # Printing it on console
    print("NETWORK: Server key: " + str(key) + ", "+ str(addr[0]) + ":" + str(addr[1]) + " key:", str(otherkey))

    # Wrapped in try except to detect logging off of users
    try:
        # Attempting sign in and sing up
        while True:
            # Receive data
            login = client_receive(clientsocket, otherkey)
            print("DEBUG: login / signup attempt", login)
            # Making sure the client hasn't disconnected
            if login == "disconnect":
                clientsocket.close()
                break
            # Splitting username and password, clients have already validated input
            user, passw = login[1:].split()
            passw = passw.encode("utf-8")
            # Hashing the password
            passw = hashlib.sha1(passw)
            # Storing hashed password in hex form
            passw = passw.hexdigest()
            print("DEBUG: Hashed password is: " + str(passw))

            # if sign up else if login attempt
            if(login[0] == '?'):
                # Creating an account
                # If user hasn't already signed up
                if user not in loginss:
                    # Store username and password combo in memory
                    loginss[user] = passw;
                    # Tell the client
                    send_to_client(clientsocket, "$success-signup", key)
                    # Give them default profile pic
                    pics[user] = 0
                    # Update relevant storage
                    updatefile("loginss.txt", loginss)
                    updatefile("pic.txt", pics)
                    print("USERS:", user, "signed up")
                else:
                    # Else tell them they failed
                    send_to_client(clientsocket, "$fail-signup", key)
                    print("USERS: Received failed signup")
                continue
            elif(login[0] == '!'):
                # Logging in
                # In a try except to prevent key errors
                try:
                    if(loginss[user] == passw):
                        # This is a successful login
                        # Marking such on server
                        username = user
                        # Tell the client
                        send_to_client(clientsocket, "$success-login", key)
                        print("USERS:", username, "signed in")
                        break
                    else:
                        # Unsuccessful login
                        # Tell them they failed
                        send_to_client(clientsocket, "$fail-login", key)
                except:
                    # Probably key error, they need to sign up first
                    # Tell them they failed
                    send_to_client(clientsocket, "$fail-login", key)

        # Only if they have logged in successfully
        if(username != ''):
            # If they are not connected (should be almost always)
            if username not in connected_list:
                # mark thier username as conncted
                connected_list.append(username)
                # Tell clients about new profile picture and new client username
                send_all(username, "p"+str(pics[username])+" "+username)
                new_online(username)
                print("USERS: Sent", username, "is online")
            # Record sockets and keys for easy access by utility functions
            record[clientsocket] = username
            records[username] = clientsocket
            keys[username] = key

            # Listen and act until told not to
            while True:
                # Receive using function
                msg = client_receive(clientsocket, otherkey)
                # Make sure client hasnt disconnected
                if msg == "disconnect":
                    # If they have tell other clients and remove them from lists
                    connected_list.remove(username)
                    del keys[username]
                    clientsocket.close()
                    send_all("", "-"+username)
                    print("Users: " + username + " quit")
                    break

                # Interpreting comands from clients using codes from the table at the top
                if msg[0] == '@':
                    # Split message
                    recievername = msg[1:].split(" ", 1)
                    # Determine sockets and keys
                    receiversoc = records[recievername[0]]
                    reckey = keys[recievername[0]]
                    # Create message
                    tosend = "@" + username + " " + recievername[1]
                    print("MESSAGES: " + username + " SENT " + recievername[1] + " TO " + recievername[0])
                    # Send
                    send_to_client(receiversoc, tosend, reckey)
                elif msg[0] == '^':
                    # Determine sendername
                    sendername = record[clientsocket]
                    # Remove whitespace
                    tosend = msg[1:].strip()
                    print("MESSAGES: " + sendername + " SENT " + tosend + " TO ALL USERS")
                    # Send to all using function
                    msg_all(tosend, sendername)
                elif msg[0] == '*':
                    # If request connected list, send list
                    print("DEBUG:", username, "requested list")
                    send_to_client(clientsocket, connected_list, key)
                elif msg[0] == 'p':
                    # Determine sendername
                    sendername = record[clientsocket]
                    # Update memory list and file
                    pics[sendername] = msg[1]
                    updatefile("pic.txt", pics)
                    # Tell other clients of updated picture
                    send_all('', msg + " " + sendername)
                    print("USERS:", sendername, "changed their profile picture to:", msg[1])
                elif msg[0] == '=':
                    # If request pic dict, send pic dict
                    print("DEBUG:", username, "requested pics dict")
                    send_to_client(clientsocket, pics, key)
                
    except:
        # This is usually a logoff
        try:
            # This is when they are registered and logged in
            clientsocket.close()
            connected_list.remove(username)
            del keys[username]
            # Tell other clients
            send_all("", "-"+username)
            print("USERS: " + username + " quit")
        except:
            # If they arn't registered, the above code will have already closed the socket, so just record and quit
            print("USERS: Non-Authenicated user quit")


# Code skips to here

# Check if both files exist and populate memory with their contents it they do
# If they don't, set memory contents to empty and create files
# Also log it at the end, so the server runner knows what just happened
if file_exists("loginss") == False:
    file = open("loginss.txt", "w+")
    file.close()
with open('loginss.txt', 'rb') as file:
    try:
        loginss = pickle.load(file)
    except:
        print("DEBUG: Failed reading file (the login file is probably empty, no need to worry)")

if file_exists("pic") == False:
    file = open("pic.txt", "w+")
    file.close()
with open('pic.txt', 'rb') as file:
    try:
        pics = pickle.load(file)
    except:
        print("DEBUG: Failed reading file (the pic file is probably empty, no need to worry)")


# Telling the host that it doesn't need to filter ips
host = ''
# Setting the port
port = 443
# Bind to the port
s.bind((host, port))        
# Allow up to ten messages stcked up
s.listen(10)                 

# Now wait for client connection.
print("DEBUG: Started on:", (host, port))
print("DEBUG: Ready for clients")

while True:
    # Blocking call, waits to accept a connection
    conn, addr = s.accept()
    # Log it
    print("NETWORK: Connected to " + addr[0] + ":" + str(addr[1]))
    # Start a new thread to new client
    threading.Thread(target=on_new_client, args=(conn,addr)).start()
    print("\nDEBUG: Started new thread") 
    # Main thread continues listening loop to assingn new threads to new clients

# In the rare case we are here, close down the server socket gracefully and then quit
s.close()