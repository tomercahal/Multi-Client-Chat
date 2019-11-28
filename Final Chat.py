import socket
import select
import msvcrt
import re
import datetime

IP = '0.0.0.0'
PORT = 23
server_socket = socket.socket()
server_socket.bind((IP, PORT))
server_socket.listen(5)
#  UNIQUE_ID = 0
#                 VARIABLES                 #
open_client_sockets = []
client_sockets_with_names = []
manager_list = []
messages_to_send = []
#  rlist = able to read from
#  wlist = able to send to
#  xlist = got an error from


def get_time():
    """The function returns the time in the current format: hour:minutes and a space"""
    time_with_seconds = str(datetime.datetime.now().time())
    time_sent = time_with_seconds[:5:] + " "
    return time_sent


def send_left_message(name, way):
    """This function sends a message to all the users that a certin user has left the chat."""
    what_happened = ""
    for receiver_socket in open_client_sockets:
            time_sent = get_time()
            if way == 1:
                what_happened = " has left the chat!"
            if way == 2:
                what_happened = " has been kicked from the chat!"
            receiver_socket.send(time_sent + name + what_happened)  # actual send to the user


def send_waiting_messages():
    """The function sends the waiting messages that need to be sent out,
    onlt if the client's socket it writable"""
    for message in messages_to_send:
        (sender_socket, data, recievers_list) = message
        for reciever_socket in recievers_list:
            if reciever_socket is not sender_socket:
                time_sent = get_time()
                reciever_socket.send(time_sent + data)  # actual send to the user
                recievers_list.remove(reciever_socket)
                if len(recievers_list) == 0:
                    messages_to_send.remove(message)


def decrypt_data(data):
    """The function gets the data from the user and returns all of the parameters from it."""
    print data
    parts = data.split('/')
    print parts
    name = parts[0]
    operation = parts[1]  # for now only 1 (regular message)
    mess = parts[2]
    return name, operation, mess


def kick_person(person_name):
    """A function that kicks a person that is in the param"""
    helper = ''
    for socket in client_sockets_with_names:
        helper = socket[1]  # the name
        if person_name == helper or person_name == helper[:len(helper)-1:]:
            socket[0].send('exterminate')
            open_client_sockets.remove(socket[0])
            client_sockets_with_names.remove(socket)
            print "The connection with " + person_name + " is closed"
            send_left_message(person_name, 2)
            return
    current_socket.send("Sorry we couldn't find: " + person_name + " in the chat users.")


def make_manager(name, current_socket, n):
    """A function that makes a client a manager. It is the name that is in the param"""
    for socket in client_sockets_with_names:
        if name == socket[1]:
            manager_list.append('@' + name)
            print name + " is now a manager"
            socket[0].send("You are now a chat manager, thanks to: " + n)
            current_socket.send(name + " is now a manager!")
            return
    current_socket.send("Sorry we couldn't find: " + name + " in the chat users.")


def mute_person(name, current_socket):
    """A function that mutes a client, it is the client in the param."""
    for socket in client_sockets_with_names:
        if name == socket[1]:
            socket[0].send('mute')
            print name + " is now muted"
            current_socket.send(name + " is now muted.")
            return
    current_socket.send("sorry we couldn't find: " + name + " in the chat users.")


def send_secret_message(user, data, sender_name ,current_socket):
    """This function gets 4 params the user to send the message to, the actual message, the sender's
    name and the socket of the sender. The function sends a secret message to the user intended."""
    stam = ''
    for socket in client_sockets_with_names:
        if '@' in socket[1]:
            stam = socket[1]
            stam = stam[:len(stam)-1:]
        if user == socket[1] or user == stam:
            time_sent = get_time()
            secret_message = time_sent + "!secret! " + sender_name + ": " + data
            socket[0].send(secret_message)
            current_socket.send("The secret message has been sent to: " + user)
            return
    current_socket.send("Sorry we couldn't find: " + user + " in the chat users.")


def analyze_func(name, fun, mess, current_socket):
    """This function is the heart of the server ia analyzes the type of request from the
    client and decides what needs to be sent back to the client and what will happen after."""
    print "Before: " + name
    if '@' in name:
        name = name[:len(name)-1:]
    print "After: " + name
    print manager_list
    if fun == '1':  # Just a regular message
        pass
    elif fun == '2':  # A request from a manager to kick a person
        if '@' + name in manager_list:
            parts = mess.split(":")
            person_kicked = parts[1]
            kick_person(person_kicked)
        else:
            current_socket.send("Error, only chat managers can kick people")
    elif fun == '3':  # Making someone a manager
        print '@' + name
        print manager_list
        if '@' + name in manager_list:
            parts = mess.split(":")
            new_manager = parts[1]
            make_manager(new_manager, current_socket, name)
        else:
            current_socket.send("Error, only chat managers can make other people managers")
    elif fun == '4':  # Mutes another user in the chat
        if '@' + name in manager_list:
            parts = mess.split(":")
            muted_person = parts[1]
            mute_person(muted_person, current_socket)
        else:
            current_socket.send("Error, only chat managers can mute other people")
    elif fun == '5':  # Sending a secret message to another user
        parts = mess.split(":")
        send_to = parts[1]
        message_data = parts[2]
        send_secret_message(send_to, message_data, name,current_socket)
    elif fun == '6':  # Shows a list of the current managers
        final_send = 'The managers are: '
        for manager in manager_list:
            final_send = final_send + "\r\n" + manager
        if len(manager_list) == 0:
            current_socket.send("The chat does not have any managers right now.")
        else:
            current_socket.send(final_send)


while True:
    rlist, wlist, xlist = select.select([server_socket] + open_client_sockets, open_client_sockets, [])
    for current_socket in rlist:
        if current_socket is server_socket:
            print "New client in!"
            (new_socket, address) = server_socket.accept()
            open_client_sockets.append(new_socket)
        else:
            data = current_socket.recv(1024)
            username, func, message = decrypt_data(data)  # gets all the parts of the data
            if current_socket not in client_sockets_with_names:
                client_sockets_with_names.append((current_socket, username))
            print username, func, message
            if '@' in username:
                if '@' + username[:len(username)-1:] not in manager_list:
                    manager_list.append('@' + username[:len(username)-1:])
            if message == "quit":
                open_client_sockets.remove(current_socket)
                client_sockets_with_names.remove((current_socket, username))
                print "The connection with the client is closed!"
                send_left_message(username, 1)
                continue
            analyze_func(username, func, message, current_socket)
            if func == '1':
                if '@' in username:
                    username = username[:len(username)-1:]
                if '@' + username in manager_list:
                    username = '@' + username
                messages_to_send.append((current_socket, username + ": " + message, wlist))

    send_waiting_messages()
