N_PARTIES=3
N_CLIENTS=3
SLEEP_TIME=3

PROTOCOL=semi

# Scripts/setup-ssl.sh $N_PARTIES
# Scripts/setup-clients.sh $N_CLIENTS

echo "Compiling demo_save_data..."
./compile.py demo_save_data || { echo "Compilation failed"; exit 1; }
echo "Compiling demo_query_computation..."
./compile.py demo_query_computation || { echo "Compilation failed"; exit 1; }


# Client 1 request to secret share data
PLAYERS=$N_PARTIES Scripts/$PROTOCOL.sh demo_save_data 2>&1 | tee demo_save_data_server_output.txt &
python3 ExternalDemo/demo_save.py 1 $N_PARTIES 1111
sleep $SLEEP_TIME

# Client 2 request to secret share data
PLAYERS=$N_PARTIES Scripts/$PROTOCOL.sh demo_save_data 2>&1 | tee demo_save_data_server_output.txt &
python3 ExternalDemo/demo_save.py 2 $N_PARTIES 2222
sleep $SLEEP_TIME

# Client 7 request to query computation
PLAYERS=$N_PARTIES Scripts/$PROTOCOL.sh demo_query_computation 2>&1 | tee demo_query_computation_server_output.txt &
python3 ExternalDemo/demo_query.py 7 $N_PARTIES 1
sleep $SLEEP_TIME

# Client 3 request to secret share data
PLAYERS=$N_PARTIES Scripts/$PROTOCOL.sh demo_save_data 2>&1 | tee demo_save_data_server_output.txt &
python3 ExternalDemo/demo_save.py 3 $N_PARTIES 3333
sleep $SLEEP_TIME

# Client 7 request to query computation
PLAYERS=$N_PARTIES Scripts/$PROTOCOL.sh demo_query_computation 2>&1 | tee demo_query_computation_server_output.txt &
python3 ExternalDemo/demo_query.py 7 $N_PARTIES 1
sleep $SLEEP_TIME
