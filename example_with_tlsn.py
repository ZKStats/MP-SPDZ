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
        # FIXME: Check calculated commitments from MP-SPDZ output match the ones in TLSN proofs
        # assert commitment_tlsn == commitment_mpspdz, f"Commitment encoding does not match for party {party_index}"


def main():
    # proofs = generate_tlsn_proofs()
    # print(f"Proofs: {proofs}")
    proofs = [
        TLSNProof(followers=10, proof_path=FILE_DIR / 'tlsn-proof-p0.json', delta='d1ec7d44024e435443a80ef42a6d59d0', zero_encodings=['eb0ff64e6d184cc300ccdede9980c52a', 'c3e21f5970827e42bf7b1931af085653', '036fb7183f6d204a91cc8d97e9a792c9', '09556a664cb4368d373b20b090e5dbd0', '3276862953633172a258263a1f3a52f5', 'b34929ece0fe3652d354c70ddae7c11e', 'c4a3e44b801555136aa90489f4ca4442', '3270ab170f3366f73d78429216d97875', 'ab1cbc3d45bab23ed57d4f1113b61351', 'ad7bc80a3a9719e5356d0b8e55a2b7da', '9bc162080e85071281bb6971ede5497e', '40c27ba571b12f2ae791f5217ed485b1', '393022347ae48bedd7244a31f6ac02e3', '104317fbf0eca460f7a77c3581968cb7', 'd7b72674b0282c1747ccf7bfcefd7c8a', '863954ffefe6ee363d5310dcd315278a'], hash='798d05beb4d1e95eadf7c0d7fe47ba11fc674660d626ab2f5f35b3e323e03b47', nonce='42584f2289e56d7d93f6cdd3c0c316d1167b8f9bbf3c5de11ed906a14a331d43'),
        TLSNProof(followers=14, proof_path=FILE_DIR / 'tlsn-proof-p1.json', delta='a7c391edf3b2b1a0828fc421628d924b', zero_encodings=['f540d6b1be084f1d18d6ddbbd0aa07b8', '0bd7fc981e6bb0e15a7fbc67451ee90f', '63b14f774eb29b25f8b64408d6381b96', 'bd3c0cc08a8bbae0b43fd281541d9025', '40903ab18e7ecbe93e37351241090a7a', '8968b757b4d83b6b0bb08c05331f6047', '8e75d69d2f624eaf4ca5de3994ed3196', '8cabb249ba300120533d8dbd80c9f5ef', '498835c3fe12ccc525bca5b5498532af', '8171425dd53a28215188d7d91bde0139', '0349a6ab30ac0ffefdfd1a08e3ce7747', 'd89204f80f615abb794a790c70ec7f3a', '782ac40e3e08f0a05971a07ebb221474', '343f6bd76ad31cff3f4a51ee2c67eb0f', '5d289b15cf6e10b8de8746a2230c2271', '6b15c1291ad2afc1135d27351170770d'], hash='52cbf3ae8280eee9bf06cc58d2514055418b36943333a8d9851d66049872c1ef', nonce='82cad1a53873655667818ced06cf09012c90ccdc978597b0555fb7bacebcbdb5'),
        TLSNProof(followers=21, proof_path=FILE_DIR / 'tlsn-proof-p2.json', delta='bd26e7427cc43c77258cf3bf23b67da1', zero_encodings=['dc9fe9e2780636a1ab70bf03c0188408', 'f878d6081dd9eea10437477a9657b6c8', 'f83da2fd15d956a983aa59219f06d6b3', '23ceed47af186dc6f3dfcd03c93e0c59', '83932885a0193ebba68bb214c4e6ce72', '5e11011b5ec62f2e3b08a7d820c3e8e0', 'bd786e4b69a444867022da6520814681', '0ec83595f88c5685da4aa512edbd5d97', '585b0a699a0be042f6de662e22ce2013', '917d7d7d07a0ffe724fc807069424c21', 'bb688ebe22dd4cc8e3ba9b85a6ef5d06', '25caa422aa10defd9d0141ba52c9e6f6', '96dd9c33b8fd8a90fc0585628fa23225', '68ad054d4bd78d2059f54f6604d7cb43', '60bf0a2c4e449de2c75cc4019b3333e7', 'e37ec97d05a5f3ce78bd07ed13fcb73c'], hash='b653e141df4f4d2ed3eb1f361bc5b15fc4693ea2079b50f535624e04d0445160', nonce='cbe3f5f84370968a9f397a9c2263d3b380c1fd88aaae65a66d649fbd79b9ee6d'),
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