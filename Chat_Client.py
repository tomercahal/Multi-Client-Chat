import socket
import select
import msvcrt
import sys
import re
import os

FIRST_AND_HELP_MESSAGE = '\r\nHi, and welcome to Tomer\'s multi-client chat\r\n' \
                         'You can choose between many different requests from the server. Would you like to:\r\n' \
                         'Send a regular message to everyone, just type your message and press enter\r\n'\
                         'Send a message to a specific user use this syntax: !secret!user:message\r\n' \
                         'Type view-managers to view all the managers as of right now.\r\n\r\n' \
                         'If you are a manager, you have some more options such as:\r\n' \
                         'To kick a user, use this syntax: kick:user\r\n' \
                         'To make a user a manager, use this syntax: manager:user\r\n' \
                         'To mute a user, use this syntax: mute:user\r\n' \
                         'To quit the chat at any time, type quit.\r\nq' \

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


class Client(object):   # This is the Client class
    def __init__(self):
        """The constructor of the client"""
        self.IP = '127.0.0.1'  # The IP of the client.
        self.PORT = 220  # The port that the client and the server are connected on
        self.enter = False  # If the user has pressed enter
        self.message = "Typing: "
        self.space = " "
        self.user_name = ''
        self.connected_sockets = []
        self.muted = False

    def clear_message(self):
        """This function deletes the last output and returns the cursor to it's
        original spot"""
        print '\r' + self.space * len(self.message) + '\r'

    def message_in(self, server_message, my_socket):
        """This function is being called once a message has been received and it
        deletes the entire line, puts the message over it and then the typing line under
        the message recieved. Returns True if a person is muted and closes connection if needed."""
        if server_message == 'exterminate':
            my_socket.close()
            print 'You have been kicked from the chat :('
            os._exit(1)  # clean close so that the client would not get an error
        print "\r" + self.space * len(self.message) + "\r",
        print server_message
        print self.message,
        if server_message == 'mute' or self.muted:
            return True
        return False

    def enter_pressed(self, my_socket):
        """This function is called once the enter key pressed. The function deletes
        the whole current Typing: line since the message has been sent. The function returns True
        if the user requested to quit the chat and false otherwise."""
        operation = '1'
        input_without_typing = self.message[8::]
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
        if self.muted and input_without_typing != 'quit':
            return False
        self.clear_message()
        print 'You: ' + input_without_typing
        build_message = self.user_name + "/" + operation + "/" + input_without_typing
        my_socket.send(build_message)
        self.message = "Typing: "
        print self.message,
        if input_without_typing == 'quit':
            print "\r" + self.space * 100 + "\r"
            return True
        return False

    def start(self):
        self.user_name = get_name()
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_socket.connect((self.IP, self.PORT))
        print FIRST_AND_HELP_MESSAGE  # The first and the help message
        print self.message,
        while True:
            rlist, wlist, xlist = select.select([my_socket], [my_socket], [])
            if len(rlist) != 0:
                message_received = my_socket.recv(1024)
                self.muted = self.message_in(message_received, my_socket)
            if self.enter:
                quit = self.enter_pressed(my_socket)
                if quit:
                    my_socket.close()
                    break
                elif self.muted:
                    self.message_in('You can not speak here :(')
                self.enter = False
            if msvcrt.kbhit():  # Checking for a new char without blocking
                char = msvcrt.getch()  # Getting the char, there is one now
                if char == chr(8):  # Checking if the user has pressed backslash
                    if len(self.message) != 8:  # can no longer erase (got to Typing:)
                        self.message = self.message[:len(self.message) - 1:]
                    print "\r" + self.message + " " + '\b',
                    continue
                if char == chr(13):  # Checking if the user has pressed enter
                    self.enter = True
                    continue
                sys.stdout.write(char)
                self.message += char
                # print "The message right now is: " + message


if __name__ == '__main__':
    client = Client()  # Creating a client
    client.start()  # Using the client's start function
