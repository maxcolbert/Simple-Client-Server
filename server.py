import threading
import sys
from socket import *
import os
import time
from options import options

# SERVER
class Server():
    def __init__(self, server_port):
        # Create Listener
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.bind(('127.0.0.1', server_port))
        self.sock.listen(5)

    def send(self, message):
        # message = [msgType, sender, reciver, money]
        time.sleep(1)
        # Broadcast message to all processes
        print(f'Sending responses to {message}')
        msg = message[1:-1].split(', ')
        for i in range(1, options['NUM_PROCS']+1):
            if ((not i == int(msg[1]) and not msg[0] == 'Transaction' ) or msg[0] == 'Transaction'):
                print(f'Sending response to client {i} on port {options[i]}')
                self.sender = socket(AF_INET, SOCK_STREAM)
                self.sender.connect((options['serverIP'], options[i]))
                self.sender.sendall(message.encode())
                self.sender.close()

    def receive(self):
        while True:
            try:
                stream, addr = self.sock.accept()
                message = stream.recv(4096).decode()
                print("MSG RECV: ", message)
                msg = message[1:-1].split(', ')
                if msg[0] == 'Transaction':
                    stream.send('ACK'.encode())
                if msg[0] == 'Request Reply':
                    time.sleep(1)
                    # simply send confirmation to requester
                    self.sender = socket(AF_INET, SOCK_STREAM)
                    self.sender.connect((options['serverIP'], options[int(msg[2])]))
                    self.sender.sendall(message.encode())
                    self.sender.close()
                    print('Forwarded Request Reply')
                else:
                    self.send(message)
                    print(f'Broadcasted {msg[0]} Message')
            except error:
                print('Error occurred on server.')


server = Server(options['serverPort'])
server.receive()
