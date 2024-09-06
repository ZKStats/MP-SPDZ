# Authenticating MPC Inputs with TLSNotary

## Introduction
A system that allows parties to prove their inputs in Multi-Party Computation (MPC) come from specific websites without revealing the inputs themselves. Implemented in [MP-SPDZ](https://github.com/data61/MP-SPDZ), it can be used in various ZKP/MPC/FHE frameworks. This approach ensures that while MPC guarantees input privacy, it also verifies input authenticity, preventing arbitrary or fabricated inputs.

### How It Works
1. Parties generate TLSNotary proofs for their input webpages.
2. MPC calculates and reveals TLSNotary data commitments from private inputs.
3. Parties verify each other's TLSNotary proofs and check if MPC-calculated commitments match those in the proofs.

### Detailed Process
- **Problem 1: No way to prove properties of redacted data**
  - The ZKP feature of TLSNotary is still in development, so redacted data is not committed, making it impossible to prove properties.
  - **Solution:** Add a "commit-and-reveal-commitment" feature to TLSNotary, allowing only commitments (hashes) to be revealed, keeping private inputs confidential.

- **Problem 2: Hash function blake3 is not supported in MP-SPDZ**
  - **Solution:** Replace blake3 with sha3 for compatibility with MP-SPDZ.

![Detailed Process](./structure.png)

With the installation and demo run instructions provided below, you can quickly set up the project and verify its functionality.

## Getting Started

### Install and Setup
```bash
git clone https://github.com/ZKStats/MP-SPDZ.git
cd MP-SPDZ && git checkout tlsn-integration
make setup && make -j8 semi-party.x
cd .. && git clone https://github.com/ZKStats/tlsn.git
cd tlsn && git checkout mpspdz-compat
```

### Run Demo
Run the demo to calculate followers from three webpages:
- [party_0](https://mhchia.github.io/followers-page/party_0.html)
- [party_1](https://mhchia.github.io/followers-page/party_1.html)
- [party_2](https://mhchia.github.io/followers-page/party_2.html)

![Demo Overview](./demo-pages.png)
Execute the following command to start the demo:

```bash
cd ../MP-SPDZ
python example_with_tlsn.py
```

Expected output:
```bash
TLSN proofs verified successfully and matched with MP-SPDZ output
Average followers: 6
```

## Future Work
- Make it work with multiple digits inputs.
- Replace example pages with real-world pages, like [the health care page in Taiwan](https://github.com/ZKStats/tlsn/pull/4).
- Improve modularity and portability
- Use blake3 in MP-SPDZ so we can use the upstream TLSNotary.
- Utilize TLSNotary's ZKP feature when available

## Contributors
(alphabetically) Alex Kuzmin, Jern Kunpittaya, Kevin Chia, Kimi Wu, Ya-Wen (Vivian) Jeng.
