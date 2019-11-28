import socket
import select
import msvcrt
import sys
import re

IP = '127.0.0.1'
PORT = 23
enter = False
message = "Typing: "
space = " "
connected_sockets = []
muted= False


def get_name():
    """This function is called when a new user has joined and needs to give his name. It
    returns the name if it is a valid name """
    got_name = False
    name = ''
    manage = ''
    while not got_name:
        name = raw_input("Please enter the name you want: ")
        if name == 'power' and manage == '':
            print "unlocked manager mode! THE POWER IS IN YOUR HANDS"
            manage = '@'
            name = raw_input("Now enter the name everyone is going to see: ")
        if '/' in name or '@' in name:
            print "Error, sorry username cannot include / or @"
            continue
        if len(name) == 0:
            print 'Error, sorry the username field can not be empty!'
        else:
            got_name = True
    print
    return name + manage


def message_in(server_message):
    """This function is being called once a message has been received and it
    deletes the entire line, puts the message over it and then the typing line under
    the message recieved. Returns True if a person is muted and closes connection if needed."""
    if server_message == 'exterminate':
        my_socket.close()
    print "\r" + space * len(message) + "\r",
    print server_message
    print message,
    if server_message == 'mute' or muted:
        return True
    return False


def enter_pressed():
    """This function is called once the enter key pressed. The function deletes
    the whole current Typing: line since the message has been sent. The function returns True
    if the user requested to quit the chat and false otherwise."""
    global message
    operation = '1'
    input_without_typing = message[8::]
    if re.search('kick:.*', input_without_typing):
        operation = '2'
    if re.search('manager:.*', input_without_typing):
        operation = '3'
    if re.search('mute:.*', input_without_typing):
        operation = '4'
    if re.search('!secret!:.*:.*', input_without_typing):
        operation = '5'
    if re.search('view-managers', input_without_typing):
        operation = '6'
    if input_without_typing == 'quit':
        print "\r\nThank you for using our chat we hope you enjoyed!"
    if muted and input_without_typing != 'quit':
        return False
    build_message = user_name + "/" + operation + "/" + input_without_typing
    my_socket.send(build_message)
    print "\r" + space * len(message) + "\r",
    message = "Typing: "
    print message,
    if input_without_typing == 'quit':
        print "\r" + space * 100 + "\r"
        return True
    return False


user_name = get_name()
my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
my_socket.connect((IP, PORT))
print message,
while True:
    rlist, wlist, xlist = select.select([my_socket], [my_socket], [])
    if len(rlist) != 0:
        message_received = my_socket.recv(1024)
        muted = message_in(message_received)
    if enter:
        quit = enter_pressed()
        if quit:
            my_socket.close()
            break
        elif muted:
            message_in('You can not speak here :(')
        enter = False
    if msvcrt.kbhit():
        char = msvcrt.getch()
        if char == chr(8):
            if len(message) != 8:  # can no longer erase (got to Typing:)
                message = message[:len(message) - 1:]
            print "\r" + message + " " + '\b',
            continue
        if char == chr(13):
            enter = True
            continue
        sys.stdout.write(char)
        message += char
        # print "The message right now is: " + message
