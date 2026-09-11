# Cyber Fraud Detector: Crypto Wallet Fraud Tracing Engine
> **Smart India Hackathon (SIH) — Problem Statement 26183**  
> **Organizing Ministry:** Ministry of Home Affairs (MHA), Government of India / Indian Cyber Crime Coordination Centre (I4C)  
> **Mission:** *"When someone reports a scam wallet, follow the stolen money and find where it gets cashed out."*

[![Live Demo](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-blue?style=for-the-badge&logo=github)](https://atlas55kk.github.io/Cyber_fraud_detector/)
[![Research Paper](https://img.shields.io/badge/Research%20Paper-31%20Pages%20(PDF)-red?style=for-the-badge&logo=latex)](https://github.com/Atlas55kk/Cyber_fraud_detector/blob/main/research_paper/main.pdf)
[![Tests](https://img.shields.io/badge/Tests-53%2F53%20Passing-brightgreen.svg?style=for-the-badge)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

> 🚀 **1-Click Live Web Application (No Installation Needed):**  
> **👉 [https://atlas55kk.github.io/Cyber_fraud_detector/](https://atlas55kk.github.io/Cyber_fraud_detector/)**  
> Test live forensic tracing, progressive whiteboard visualization, and statutory freeze notices directly in your browser.

## 1. Overview & Root-Cause Solution

In real-world cyber fraud, scammers rarely keep stolen cryptocurrency in the initial receiving wallet. They rapidly split and bounce funds across dozens or hundreds of intermediate wallets using **peel chains**, **smurfing (structuring)**, and **cross-wallet transit layers** to make manual tracing exhausting.

### The Technical Challenge
- Naive Breadth-First Search (BFS) scripts collapse due to **$O(b^d)$ combinatorial explosion**: exploring 20 branches over 4 hops generates 160,000 queries, hitting public API rate limits (HTTP 429) within seconds.
- Account-based blockchains (like Ethereum and TRON USDT) lack explicit UTXO coin ancestry. When stolen tokens mix with existing balances, naive tools fail to track **proportional dilution**, leading to false accusations and invalid legal notices.

### Our Solution
This engine implements a **5-Layer Forensic Graph Architecture**:
1. **Lightweight Attributed Forensic Node Boxes:** Memory-optimized (`__slots__`) graph containers capable of tracking over 100,000 accounts in under 20 MB of RAM.
2. **Mathematical Proportional Haircut Taint Engine:** Enforces strict conservation of mass ($\theta = \frac{V_{\text{stolen}}}{B_{\text{total}}}$) and accounts for native gas fees burned at each step.
3. **Heuristic Best-First Search ($H\text{-BFSTP}$):** A priority-queue search scoring candidate edges via:
   $$f(e) = \alpha \cdot \mathcal{T}(e) + \beta \cdot \mathcal{V}(w) + \gamma \cdot \Delta(\tau) + \delta \cdot \mathcal{A}(v)$$
   Prioritizes high-taint, recent, and exchange-bound edges while dynamically pruning low-value dust noise.
4. **Topological Pattern Recognizers:** Automated detection and collapsing of **Peel Chains** and **Smurfing Fan-Out Clusters**.
5. **Law Enforcement Action Output:** Automatically generates statutory **Section 94 BNSS (Section 91 CrPC) Legal Freeze Requisitions** to serve to Centralized Exchanges (Binance, CoinDCX, WazirX) during the critical golden hours.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       LAYER 1: DATA INGESTION ENGINE                        │
│  - Multi-chain connectors (Etherscan, Polygonscan, Tronscan)                │
│  - Rate-Limit Shield with Local File Caching (Guarantees <4 req/sec)        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                LAYER 2: MATHEMATICAL TAINT & ACCOUNTING ENGINE              │
│  - Proportional Haircut Taint Accounting (Conservation of Mass)             │
│  - Physical Gas Fee Burn Subtraction & Dynamic Threshold Pruning (<2%)      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 LAYER 3: HEURISTIC GRAPH SEARCH & PRUNING                   │
│  - Priority Best-First Search (f(e) Priority Queue Traversal)               │
│  - Peel Chain Collapser & Smurfing Structuring Filter                       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               LAYER 4: ENTITY ATTRIBUTION & KNOWLEDGE BASE                  │
│  - Centralized Exchange (CEX) Hot/Deposit Registry (Binance, CoinDCX, etc.) │
│  - Smart Contract Router & Privacy Mixer Classifier (Tornado Cash)          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│           LAYER 5: FORENSIC DOSSIER & LEGAL REQUISITION GENERATOR           │
│  - Interactive Cytoscape Whiteboard Visualizer (`whiteboard.html`)          │
│  - Statutory Section 94 BNSS / Section 91 CrPC Account Freeze Notices        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Quickstart & Demonstration

### Prerequisites
- Python 3.10+ (Standard library + NumPy)

### Installation
```bash
git clone https://github.com/Atlas55kk/Cyber_fraud_detector.git
cd Cyber_fraud_detector
pip install numpy fastapi uvicorn
```

### Launch the Live Interactive Web Portal
```bash
python server.py
```
Open **`http://localhost:8000`** in any web browser to access the live forensic command center with interactive graph visualization, live typewriter logs, and one-click Section 94 BNSS notice export.

### Run the Multi-Chain Forensic CLI Demo
```bash
# Trace both EVM and TRON incidents simultaneously
python main.py --chain both

# Trace only TRON (TRC-20 USDT) incidents (Primary Indian Cybercrime Vector)
python main.py --chain tron

# Trace only Ethereum / EVM incidents
python main.py --chain evm
```

### Run the Complete Test Suite
```bash
python -m unittest discover tests
```
*All 26 unit and integration tests execute in <0.05 seconds.*

---

## 4. Repository Structure

```
Cyber_fraud_detector/
├── main.py                           # CLI entry point for full forensic demonstration
├── whiteboard.html                   # Interactive Cytoscape.js whiteboard canvas
├── problem_statement.txt             # Raw SIH Problem Statement description
├── docs/                             # Core theoretical & mathematical documentation
│   ├── 01_FIRST_PRINCIPLES_AND_ROOT_CAUSE.md
│   ├── 02_LITERATURE_REVIEW_AND_METHODS.md
│   ├── 03_REAL_WORLD_CONTEXT_INDIA_MHA_I4C.md
│   ├── 04_LANDSCAPE_AND_SYSTEM_BLUEPRINT.md
│   ├── 05_CORE_DATA_STRUCTURES_AND_TAINT_ENGINE.md
│   └── 06_HEURISTIC_SEARCH_AND_TOPOLOGICAL_PRUNING.md
├── research/                         # Academic papers and authenticity audit
│   ├── papers_read.txt               # Log of 33 peer-reviewed research papers
│   ├── VERIFIED_BIBLIOGRAPHY.md      # Clickable DOIs and direct PDF URLs
│   ├── AUTHENTICITY_AUDIT.json       # Programmatic HTTP 200 registry audit
│   └── literature_notes/             # Paper-by-paper deep-dives
├── data/
│   └── known_entities/registry.json  # Curated exchange deposit and contract registry
├── reports/                          # Generated legal notices (Sec 94 BNSS)
├── src/                              # Core Python source packages
│   ├── core/                         # NodeBox, WireEdge, TaintEngine, Canvas
│   ├── attribution/                  # EntityResolver
│   ├── algorithms/                   # PrioritySearch, PeelDetector, SmurfFilter
│   ├── fetchers/                     # EtherscanFetcher, MockGenerator
│   └── reporting/                    # LegalDossierGenerator, Visualizer
└── tests/                            # Comprehensive unit & integration tests
```

---

## 5. Verified Academic Bibliography

All citations have been programmatically validated against official registries (Cornell arXiv, CrossRef, ACM, and FATF):
1. **TRacer:** *Scalable Graph-based Transaction Tracing for Account-based Blockchains* (Wu et al., 2022) — [arXiv:2201.05757](https://arxiv.org/abs/2201.05757)
2. **Peel Chains:** *How to Peel a Million: Validating and Expanding Bitcoin Clusters* (Kappos et al., 2022) — [arXiv:2205.13882](https://arxiv.org/abs/2205.13882)
3. **Subgraph Topologies:** *The Shape of Money Laundering (Elliptic2)* (Bellei et al., MIT-IBM, 2024) — [arXiv:2404.19109](https://arxiv.org/abs/2404.19109)
4. **Subgraph Filtering:** *Identifying Money Laundering Subgraphs (RevTrack)* (Song et al., 2024) — [arXiv:2410.08394](https://arxiv.org/abs/2410.08394)
5. **Mixer De-Anonymization:** *Clustering Deposit & Withdrawal Activity in Tornado Cash* (Cristodaro et al., 2025) — [arXiv:2510.09433](https://arxiv.org/abs/2510.09433)
6. **Regulatory Standards:** *Virtual Assets Red Flag Indicators of Money Laundering* (FATF Global Standards, Sept 2020) — [FATF Report](https://www.fatf-gafi.org/media/fatf/documents/recommendations/Virtual-Assets-Red-Flag-Indicators.pdf)

---

## 6. License
MIT License. Open-source contribution for Smart India Hackathon (SIH 2026).
