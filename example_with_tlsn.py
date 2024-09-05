from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class TLSNProof:
    # private to party
    followers: int
    # public
    proof_path: Path


@dataclass(frozen=True)
class TLSNCommitment:
    encoding: int
    delta: int
    # opening.recover().hash()
    commitment: int


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


def prepare_player_data(proofs: list[TLSNProof]):
    assert len(proofs) == NUM_PARTIES
    for i, proof in enumerate(proofs):
        party_data_file = PARTY_DATA_DIR / f"Input-P{i}-0"
        with open(party_data_file, "w") as f:
            f.write(f"{proof.followers}\n")
            # FIXME: how to get the delta from the proof?
            # FIXME: how should we write delta and zero_encodings to the mpspdz input file?
            # FIXME: what types can we use in MP-SPDZ to read the delta?


def generate_tlsn_proofs() -> list[TLSNProof]:
    # Run the tlsn proof generation command
    proofs = []
    for party_index in range(NUM_PARTIES):
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
        proofs.append(TLSNProof(followers=followers, proof_path=proof_file))
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
        encoding_0 = parsed_data['encoding_0']
        encoding_1 = parsed_data['encoding_1']
        encoding_2 = parsed_data['encoding_2']
        delta_0 = parsed_data['delta_0']
        delta_1 = parsed_data['delta_1']
        delta_2 = parsed_data['delta_2']
        commitment_0 = parsed_data['commitment_0']
        commitment_1 = parsed_data['commitment_1']
        commitment_2 = parsed_data['commitment_2']
    except KeyError as e:
        raise KeyError(f"Missing expected output variable: {str(e)}")

    return avg_followers, [
        TLSNCommitment(encoding=encoding_0, delta=delta_0, commitment=commitment_0),
        TLSNCommitment(encoding=encoding_1, delta=delta_1, commitment=commitment_1),
        TLSNCommitment(encoding=encoding_2, delta=delta_2, commitment=commitment_2),
    ]


def verify_tlsn_proofs(proofs: list[TLSNProof]):
    assert len(proofs) == NUM_PARTIES
    for proof in proofs:
        try:
            subprocess.run(
                f"cd {EXAMPLE_DIR} && {CMD_VERIFY_TLSN_PROOF} {proof.proof_path}",
                shell=True, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")
            print(f"stdout:\n{e.stdout}")
            print(f"stderr:\n{e.stderr}")
            exit(1)


def main():
    # proofs = generate_tlsn_proofs()
    proofs = [
        TLSNProof(followers=10, proof_path=FILE_DIR / f"tlsn-proof-p0.json"),
        TLSNProof(followers=14, proof_path=FILE_DIR / f"tlsn-proof-p1.json"),
        TLSNProof(followers=21, proof_path=FILE_DIR / f"tlsn-proof-p2.json"),
    ]
    prepare_player_data(proofs)
    avg_followers, commitments = compile_run()
    verify_tlsn_proofs(proofs)
    print(f"Average followers: {avg_followers}")
    print(f"Commitments: {commitments}")



if __name__ == "__main__":
    main()