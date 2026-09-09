# Literature Deep-Dive: TRacer (Wu et al., 2022)
**Paper:** *TRacer: Scalable Graph-based Transaction Tracing for Account-based Blockchain Trading Systems*  
**Authors:** Zhiying Wu, Jieli Liu, Jiajing Wu, Zibin Zheng (Sun Yat-sen University)  
**ArXiv ID:** [arXiv:2201.05757](http://arxiv.org/abs/2201.05757v3)

---

## 1. Problem Formulated
Account-based blockchains (e.g., Ethereum, TRON) lack explicit input-output coin lineage (unlike Bitcoin's UTXO model). Balances are scalar and fungible. When stolen funds enter an account holding other funds, traditional heuristics fail because of:
1. **Fungibility Dilution:** Money mixes into a single pool.
2. **Combinatorial Graph Explosion:** As the search depth expands, high-degree nodes cause the graph to blow up into millions of edges.
3. **DeFi / Smart Contract Opacity:** Direct transfers, internal contract transactions, and token swaps are mixed.

---

## 2. Core Methodology: Multi-Relational Directed Temporal Personalized PageRank (PPR)
Instead of blind Breadth-First Search (BFS), TRacer models transaction tracing as a **relevance inference problem on a directed temporal multigraph**:

$$G = (V, E, \mathcal{W}, \mathcal{T})$$
- $V$: Accounts (EOAs and Smart Contracts).
- $E$: Directed transactions.
- $\mathcal{W}$: Transaction value/weight matrix.
- $\mathcal{T}$: Temporal timestamps enforcing chronological forward flow ($\tau_{out} \ge \tau_{in}$).

### Mathematical Relevance Propagation:
Starting with source scam account $s$, the relevance probability vector $\mathbf{r}$ satisfies:
$$\mathbf{r} = (1 - c) \mathbf{P}^T \mathbf{r} + c \mathbf{e}_s$$

Where:
- $c \in (0, 1)$ is the restart probability (teleportation parameter, usually $c \approx 0.15$).
- $\mathbf{e}_s$ is the preference vector (concentrated at the scam wallet $s$).
- $\mathbf{P}$ is the transition probability matrix, weighted by transaction amount and decayed by time delta:
  $$P_{uv} = \frac{w(u, v) \cdot \exp(-\lambda (\tau_{uv} - \tau_{incident}))}{\sum_{k \in \text{Out}(u)} w(u, k) \cdot \exp(-\lambda (\tau_{uk} - \tau_{incident}))}$$

---

## 3. Direct Application to Our SIH Solution
1. **Relevance-Guided Queue:** Instead of exploring all outgoing edges equally, edges are priority-ranked by their relevance score from PPR.
2. **Adaptive Branch Pruning:** Nodes whose relevance drops below a dynamic epsilon ($\epsilon = 10^{-4}$) are immediately pruned, preventing tree explosion.
3. **Handles Internal Transactions:** Accounts interacting through smart contract transfers (ERC-20/TRC-20 Transfer events) are mapped as first-class edges.
