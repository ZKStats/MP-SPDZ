from common_lib import create_party_data_files, get_aggr_party_data_vec, write_result, datasets_dir
from mpcstats_lib import mean

NUM_PARTIES = 3
ROW_INDEX = 1

def prepare_data():
    dataset_file = datasets_dir / 'wine' / 'wine.data.txt'
    create_party_data_files(dataset_file, NUM_PARTIES)

def computation():
    vec = get_aggr_party_data_vec(NUM_PARTIES, ROW_INDEX) 
    res = mean(vec)
    write_result(res.reveal())

