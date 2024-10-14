#!/usr/bin/python3

import sys

sys.path.append('.')

from client import *
from domains import *

client_id = int(sys.argv[1])
n_parties = int(sys.argv[2])
computationIndex = int(sys.argv[3])
MAX_NUM_CLIENTS = 10


client = Client(['localhost'] * n_parties, 14000, client_id)

for socket in client.sockets:
    os = octetStream()
    # computationIndex is public, not need to be secret shared.
    os.store(computationIndex)
    os.Send(socket)

def run():
    output_list = client.receive_outputs(1+MAX_NUM_CLIENTS)
    print('Computation index',computationIndex, "is", output_list[0])
    for i in range(MAX_NUM_CLIENTS):
        print('commitment: ',i, 'is', output_list[i+1])
    # print('commitment index is', client.receive_outputs(2)[1])

# running two rounds
# first for sint, then for sfix
run()
# run(bonus * 2 ** 16)
