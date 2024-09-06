from dataclasses import dataclass
from pathlib import Path
import subprocess
import json

from Compiler.compilerLib import Compiler
from Compiler.types import sint, Array
from Compiler.GC.types import sbitvec, sbits
from Compiler.library import print_ln, for_range
from Compiler.circuit import sha3_256



@dataclass(frozen=True)
class TLSNProof:
    # private to party
    followers: int
    # public
    proof_path: Path
    delta: str
    zero_encodings: list[str]
    hash: int
    nonce: int


FILE_DIR = Path(__file__).parent
TLSN_PROJECT_ROOT = FILE_DIR.parent / 'tlsn'
# ls tlsn/examples
EXAMPLE_DIR = TLSN_PROJECT_ROOT / 'tlsn' / 'examples' / 'simple'
CMD_GEN_TLSN_PROOF = "cargo run --release --example simple_prover"
CMD_VERIFY_TLSN_PROOF = "cargo run --release --example simple_verifier"


MPSPDZ_PROJECT_ROOT = FILE_DIR
MPSPDZ_CIRCUIT_DIR = MPSPDZ_PROJECT_ROOT / 'Programs' / 'Source'


MPC_PROTOCOL = 'semi'
LOCAL_RUN = MPSPDZ_PROJECT_ROOT / "Scripts" / f"{MPC_PROTOCOL}.sh"
CIRCUIT_NAME = 'auth_with_tlsn'

NUM_PARTIES = 3
PARTY_DATA_DIR = MPSPDZ_PROJECT_ROOT / "Player-Data"
PARTY_DATA_DIR.mkdir(parents=True, exist_ok=True)


NUM_REDACTED_BYTES = 2
WORD_SIZE = 16
WORDS_PER_LABEL = 8

COMMITMENT_HASH_SIZE = 32


def prepare_player_data(proofs: list[TLSNProof]):
    assert len(proofs) == NUM_PARTIES
    for i, proof in enumerate(proofs):
        party_data_file = PARTY_DATA_DIR / f"Input-P{i}-0"
        with open(party_data_file, "w") as f_data:
            f_data.write(f"{proof.followers}\n")


def generate_tlsn_proofs() -> list[TLSNProof]:
    # Run the tlsn proof generation command
    proofs = []
    for party_index in range(NUM_PARTIES):
        print(f"Generating TLSN proof for party {party_index}")
        proof_file = FILE_DIR / f"tlsn-proof-p{party_index}.json"
        try:
            res = subprocess.run(
                f"cd {EXAMPLE_DIR} && {CMD_GEN_TLSN_PROOF} {party_index} {proof_file}",
                shell=True, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")
            print(f"stdout:\n{e.stdout}")
            print(f"stderr:\n{e.stderr}")
            exit(1)
        # Parse the output and get this line "Party {} has {} followers"
        followers_line = next((line for line in res.stdout.splitlines() if line.startswith(f"Party {party_index} has ")), None)
        if not followers_line:
            raise ValueError(f"Could not find followers line for party {party_index}")
        followers = int(followers_line.split()[3])
        with open(proof_file, "r") as f_proof:
            proof_data = json.load(f_proof)
            private_openings = proof_data["substrings"]["private_openings"]
            assert len(private_openings) == 1, f"Expected 1 private opening, got {len(private_openings)}"
            commitment_index, openings = list(private_openings.items())[0]
            commitment_info, commitment = openings
            data_commitment_hash = bytes(commitment["hash"]).hex()
            data_commitment_nonce = bytes(commitment["nonce"]).hex()

            encodings = proof_data["encodings"]
            assert len(encodings) == NUM_REDACTED_BYTES, f"Expected {NUM_REDACTED_BYTES} bytes in encodings, got {len(encodings)}"
            for e in encodings:
                delta = e["U8"]["state"]["delta"]
                labels = e["U8"]["labels"]
                assert len(delta) == WORD_SIZE, f"Expected {WORD_SIZE} bytes in delta, got {len(delta)}"
                delta_hex = bytes(delta).hex()
                assert len(labels) == WORDS_PER_LABEL, f"Expected {WORDS_PER_LABEL} labels, got {len(labels)}"
                all_labels = []
                for l in labels:
                    assert len(l) == WORD_SIZE, f"Expected {WORD_SIZE} bytes in label, got {len(l)}"
                    label_hex = bytes(l).hex()
                    all_labels.append(label_hex)
        proofs.append(
            TLSNProof(
                followers=followers,
                proof_path=proof_file,
                delta=delta_hex,
                zero_encodings=all_labels,
                hash=data_commitment_hash,
                nonce=data_commitment_nonce
            )
        )
    return proofs



def compile_run(computation):
    compiler = Compiler()
    compiler.register_function(CIRCUIT_NAME)(computation)
    compiler.compile_func()

    # check if the circuit file exists
    # circuit_file = MPSPDZ_CIRCUIT_DIR / f"{CIRCUIT_NAME}.mpc"
    # if not circuit_file.exists():
    #     raise FileNotFoundError(f"Circuit file {circuit_file} not found")
    try:
        command = f"PLAYERS={NUM_PARTIES} {LOCAL_RUN} {CIRCUIT_NAME}"
        print(f"Running command: {command}")
        res = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        print(f"stdout:\n{e.stdout}")
        print(f"stderr:\n{e.stderr}")
        exit(1)
    # Parse the output
    # output: avg_followers = 15
    # Reg[8] = 0xed7ec2253e5b9f15a2157190d87d4fd7f4949ab219978f9915d12c03674dd161 #
    # Reg[4] = 0xec6b82369f30ad1d25022d87ac5cc825995dba1e140390392b0d948d30f672a6 #
    # Reg[0] = 0x28059a08d116926177e4dfd87e72da4cd44966b61acc3f21870156b868b81e6a #
    output_lines = res.stdout.split('\n')
    avg_followers = None
    commitments = []
    for line in output_lines:
        # Case for 'output: avg_followers = 15'
        if line.startswith('output: avg_followers = '):
            avg_followers = int(line.split('=')[1].strip())
        # Case for 'Reg[0] = 0x28059a08d116926177e4dfd87e72da4cd44966b61acc3f21870156b868b81e6a #'
        elif line.startswith('Reg['):
            # 0xed7ec2253e5b9f15a2157190d87d4fd7f4949ab219978f9915d12c03674dd161 #
            after_equal = line.split('=')[1].strip()
            # ed7ec2253e5b9f15a2157190d87d4fd7f4949ab219978f9915d12c03674dd161
            reg_value = after_equal.split(' ')[0][2:]
            commitments.append(reg_value)

    print(f"stdout: {res.stdout}")
    # Extract the variables
    if avg_followers is None:
        raise ValueError("Missing avg_followers in MP-SPDZ output")
    if len(commitments) != NUM_PARTIES:
        raise ValueError(f"Missing commitments for all parties, expected {NUM_PARTIES}, got {len(commitments)}")
    return avg_followers, commitments


def verify_tlsn_proofs(proofs: list[TLSNProof], commitments_mpspdz: list[int]):
    assert len(proofs) == NUM_PARTIES
    for party_index, proof in enumerate(proofs):
        # Verify TLSN proof for party
        try:
            subprocess.run(
                f"cd {EXAMPLE_DIR} && {CMD_VERIFY_TLSN_PROOF} {proof.proof_path}",
                shell=True, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")
            print(f"stdout:\n{e.stdout}")
            print(f"stderr:\n{e.stderr}")
            exit(1)
        # Get the first (and only) data commitment from the TLSN proof
        commitment_tlsn = proof.hash
        commitment_mpspdz = commitments_mpspdz[party_index]
        print(f"party {party_index}: commitment_tlsn = {commitment_tlsn}")
        print(f"party {party_index}: commitment_mpspdz = {commitment_mpspdz}")
        # FIXME: Check calculated commitments from MP-SPDZ output match the ones in TLSN proofs
        # assert commitment_tlsn == commitment_mpspdz, f"Commitment encoding does not match for party {party_index}"


def main():
    # proofs = generate_tlsn_proofs()
    # print(f"Proofs: {proofs}")
    proofs = [
        TLSNProof(followers=10, proof_path=FILE_DIR / 'tlsn-proof-p0.json', delta='d36d53dada9156e0b06758f143623839', zero_encodings=['0386109eea524dd7c70ddeed7c4978ba', '0b88173f5667ff26ae9258fde0eff735', '5e9781f88c98d8a09089710c075e9c09', 'd42d2ce9e55ef14b9d6b5cf8fc669ded', 'aa212f7c88c954c84e13405b1ca2af10', '3d9f3ce5cca1cbc27826909a9e70d930', 'a50050ff300f9dee6cf902d66e13cf14', '50b216bb1ec747a9951b06e4bc9bffe5'], hash='fdad7b9374ca5843d5364b3c3d7ea680d3bce0ad85daba93ec60735bbd109c47', nonce='8ee24f0a12c839cca607dd825cb0ed02e8ef5c3682537279bdc59aefa05b19c7'),
        TLSNProof(followers=14, proof_path=FILE_DIR / 'tlsn-proof-p1.json', delta='29c5b16b2a8a90c74f621658b42d9d99', zero_encodings=['0114f9b7900a22442dd6b365c595dba9', 'cc9ed62bf7a91898d8ed77f7fb4befda', '9f20bfb2baddc0cbd3326b0cb97ed9b6', '1fd3bccb52ed35abca50581f6cead317', '21c03c26a5e0dee2e4000fbfe55e6993', '41d119aff4a2863c72dc1f9861017ed7', '94ebde1268dcf501c9680af1867fbbc0', 'c57dbd7901751f07c0a368c938a34093'], hash='8f3a3d8cbf6041c80b0d30751439d9f4be583dcff1b1f0090905c72d4daeccc0', nonce='75ed4c01732977f9e150ad013233665458d2aaf408528199a37b2dce923973c4'),
        TLSNProof(followers=21, proof_path=FILE_DIR / 'tlsn-proof-p2.json', delta='1735ee5903a44adbc1a48ea4d74fc352', zero_encodings=['13decd93e09d1ce104e8fe220c427313', 'b3cefbca0b171b32bc81330bb85f1a48', 'cbf6a9afa99e72a816b667e979a6128f', '3b15fe00aca04319535f92e1bc8f21df', '9feb755b737f4205da6dc739332e60f1', '12d34a49f87f9d9355f55c145eade67a', 'd90c7943cb1f18056c17fcc0d4477d2b', '3b1ba36d14c05597115b0cb79bc40b21'], hash='711bab8b9684d3493ac8775d9ca29dd407c9d080f9094b9a188a69a333038e2f', nonce='7507b6c2576c6ffd445cec7bcdc6a1b2b0264b1f74fbfb71125b4a3c20d7a75b'),
    ]
    prepare_player_data(proofs)

    # MP-SPDZ circuit
    def computation():
        def calculate_data_commitment(followers: sint, delta: sbitvec, encoding: list[sbitvec], nonce: sbitvec):
            # `followers` is "Data" and `encoding` is the "Full Encoding"
            # Active coding is calculated from `followers` and `encoding`.
            # Ref:
            #   - docs: https://docs.tlsnotary.org/mpc/commitments.html#commitments
            #   - code: https://github.com/tlsnotary/tlsn/blob/e14d0cf563e866cde18d8cf7a79cfbe66d220acd/crates/core/src/commitment/blake3.rs#L76-L80
            
            # FIXME: Now, we only assume that length >= len(encoding) which depends on plain text
            length =  16 # Vary on the maximum length of plain text SHOULD BE BIGGER than this value!! but here we let it be 16
            ENCODE_BIT_LEN = 128 # since each encoding[i] is 128 bits.
            big_num = sint(2**ENCODE_BIT_LEN-1) 
            followers_bits= sbitvec(followers, length)
            followers_bits_list = [sint(ele) for ele in followers_bits.v]
            # print_ln('Print follower bits')
            # @for_range(length)
            # def _(i):
            #     print_ln('bittt : %s',followers_bits_list[i].reveal())
            
            active_encoding:list[sbitvec] = []
            for i in range(len(encoding)):
                # if followers_bits_arr[i] = 0--> big_num+1 overflows 128 bits, seeing only all 0
                # On the other hand, big_num still have 1 for all 128 bits
                nullifier = sbitvec(big_num+sint(1)-followers_bits_list[i], ENCODE_BIT_LEN)
                active_encoding.append(encoding[i].bit_xor(delta.bit_and(nullifier)))
            
            # # FIXME: Now do concat with nounce and then hash
            return sha3_256(delta + nonce)

        # Private inputs
        followers_0 = sint.get_input_from(0)
        followers_1 = sint.get_input_from(1)
        followers_2 = sint.get_input_from(2)

        # Public inputs
        nonce_0 = sbitvec.from_hex(proofs[0].nonce)
        nonce_1 = sbitvec.from_hex(proofs[1].nonce)
        nonce_2 = sbitvec.from_hex(proofs[2].nonce)
        delta_0 = sbitvec.from_hex(proofs[0].delta)
        delta_1 = sbitvec.from_hex(proofs[1].delta)
        delta_2 = sbitvec.from_hex(proofs[2].delta)
        zero_encodings_0 = [sbitvec.from_hex(e) for e in proofs[0].zero_encodings]
        zero_encodings_1 = [sbitvec.from_hex(e) for e in proofs[1].zero_encodings]
        zero_encodings_2 = [sbitvec.from_hex(e) for e in proofs[2].zero_encodings]

        # Calculation
        avg_followers = (followers_0 + followers_1 + followers_2) / 3
        commitment_0 = calculate_data_commitment(followers_0, delta_0, zero_encodings_0, nonce_0)
        commitment_1 = calculate_data_commitment(followers_1, delta_1, zero_encodings_1, nonce_1)
        commitment_2 = calculate_data_commitment(followers_2, delta_2, zero_encodings_2, nonce_2)

        # Outputs
        print_ln("output: avg_followers = %s", avg_followers.reveal())
        commitment_0.reveal_print_hex()
        commitment_1.reveal_print_hex()
        commitment_2.reveal_print_hex()


    avg_followers, commitments_mpsdz = compile_run(computation)
    verify_tlsn_proofs(proofs, commitments_mpsdz)
    print(f"Average followers: {avg_followers}")


if __name__ == "__main__":
    main()