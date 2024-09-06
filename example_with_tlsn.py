from dataclasses import dataclass
from pathlib import Path
import subprocess
import json

from Compiler.compilerLib import Compiler
from Compiler.types import sint, sfix
from Compiler.GC.types import sbitvec, sbits
from Compiler.library import print_ln
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


# Only supports 1 byte for now
NUM_REDACTED_BYTES = 1
WORD_SIZE = 16
WORDS_PER_LABEL = 8

COMMITMENT_HASH_SIZE = 32
ASCII_BASE = 48


def prepare_player_data(proofs: list[TLSNProof]):
    assert len(proofs) == NUM_PARTIES
    for i, proof in enumerate(proofs):
        party_data_file = PARTY_DATA_DIR / f"Input-P{i}-0"
        with open(party_data_file, "w") as f_data:
            followers = proof.followers
            bytes_followers = str(followers).encode('ascii')
            assert len(bytes_followers) == NUM_REDACTED_BYTES, f"Expected {NUM_REDACTED_BYTES} bytes, got {len(bytes_followers)}"
            f_data.write(f"{followers}\n")


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
            all_labels = []
            for e in encodings:
                delta = e["U8"]["state"]["delta"]
                labels = e["U8"]["labels"]
                assert len(delta) == WORD_SIZE, f"Expected {WORD_SIZE} bytes in delta, got {len(delta)}"
                delta_hex = bytes(delta).hex()
                assert len(labels) == WORDS_PER_LABEL, f"Expected {WORDS_PER_LABEL} labels, got {len(labels)}"
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
        assert commitment_tlsn == commitment_mpspdz, f"Commitment encoding does not match for party {party_index}"


def main():
    print("Generating TLSN proofs for parties...")
    proofs = generate_tlsn_proofs()
    print(f"Proofs: {proofs}")
    # proofs = [
    #     TLSNProof(followers=3, proof_path=FILE_DIR / 'tlsn-proof-p0.json', delta='2501fa5c2b50281d97cc4e63bb1beaef', zero_encodings=['b51d9f6c1d7133a3c2d307b431c7f3ea', '2842eaaf492880247548f2cb189c2f5b', 'f1844ae7b20ad935605c87878b0ffb96', 'd19b84012adf53dedc896ebb36f7decd', 'e9629218d15b7d0887ffa78c4c70d237', 'd7ce38f06c1b134f30ee3dcd5c947d54', '7e666304dbc6c6a48d270c6d4c71f789', '62a1e68e06fd1d02adeb3646cfb47601'], hash='dc249d3704656445a729cc36e39a2f62900fd24f79d20d0dc6f30a5f22ef8f06', nonce='2a0ffcbec6f9338b582694ed46504445e59f3159ad6b7cb035325450ccb31213'),
    #     TLSNProof(followers=7, proof_path=FILE_DIR / 'tlsn-proof-p1.json', delta='373649df4ba763efb80393526cd8914a', zero_encodings=['4072e2f7e1c271086b4e73ddfd01f55a', '9de71f0bc983a30a4f4d48e21e8202a5', '5abfda4890938dc295bde881e309e8ca', 'c03b03d33cf9f21d110c85c4e76b957c', 'b38ce9704025ed2dede2a17d878a207e', 'ff676722a58d98742644268c05abe19d', '02ee533f359a03c45302b2e1cf529b9f', '27b057b471aa76641263e71c82526310'], hash='9b1d8da9d318e47f0350ff28a517e082083b3cd230dd846c87c85998612c50bf', nonce='d25f6e5bb66954b8765ee15ce9b76eee77567f1c5d9254aeeacf4ba013a58ff6'),
    #     TLSNProof(followers=8, proof_path=FILE_DIR / 'tlsn-proof-p2.json', delta='a933d0765b313d91d518bda095977f78', zero_encodings=['4b88931361b0b69fa573e18995f84042', '659d0fc74b3a8fe2baa71f5917c20c16', 'de0c378c7ae34171fff72a8bf5c93ad2', '554f1ed3f33d8c522988407d6d6f84d1', '71413cfa8f91380a0edc510a93e07fca', '26eb86d3c2fa2187be7087f17233ebbb', '3db5b599d6b8590693ffda5f4a2be9bb', '06462ccd3c5e11b7839053b4b9860409'], hash='5f8f1b8aaee66105cd5f29c65f85448e5e6e8f4a76a1c22dc619cffd09fd3666', nonce='451fa29db39b2ede357f10011b1d5957fa2ceca56ff6ac83b75c68f75340da99')
    # ]
    prepare_player_data(proofs)

    # MP-SPDZ circuit
    def computation():
        sfix.round_nearest = True
        def calculate_data_commitment(followers: sint, delta: sbitvec, encoding: list[sbitvec], nonce: sbitvec):
            # `followers` is "Data" and `encoding` is the "Full Encoding"
            # Active coding is calculated from `followers` and `encoding`.
            # Ref:
            #   - docs: https://docs.tlsnotary.org/mpc/commitments.html#commitments
            #   - code: https://github.com/tlsnotary/tlsn/blob/e14d0cf563e866cde18d8cf7a79cfbe66d220acd/crates/core/src/commitment/blake3.rs#L76-L80
            followers_byte = followers + ASCII_BASE
            followers_bits = sbitvec(followers_byte, NUM_REDACTED_BYTES*8)
            ENCODE_BIT_LEN = 128 # since each encoding[i] is 128 bits.
            big_num = sint(2**ENCODE_BIT_LEN-1)
            followers_bits_list = [sint(ele) for ele in followers_bits.v]
            active_encoding:list[sbitvec] = []
            for i in range(len(encoding)):
                # if followers_bits_arr[i] = 0--> big_num+1 overflows 128 bits, seeing only all 0
                # On the other hand, big_num still have 1 for all 128 bits
                nullifier = sbitvec(big_num+sint(1)-followers_bits_list[i], ENCODE_BIT_LEN)
                active_encoding.append(encoding[i].bit_xor(delta.bit_and(nullifier)))

            concat = nonce.bit_decompose()+ sbitvec(sint(1), NUM_REDACTED_BYTES*8).bit_decompose()+ sbitvec(sint(1), NUM_REDACTED_BYTES*8).bit_decompose()

            for i in range(len(active_encoding)):
                concat = concat + active_encoding[i].bit_decompose()

            return sha3_256(sbitvec.compose(concat))

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

    print("Running MP-SPDZ circuit...")
    avg_followers, commitments_mpsdz = compile_run(computation)
    print("Verifying TLSN proofs...")
    verify_tlsn_proofs(proofs, commitments_mpsdz)
    print("\n\n\nTLSN proofs verified successfully and matched with MP-SPDZ output")
    print(f"Average followers: {avg_followers}")


if __name__ == "__main__":
    main()