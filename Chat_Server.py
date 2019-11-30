import socket
import select
import datetime


def get_time():
    """The function returns the time in the current format: hour:minutes and a space"""
    time_with_seconds = str(datetime.datetime.now().time())
    time_sent = time_with_seconds[:5:] + " "
    return time_sent


def decrypt_data(data):
    """The function gets the data from the user and returns all of the parameters from it."""
    parts = data.split('/')
    name = parts[0]
    operation = parts[1]  # for now only 1 (regular message)
    mess = parts[2]
    return name, operation, mess


class Server(object):  # This is the server class
    def __init__(self):
        """The constructor method of the server class"""
        self.IP = '127.0.0.1'  # maybe will have to change to 0.0.0.0
        self.PORT = 220
        self.open_client_sockets = []
        self.client_sockets_with_names = []
        self.manager_list = []
        self.messages_to_send = []

    def send_left_message(self, name, way):
        """This function sends a message to all the users that a certain user has left the chat. The input is the name
        of the user that is leaving plus the way he left."""
        what_happened = ""
        for receiver_socket in self.open_client_sockets:
                time_sent = get_time()
                if way == 1:  # If it is 1 it means that he just left the chat
                    what_happened = " has left the chat!"
                if way == 2:  # If it is 2 it means that he was kicked by a manager
                    what_happened = " has been kicked from the chat!"
                receiver_socket.send(time_sent + name + what_happened)  # actual send to the each user
       
    def send_waiting_messages(self):
        """The function sends the waiting messages that need to be sent out,
        only if the client's socket is writable"""
        for message in self.messages_to_send:
            (sender_socket, data, recievers_list) = message
            for reciever_socket in recievers_list:
                if reciever_socket is not sender_socket:
                    time_sent = get_time()
                    reciever_socket.send(time_sent + data)  # actual send to the user
                    recievers_list.remove(reciever_socket)
                    if len(recievers_list) == 0:
                        self.messages_to_send.remove(message)
    
    def kick_person(self, person_name, current_socket):
        """A function that kicks a person that is in the param"""
        helper = ''
        for socket in self.client_sockets_with_names:
            helper = socket[1]  # the name
            if person_name == helper or person_name == helper[:len(helper)-1:]:
                socket[0].send('exterminate')
                self.open_client_sockets.remove(socket[0])
                self.client_sockets_with_names.remove(socket)
                print "The connection with " + person_name + " is closed"
                self.send_left_message(person_name, 2)
                return
        current_socket.send("Sorry we couldn't find: " + person_name + " in the chat users.")  
    
    def make_manager(self, name, current_socket, n):
        """A function that makes a client a manager. It is the name that is in the param"""
        for socket in self.client_sockets_with_names:
            if name == socket[1]:
                self.manager_list.append('@' + name)
                print name + " is now a manager"
                socket[0].send("You are now a chat manager, thanks to: " + n)
                current_socket.send(name + " is now a manager!")
                return
        current_socket.send("Sorry we couldn't find: " + name + " in the chat users.")   
    
    def mute_person(self, name, current_socket):
        """A function that mutes a client, it is the client in the param."""
        for socket in self.client_sockets_with_names:
            if name == socket[1]:
                socket[0].send('mute')
                print name + " is now muted"
                current_socket.send(name + " is now muted.")
                return
        current_socket.send("sorry we couldn't find: " + name + " in the chat users.")  
    
    def send_secret_message(self, user, data, sender_name ,current_socket):
        """This function gets 4 params the user to send the message to, the actual message, the sender's
        name and the socket of the sender. The function sends a secret message to the user intended."""
        stam = ''
        for socket in self.client_sockets_with_names:
            if '@' in socket[1]:
                stam = socket[1]
                stam = stam[:len(stam)-1:]  # Just getting read of unnecessary parts for the print
            if user == socket[1] or user == stam:
                time_sent = get_time()
                secret_message = time_sent + "!secret! " + sender_name + ": " + data
                socket[0].send(secret_message)
                current_socket.send("The secret message has been sent to: " + user)
                return
        current_socket.send("Sorry we couldn't find: " + user + " in the chat users.")
    
    def analyze_func(self, name, fun, mess, current_socket):
        """This function is the heart of the server ia analyzes the type of request from the
        client and decides what needs to be sent back to the client and what will happen after."""
        if '@' in name:
            name = name[:len(name)-1:]  # Fixing a bug that caused other users not able to see the @ of the manager
        print name + ' sent: ' + mess
        if fun == '1':  # Just a regular message
            pass
        elif fun == '2':  # A request from a manager to kick a person
            if '@' + name in self.manager_list:
                parts = mess.split(":")
                person_kicked = parts[1]
                self.kick_person(person_kicked, current_socket)
            else:
                current_socket.send("Error, only chat managers can kick people")
        elif fun == '3':  # Making someone a manager
            if '@' + name in self.manager_list:
                parts = mess.split(":")
                new_manager = parts[1]
                self.make_manager(new_manager, current_socket, name)
            else:
                current_socket.send("Error, only chat managers can make other people managers")
        elif fun == '4':  # Mutes another user in the chat
            if '@' + name in self.manager_list:
                parts = mess.split(":")
                muted_person = parts[1]
                self.mute_person(muted_person, current_socket)
            else:
                current_socket.send("Error, only chat managers can mute other people")
        elif fun == '5':  # Sending a secret message to another user
            parts = mess.split(":")
            send_to = parts[1]
            message_data = parts[2]
            self.send_secret_message(send_to, message_data, name,current_socket)
        elif fun == '6':  # Shows a list of the current managers
            final_send = 'The managers are: '
            for manager in self.manager_list:
                final_send = final_send + "\r\n" + manager  # Just making the output prettier
            if len(self.manager_list) == 0:
                current_socket.send("The chat does not have any managers right now.")
            else:
                current_socket.send(final_send)

    def start(self):
        """This function......."""
        print('Server starting up on ip %s port %s' % (self.IP, self.PORT))
        server_socket = socket.socket()
        server_socket.bind((self.IP, self.PORT))
        server_socket.listen(1)
        while True:
            rlist, wlist, xlist = select.select([server_socket] + self.open_client_sockets, self.open_client_sockets, [])
            #  rlist = able to read from
            #  wlist = able to send to
            #  xlist = got an error from
            for current_socket in rlist:
                if current_socket is server_socket:
                    print "\r\nNew client in!"
                    (new_socket, address) = server_socket.accept()  # Accepting the new user
                    self.open_client_sockets.append(new_socket)  # Adding the new client to the sockets I can conatct with list
                else:
                    data = current_socket.recv(1024)  # Gets the data from the user
                    username, func, message = decrypt_data(data)  # gets all the parts of the data
                    if current_socket not in self.client_sockets_with_names:
                        self.client_sockets_with_names.append((current_socket, username))  # Adding him
                    if '@' in username:  # If he is a manager
                        if '@' + username[:len(username)-1:] not in self.manager_list:  # checking if he is a manager
                            self.manager_list.append('@' + username[:len(username)-1:])
                    if message == "quit":  # If the client has asked to leave
                        self.open_client_sockets.remove(current_socket)  # Removing the client from the sockets to send to
                        self.client_sockets_with_names.remove((current_socket, username))
                        print "The client: " + username + ", has disconnected "
                        self.send_left_message(username, 1)  # Sending to the rest of the users that the user left.
                        continue
                    self.analyze_func(username, func, message, current_socket)
                    if func == '1':
                        if '@' in username:  # Checking if he is a manager
                            username = username[:len(username)-1:]
                        if '@' + username in self.manager_list:  # Checking if he is in the managers list
                            username = '@' + username
                        self.messages_to_send.append((current_socket, username + ": " + message, wlist))  # Adding to managers list

            self.send_waiting_messages()  # Sending the messages that are still waiting to be sent


if __name__ == '__main__':
    s = Server()  # Starting up the server
    s.start()  # The first function that handles the clients inside the server
