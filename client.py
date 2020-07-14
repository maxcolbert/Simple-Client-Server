import threading
import ipaddress
import queue
from socket import *
from options import options
import sys
import time

# INSTRUCTIONS:
# Must run this file via:   python client_tcp.py 1
# this will set process ID to 1
# END INSTRUCTIONS

###   (START) USED TO SET CLIENT ID   ###
# take command line input
inp_clientID = 1
try:
    inp_clientID = int(sys.argv[1:][0])
except:
    inp_clientID = 1
###   (END) USED TO SET CLIENT ID   ###

# Blockchain Nodes
class Node:
    def __init__(self, sender, receiver, amt):
        self.sender = sender
        self.reciever = receiver
        self.amt = amt
        self.next = None

# Linked List Transaction Storage
class Blockchain:
    def __init__(self):
        self.head = None
        self.tail = None

    def append(self, sendr, rcvr, amt):
        tmp = Node(sendr, rcvr, amt)
        if self.head:
            self.tail.next = tmp
            self.tail = tmp
        else:
            self.head = tmp
            self.tail = self.head

    def printchain(self):
        printer = self.head
        msg = '['
        while printer:
            msg += f'(P{printer.sender}, '
            msg += f'P{printer.reciever}, '
            msg += f'${printer.amt}), '
            printer = printer.next
        msg += ']'
        print(msg)

class Client():
    def __init__(self, num):
        self.num = num
        self.balance = 10
        self.chain = Blockchain()
        self.queue = []
        self.replies = 1
        # Socket
        self.sock = socket(AF_INET, SOCK_STREAM)
        print("BINDING: ", self.num, " ... ", options[inp_clientID])
        self.sock.bind((options['serverIP'], options[inp_clientID]))
        self.sock.listen(5)
        
    def printChain(self):
        self.chain.printchain()

    def sendReply(self, msg):
        # connect to server, send reply
        sender = socket(AF_INET, SOCK_STREAM)
        sender.connect((options['serverIP'], options['serverPort']))
        sender.sendall(msg.encode())
        sender.close()
        
    def send(self, msg):
        # msg format: [type, sender, recvr, amt]
        check = msg[1:-1].split(', ')
        # Insufficient Balance
        if int(check[3]) > self.balance:
            print('Failure: Insufficient Funds')
            return
        print('Continuing. Sufficient Funds...')
        # Request Blockchain Access
        rqst = f'[Request, {self.num}, NULL, NULL]'
        self.queue.append(self.num)
        # Reset Replies
        self.replies = 1
        # Connect + Request Server
        sender = socket(AF_INET, SOCK_STREAM)
        sender.connect((options['serverIP'], options['serverPort']))
        sender.sendall(rqst.encode())
        # Wait until all replies received and top of queue
        while (self.replies != options['NUM_PROCS'] or self.queue[0] != self.num):
            # print(f'Waiting for access ...')
            time.sleep(0.5)
        # print(f'Received blockchain access.')
        # Connect to server
        sender = socket(AF_INET, SOCK_STREAM)
        sender.connect((options['serverIP'], options['serverPort']))
        # Broadcast Transaction
        sender.sendall(msg.encode())
        # self.chain.append(check[1], check[2], int(check[3]))
        # self.balance -= int(check[3])
        # print(f'Processed Transaction {msg}.')
        # Receive ACK from server to send release, this enables pause
        response = sender.recv(1024).decode()
        # Release Blockchain Access
        rls = f'[Release, {self.num}, NULL, NULL]'
        sender = socket(AF_INET, SOCK_STREAM)
        sender.connect((options['serverIP'], options['serverPort']))
        self.queue.pop(0)
        # assert(self.queue.pop(0) == self.num)
        sender.sendall(rls.encode())
        sender.close()
        # print('Sent release & closed')

    # Communication Thread
    def receive(self):
        while True:
            try:
                stream, addr = self.sock.accept()
                message = stream.recv(1024).decode()
                msg = message[1:-1].split(', ')
                # print("MSG RECV: ", message)
                # msg format: [type, sender, recvr, amt]
                if msg[0] == 'Transaction':
                    # if not int(msg[1]) == self.num:
                    self.chain.append(msg[1], msg[2], int(msg[3]))
                    if int(msg[2]) == self.num:
                        self.balance += int(msg[3])
                    if int(msg[1]) == self.num:
                        self.balance -= int(msg[3])
                elif msg[0] == 'Request':
                    self.sendReply(f'[Request Reply, {self.num}, {msg[1]}, NULL]')
                    stream.close()
                    self.queue.append(int(msg[1]))
                elif msg[0] == 'Release':
                    self.queue.pop(0)
                    # assert(self.queue.pop(0) == int(msg[1]))
                elif msg[0] == 'Request Reply':
                    self.replies += 1
                stream.close()
            except timeout:
                stream.close()
            except error:
                stream.close()

# SET UP client:
client = Client(inp_clientID)

pro1 = threading.Thread(target=client.receive)
pro1.daemon = True
pro1.start()

while True:
    print('Input 1 to send, 2 to print chain, 3 to print balance, or 4 to quit:')
    inp = int(input())
    if (inp == 1):
        print('Select Receiver ID (1, 2, 3):')
        receiverID = int(input())
        print('State send amount:')
        amt = int(input())
        msg = f'[Transaction, {client.num}, {receiverID}, {amt}]'        
        sendThread = threading.Thread(target=client.send, args=(msg, ))
        sendThread.daemon = True
        sendThread.start()
    elif (inp == 2):
        client.printChain()
    elif (inp == 3):
        print('Amount: $', client.balance)
    elif (inp == 4):  # Working
        sys.exit()
    else:
        print('Invalid...')
