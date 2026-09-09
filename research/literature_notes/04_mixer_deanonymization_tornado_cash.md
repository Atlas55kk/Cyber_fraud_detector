# Literature Deep-Dive: Privacy Pool & Mixer De-Anonymization (Tornado Cash)
**Papers:**  
- *Clustering Deposit and Withdrawal Activity in Tornado Cash: A Cross-Chain Analysis* (Cristodaro et al., 2025, arXiv:2510.09433)  
- *Tutela: An Open-Source Tool for Assessing User-Privacy on Ethereum and Tornado Cash* (Wu et al., 2022, arXiv:2201.06811)  
- *Blockchain is Watching You: Profiling and Deanonymizing Ethereum Users* (Béres et al., 2020, arXiv:2005.14051)

---

## 1. The Myth of Perfect Anonymity in Mixers

Mixers like Tornado Cash utilize Zero-Knowledge SNARKs (zk-SNARKs) to mathematically break the link between the deposit address and the withdrawal address. When a user deposits 10 ETH, a cryptographic commitment is stored in a Merkle tree. When withdrawing, a zk-proof proves membership in the tree without revealing the specific leaf.

**However, human behavior and operational constraints leak metadata that re-links deposits to withdrawals.**

---

## 2. The 3 Primary De-Anonymization Heuristics

### Heuristic 1: Address-Reuse & Cross-Account Contamination
- **Sloppy Operational Security (OpSec):** Scammers frequently withdraw clean funds into a fresh wallet, but then transfer funds back to an address that originally funded the deposit, or interact with the same smart contracts.
- **Gas Sponsoring:** A freshly generated withdrawal address has 0 ETH for gas fees. Scammers often send a tiny amount of ETH from their dirty wallet to the fresh wallet to pay for the first transaction—completely nullifying the mixer!

### Heuristic 2: FIFO & Queue-Length Temporal Matching (Cristodaro et al., 2025)
- In low-liquidity pools (e.g., Tornado Cash 100 ETH or 100,000 DAI pools), deposits and withdrawals are infrequent.
- **The FIFO Rule:** If deposit $D_i$ occurs, and withdrawal $W_j$ occurs shortly after with few or zero intervening deposits in that specific denomination pool, the probability $P(D_i \leftrightarrow W_j)$ approaches certainty.
- Cristodaro et al. proved that **FIFO temporal-matching links 15–22% of all Tornado Cash withdrawals** with statistical confidence ($p < 0.001$), de-anonymizing over \$2.3 Billion.

### Heuristic 3: Transactional Fingerprinting & Relayer Linkage
- **Relayer Address Re-use:** When using third-party relayers to pay gas fees on withdrawal, relayers often bundle transactions or operate on deterministic nonces.
- **Gas Price & Client Fingerprinting:** EIP-1559 priority fee choices, custom gas limits (e.g., Metamask vs Python Web3 defaults), and time-of-day timezone clustering act as quasi-identifiers.

---

## 3. Forensic Integration in Our Engine
When a path reaches a mixer contract:
1. Identify the exact denomination pool and block height of deposit.
2. Monitor pool withdrawals within a 72-hour window.
3. Apply FIFO queue scoring and gas-funder linking to flag high-confidence candidate recipient addresses rather than giving up.
