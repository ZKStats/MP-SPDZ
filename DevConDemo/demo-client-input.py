#!/usr/bin/python3

import sys

sys.path.append('.')

from client import *
from domains import *

client_id = int(sys.argv[1])
n_parties = int(sys.argv[2])
# isInput = int(sys.argv[3])
bonus = int(sys.argv[3])

client = Client(['localhost'] * n_parties, 14000, client_id)

for socket in client.sockets:
    os = octetStream()
    os.store(0)
    os.Send(socket)

def reverse_bytes(integer):
    # Convert integer to bytes, assuming it is a 32-bit integer (4 bytes)
    byte_length = (integer.bit_length() + 7) // 8 or 1
    byte_representation = integer.to_bytes(byte_length, byteorder='big')
    
    # Reverse the byte order
    reversed_bytes = byte_representation[::-1]
    
    # Convert the reversed bytes back to an integer
    reversed_integer = int.from_bytes(reversed_bytes, byteorder='big')
    
    return reversed_integer

def run(x):
    nonce = 19025386729892471294905774323873829730555352566281815376957579075809073893907
    client.send_private_inputs([x, reverse_bytes(nonce)])
    print("finish sending private inputs")
    # print('Winning client id is :', client.receive_outputs(1)[0])

# running two rounds
# first for sint, then for sfix
run(bonus)
# run(bonus * 2 ** 16)
