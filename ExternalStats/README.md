This folder is for doing client interface with statistics function where client does nothing but getting the output.

Here, we consider 2 servers with private data doing MPC together, only to output to the client.
We input private data of these 2 servers in Player-Data/Input-P0-0, and Player-Data/Input-P1-0

Run the following commands

```
make stats-client.x
./compile.py stats-client
Scripts/setup-ssl.sh 2
Scripts/setup-clients.sh 1
PLAYERS=2 Scripts/semi.sh stats-client
./stats-client.x 0 2 1
```

Commands above do the following

- make stats-client.x : Run Makefile to handle stats-client.cpp in folder ExternalStats
- ./compile.py stats-client: Compile stats-client.mpc file in Programs/Source
- Scripts/setup-ssl.sh 2: Create triple shares for each party (spdz engine). 2 means 2 computing servers
- Scripts/setup-clients.sh 1: Create SSL keys and certificates for clients. 1 means 1 client
- PLAYERS=2 Scripts/semi.sh stats-client: Run server engines
- ./stats-client.x 0 2 1: Run client. 0 means client index 0, 2 means number of party, 1 means finish (dont need to wait for more clients)
