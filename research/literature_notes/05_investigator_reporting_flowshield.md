# Literature Deep-Dive: Semantic Parsing & Investigator Reporting (FlowShield & AMLGuard)
**Papers:**  
- *FlowShield: cryptocurrency anti-money laundering with transaction semantics parsing and fund flow tracking* (Fu et al., 2026, arXiv:2608.17355)  
- *Tracing the Shadows: Automatic Tracking and Analysis of Crypto Money Laundering via Transaction Semantic Analysis* (Wu et al., 2026, arXiv:2607.18869)  
- *Of Degens and Defrauders: Using Open-Source Investigative Tools to Investigate DeFi Frauds* (Trozze et al., 2023, arXiv:2303.00810)

---

## 1. The Gap Between Graph Algorithms and Court Admissibility

A high F1-score graph algorithm is useless to a police sub-inspector or an exchange compliance officer if it cannot explain:
1. **The Origin:** Where did the funds come from (victim complaint details).
2. **The Chain of Custody:** The unbroken deterministic sequence of transaction hashes ($tx_1 \to tx_2 \dots$).
3. **The Semantic Meaning:** Explaining raw hexadecimal bytecode in plain language (e.g., *"Wallet S swapped 50,000 USDT for 15.2 ETH via Uniswap V3 Pool, then bridged 10 ETH to Arbitrum via Across Protocol"*).
4. **The Target Action:** Exactly which exchange account needs to be frozen immediately.

---

## 2. Key Contributions of FlowShield & AMLGuard

### A. DeFi Semantic Units (DSUs)
Instead of treating every transaction as a generic transfer edge, AMLGuard maps contract calls into high-level semantic units:
- `SWAP(TokenIn, AmountIn, TokenOut, AmountOut, DEX)`
- `BRIDGE_DEPOSIT(OriginChain, DestinationChain, Recipient)`
- `CEX_DEPOSIT(ExchangeName, DepositAddress)`
- `PEEL_SPLIT(PeelAmount, ForwardAmount, NextTransitHop)`

### B. Automated Suspicious Activity Report (SAR) Generation
FlowShield uses structured templates fused with LLM summarization to generate standardized investigative dossiers:
- Executive Summary (Total stolen, current recovered, current frozen, at-risk).
- High-risk node breakdown (Entity classifications).
- Recommended Legal Actions (Notices under relevant criminal codes).

---

## 3. Integration into Our Project
We will incorporate:
1. A semantic decoder for ERC-20/TRC-20 `transfer`, Uniswap `swap`, and CEX deposit patterns.
2. An automated **Police Requisition Dossier Generator** exporting markdown and JSON reports formatted specifically for Indian LEAs (compliant with Section 91 CrPC / Section 94 BNSS).
