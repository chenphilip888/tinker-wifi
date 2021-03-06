#!/usr/bin/python

import select
import socket
import ASUS.GPIO as GPIO
import time
import sys
import Queue

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(32, GPIO.OUT)

pwm = GPIO.PWM(32, 50)
pwm.start(2.5)              # min 2.5, max 11.5 180 degrees

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 50007              # Arbitrary non-privileged port

# Create a TCP/IP socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)

# Bind the socket to the port
server.bind((HOST, PORT))

# Listen for incoming connections
server.listen(5)

# Sockets from which we expect to read
inputs = [ server ]

# Sockets to which we expect to write
outputs = [ ]

# Outgoing message queues (socket:Queue)
message_queues = {}

while inputs:

    # Wait for at least one of the sockets to be ready for processing
    readable, writable, exceptional = select.select(inputs, outputs, [])

    # Handle inputs
    for s in readable:

        if s is server:
            # A "readable" server socket is ready to accept a connection
            connection, client_address = s.accept()
            connection.setblocking(0)
            inputs.append(connection)

            # Give the connection a queue for data we want to send
            message_queues[connection] = Queue.Queue()
        else:
            data = s.recv(1024)
            if data:
                # A readable client socket has data
                # print data
                # message_queues[s].put(data)
                if data == "stop":
                        pwm.start(0)
                        message_queues[s].put("Stop ")
                elif data == "middle":
                        pwm.ChangeDutyCycle(7.0)
                        message_queues[s].put("Middle ")
                elif data == "right":
                        pwm.ChangeDutyCycle(2.5)
                        message_queues[s].put("Right ")
                elif data == "left":
                        pwm.ChangeDutyCycle(11.5)
                        message_queues[s].put("Left ")
                else:
                        message_queues[s].put("Error ")
                # Add output channel for response
                if s not in outputs:
                    outputs.append(s)
            else:
                # Interpret empty result as closed connection
                # Stop listening for input on the connection
                if s in outputs:
                    outputs.remove(s)
                inputs.remove(s)
                s.close()

                # Remove message queue
                del message_queues[s]

    # Handle outputs
    for s in writable:
        try:
            next_msg = message_queues[s].get_nowait()
        except Queue.Empty:
            # No messages waiting so stop checking for writability.
            outputs.remove(s)
        else:
            s.send(next_msg)
