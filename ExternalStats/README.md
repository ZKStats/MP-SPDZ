**Statistics operations with client Example**
This folder is for doing client interface with statistics function where client does nothing but getting the output.

Here, we consider 2 servers with private data doing MPC together, only to output to the client.
We input private data of these 2 servers in Player-Data/Input-P0-0, and Player-Data/Input-P1-0. For example, you can just put 0 1 2 3 170 160 152 180 in Player-Data/Input-P0-0, and 3 0 4 5 50 60 70 100 in Player-Data/Input-P1-0

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

**BenchMark**
We compare this 2 servers + 1 client implementation with naive 2 servers in stats-noclient.mpc in Programs/Source and get the following results

With Client

- Data sent = 3.28978 MB in ~158 rounds (party 0 only; use '-v' for more details)
  Global data sent = 6.59185 MB (all parties)

Without Client

- Data sent = 3.28973 MB in ~154 rounds (party 0 only; use '-v' for more details)
  Global data sent = 6.59176 MB (all parties)

Hence, the overhead is very small. Again the trust assumption of client-interface only depends on the computing servers

**Issues**

- However, when we run without client version with main.py, the amount of data skyrocket to - Data sent = 4.77346 MB in ~214 rounds (party 0 only; use '-v' for more details)
  Global data sent = 9.55921 MB (all parties)
  This is likely due to

  ```
  compiler = Compiler()
  compiler.register_function(PROGRAM_NAME)(computation)
  compiler.compile_func()
  ```

  inside main.py

**Observation**

- We use sfix instead of sint in our program because stats operation likely results in floating number, hence the result the client receives is already multiplied by the scale. For example, if the result is 55., the client will receive 55\*2^16 ~ 3604480
- Anyway, by default, sfix is also faster than sint: https://github.com/data61/MP-SPDZ/issues/1400#issuecomment-2107550939
