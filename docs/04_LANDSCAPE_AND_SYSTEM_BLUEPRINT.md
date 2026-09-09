# Module 4: The Landscape, Current Realities & System Blueprint

## 1. Evolution of Cryptocurrency Forensics (Previous Findings)

```
2013: UTXO Clustering & Peel Chains
├── Ron & Shamir (2013): Full Bitcoin graph analysis, peel chain discovery.
├── Meiklejohn et al. (2013): Multi-input co-spend heuristic, change address clustering.
└── Möser et al. (2013): Early Bitcoin mixer analysis.
       │
       ▼
2020: Account-Based Paradigm & Temporal Graphs
├── Friedhelm Victor (2020): Address clustering heuristics for Ethereum deposit accounts.
├── Weber et al. (2019): Elliptic dataset, Graph Convolutional Networks (GCNs).
└── TRacer (Wu et al., 2022): Directed Temporal Personalized PageRank (PPR) on account graphs.
       │
       ▼
2024–2026: Subgraph Topologies & Mixer De-Anonymization
├── Elliptic2 (Bellei et al., 2024): 122K labeled subgraphs; money laundering is a subgraph shape.
├── RevTrack (Song et al., 2024): Source-to-sink candidate filtering reduces graph size by >85%.
├── Cristodaro et al. (2025): FIFO temporal matching de-anonymizes 15–22% of Tornado Cash ($2.3B+).
└── FlowShield & AMLGuard (2026): DeFi Semantic Units (DSU) & automated Suspicious Activity Reports (SAR).
```

---

## 2. Existing Tools & Their Current Limitations

| Tool Tier | Prominent Tools | Current Operating Limitations |
| :--- | :--- | :--- |
| **Tier 1: Enterprise Commercial** | Chainalysis Reactor, Elliptic Investigator, TRM Labs | Prohibitively expensive (\$50k–\$150k/yr); closed-source black-box AI scores that struggle in Indian courts under the Bharatiya Sakshya Adhiniyam (BSA 2023); lack automated Section 91 CrPC notices. |
| **Tier 2: Academic Prototypes** | BlockSci, BitIodine, TRacer, Tutela | Require terabytes of local archival blockchain node infrastructure; disjointed research scripts without live multi-chain API connectors or unified law enforcement reporting. |
| **Tier 3: Beginner Scripts** | Naive BFS scripts using free Etherscan APIs | Exponential combinatorial explosion ($b^d$); rate-limit bans (HTTP 429) within 3 hops; zero taint accounting (fails when funds mix). |

---

## 3. What We Are Building: 5-Layer Modular Architecture

1. **Layer 1 (Ingestion):** Multi-chain connectors (Etherscan, Tronscan, Blockchair) with intelligent rate-limit caching.
2. **Layer 2 (Taint Engine):** Account-based proportional haircut taint + FIFO chronological accounting.
3. **Layer 3 (Heuristic Search):** Priority-Queue Best-First search ($f(e)$ score) + Peel Chain Collapser + Smurfing Filter.
4. **Layer 4 (Attribution):** Verified CEX deposit registry (Binance, CoinDCX, WazirX, OKX) and smart contract classifiers.
5. **Layer 5 (LEA Action Dossier):** Visual interactive graph + automated Section 91 CrPC / Section 94 BNSS freeze notices for Indian cyber police.
