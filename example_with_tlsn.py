from dataclasses import dataclass
from pathlib import Path
import subprocess
import json


@dataclass(frozen=True)
class DataCommitment:
    hash: int
    nonce: int


@dataclass(frozen=True)
class TLSNProof:
    # private to party
    followers: int
    # public
    proof_path: Path
    data_commitments: dict[int, DataCommitment]


@dataclass(frozen=True)
class TLSNCommitmentFromMPSPDZ:
    encoding: list[list[list[int]]]
    delta: list[int]
    # opening.recover().hash()
    commitments: list[list[int]]


FILE_DIR = Path(__file__).parent
TLSN_PROJECT_ROOT = FILE_DIR.parent / 'tlsn'
# ls tlsn/examples
EXAMPLE_DIR = TLSN_PROJECT_ROOT / 'tlsn' / 'examples' / 'simple'
CMD_GEN_TLSN_PROOF = "cargo run --release --example simple_prover"
CMD_VERIFY_TLSN_PROOF = "cargo run --release --example simple_verifier"


MPSPDZ_PROJECT_ROOT = FILE_DIR
MPSPDZ_CIRCUIT_DIR = MPSPDZ_PROJECT_ROOT / 'Programs' / 'Source'

COMPILE_RUN = MPSPDZ_PROJECT_ROOT / "Scripts" / "compile-run.py"

MPC_PROTOCOL = 'semi'
CIRCUIT_NAME = 'auth_with_tlsn'

NUM_PARTIES = 3
PARTY_DATA_DIR = MPSPDZ_PROJECT_ROOT / "Player-Data"
PARTY_DATA_DIR.mkdir(parents=True, exist_ok=True)


EXPECTED_REDACTED_BYTES = 12


def prepare_player_data(proofs: list[TLSNProof]):
    assert len(proofs) == NUM_PARTIES
    for i, proof in enumerate(proofs):
        party_data_file = PARTY_DATA_DIR / f"Input-P{i}-0"
        with open(party_data_file, "w") as f_data:
            f_data.write(f"{proof.followers}\n")
            data_commitment = tuple(proof.data_commitments.values())[0]
            f_data.write(f"{" ".join(map(str, data_commitment.nonce))}\n")

            with open(proof.proof_path, "r") as f_proof:
                proof_data = json.load(f_proof)
                encodings = proof_data["encodings"]
                print(f"len(encodings): {len(encodings)}")
                assert len(encodings) == EXPECTED_REDACTED_BYTES, f"Expected {EXPECTED_REDACTED_BYTES} bytes in encodings, got {len(encodings)}"
                for e in encodings:
                    delta = e["U8"]["state"]["delta"]
                    labels = e["U8"]["labels"]
                    assert len(delta) == 16, f"Expected 16 bytes in delta, got {len(delta)}"
                    f_data.write(f"{" ".join(map(str, delta))}\n")
                    assert len(labels) == 8, f"Expected 8 labels, got {len(labels)}"
                    all_labels = []
                    for l in labels:
                        assert len(l) == 16, f"Expected 16 bytes in label, got {len(l)}"
                        all_labels.extend(l)
                    f_data.write(f"{" ".join(map(str, all_labels))}\n")


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
            data_commitments = {}
            for commitment_index, openings in private_openings.items():
                commitment_info, commitment = openings
                data_commitment_hash = commitment["hash"]
                data_commitment_nonce = commitment["nonce"]
                data_commitments[commitment_index] = DataCommitment(hash=data_commitment_hash, nonce=data_commitment_nonce)
        proofs.append(
            TLSNProof(
                followers=followers,
                proof_path=proof_file,
                data_commitments=data_commitments
            )
        )
    return proofs



def compile_run():
    # check if the circuit file exists
    circuit_file = MPSPDZ_CIRCUIT_DIR / f"{CIRCUIT_NAME}.mpc"
    if not circuit_file.exists():
        raise FileNotFoundError(f"Circuit file {circuit_file} not found")
    try:
        command = f"PLAYERS={NUM_PARTIES} {COMPILE_RUN} {MPC_PROTOCOL} {CIRCUIT_NAME}"
        print(f"Running command: {command}")
        res = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        print(f"stdout:\n{e.stdout}")
        print(f"stderr:\n{e.stderr}")
        exit(1)
    print(f"stdout:\n{res.stdout}")
    # Parse the output
    output_lines = res.stdout.split('\n')
    parsed_data = {}
    for line in output_lines:
        if line.startswith('output: '):
            key, value = line[8:].split('=')
            key = key.strip()
            value = value.strip()
            try:
                parsed_data[key] = int(value)
            except ValueError:
                try:
                    parsed_data[key] = float(value)
                except ValueError:
                    parsed_data[key] = value

    # Extract the variables
    try:
        avg_followers = parsed_data['avg_followers']
        encoding_0 = eval(parsed_data['encoding_0'])
        encoding_1 = eval(parsed_data['encoding_1'])
        encoding_2 = eval(parsed_data['encoding_2'])
        delta_0 = eval(parsed_data['delta_0'])
        delta_1 = eval(parsed_data['delta_1'])
        delta_2 = eval(parsed_data['delta_2'])
        commitments_0 = eval(parsed_data['commitments_0'])
        commitments_1 = eval(parsed_data['commitments_1'])
        commitments_2 = eval(parsed_data['commitments_2'])
    except KeyError as e:
        raise KeyError(f"Missing expected output variable: {str(e)}")

    return avg_followers, [
        TLSNCommitmentFromMPSPDZ(encoding=encoding_0, delta=delta_0, commitments=[commitments_0]),
        TLSNCommitmentFromMPSPDZ(encoding=encoding_1, delta=delta_1, commitments=[commitments_1]),
        TLSNCommitmentFromMPSPDZ(encoding=encoding_2, delta=delta_2, commitments=[commitments_2]),
    ]


def verify_tlsn_proofs(proofs: list[TLSNProof], commitments_mpspdz: list[TLSNCommitmentFromMPSPDZ]):
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
        commitment_tlsn = tuple(proof.data_commitments.values())[0]
        commitment_mpspdz = commitments_mpspdz[party_index].commitments[0]
        # FIXME: Check calculated commitments from MP-SPDZ output match the ones in TLSN proofs
        # assert commitment_tlsn == commitment_mpspdz, f"Commitment encoding does not match for party {party_index}"


def main():
    proofs = generate_tlsn_proofs()
    # proofs = [
    #     TLSNProof(followers=10, proof_path=FILE_DIR / f"tlsn-proof-p0.json", data_commitments={'4': DataCommitment(hash=[200, 6, 244, 93, 132, 195, 169, 153, 178, 18, 110, 104, 103, 191, 218, 173, 108, 66, 99, 63, 193, 39, 121, 143, 130, 189, 200, 74, 145, 126, 2, 188], nonce=[127, 19, 191, 64, 204, 225, 226, 243, 83, 125, 188, 178, 244, 161, 209, 235, 243, 118, 98, 159, 233, 90, 185, 241, 194, 167, 46, 41, 118, 83, 86, 49])}),
    #     TLSNProof(followers=14, proof_path=FILE_DIR / f"tlsn-proof-p1.json", data_commitments={'4': DataCommitment(hash=[157, 70, 101, 122, 135, 135, 70, 115, 224, 116, 231, 157, 130, 68, 61, 212, 45, 54, 239, 12, 54, 104, 170, 116, 249, 125, 213, 109, 79, 143, 240, 235], nonce=[54, 185, 2, 141, 111, 239, 92, 163, 161, 188, 17, 59, 0, 137, 99, 171, 134, 133, 111, 213, 107, 180, 249, 87, 21, 237, 34, 175, 47, 243, 0, 169])}),
    #     TLSNProof(followers=21, proof_path=FILE_DIR / f"tlsn-proof-p2.json", data_commitments={'4': DataCommitment(hash=[157, 70, 101, 122, 135, 135, 70, 115, 224, 116, 231, 157, 130, 68, 61, 212, 45, 54, 239, 12, 54, 104, 170, 116, 249, 125, 213, 109, 79, 143, 240, 235], nonce=[54, 185, 2, 141, 111, 239, 92, 163, 161, 188, 17, 59, 0, 137, 99, 171, 134, 133, 111, 213, 107, 180, 249, 87, 21, 237, 34, 175, 47, 243, 0, 169])})
    # ]
    print("Parsing information from TLSN output and ")
    prepare_player_data(proofs)
    avg_followers, commitments_mpsdz = compile_run()
    verify_tlsn_proofs(proofs, commitments_mpsdz)
    print(f"Average followers: {avg_followers}")


if __name__ == "__main__":
    main()