# Module 2: Literature Review, Mathematical Formulations & Forensic Methods

## 1. Formal Mathematical Models of Taint Analysis

When funds enter an intermediate address along with other unassociated funds, forensic systems must apply an accounting rule to track how "taint" (stolen asset proportion) propagates forward.

Let address $v$ have an existing clean balance $B_{clean}$.
At timestamp $\tau_0$, it receives stolen funds of value $V_{stolen}$.
Its new balance becomes:
$$B_{total} = B_{clean} + V_{stolen}$$

Let an outgoing transaction $tx_{out} = (v, u, W)$ occur at timestamp $\tau_1 > \tau_0$.
How much of $W$ is tainted ($T_{out}$)?

### A. The Poison (Binary) Model
$$\text{Taint}(tx_{out}) = \begin{cases} 1.0 & \text{if } V_{stolen} > 0 \\ 0.0 & \text{otherwise} \end{cases}$$
- **Rationale:** Strict zero-tolerance; any touch of dirty funds contaminates the entire subsequent stream.
- **Drawback:** Extreme false-positive rate. In a high-volume wallet (or automated trading bot), a 0.001 ETH dust transaction would falsely mark millions of dollars as stolen.

### B. The Haircut (Pro-Rata / Proportional) Model
The outgoing transaction inherits taint in exact proportion to the fraction of tainted funds held by the sender at that instant:
$$\theta = \frac{V_{stolen}}{B_{total}}$$
$$\text{Tainted Value } (T_{out}) = W \cdot \theta$$
$$\text{Taint Score } = \theta$$
- **Rationale:** Preserves conservation of mass. If a wallet is 40% dirty, 40% of every outgoing dollar is counted as tainted.
- **Advantage:** Smooth mathematical decay; naturally damps down noise as funds disperse into deep pools.

### C. The FIFO (First-In, First-Out) Model
Transactions are ordered strictly by timestamp $\tau$.
- Funds entering first are consumed first by outgoing transactions.
- If $B_{clean}$ was present before $V_{stolen}$, outgoing transactions consume $B_{clean}$ until it is exhausted; only subsequent transactions are flagged as carrying $V_{stolen}$.
- **Rationale:** Matches standard forensic accounting and tax law principles. Most realistic for cold wallets or transit wallets that sit empty before receiving scam proceeds.

---

## 2. Algorithmic Solution to the Combinatorial Explosion: Heuristic-Guided $A^*$ / Best-First Search

Instead of a blind Breadth-First Search (which visits every branch equally and blows up at $O(b^d)$), we formulate forensic tracing as a **Priority-Queue Best-First Graph Traversal**:

### A. The Priority Function
For any candidate edge $e = (u, v)$ with transaction amount $w$ and timestamp $\tau$:
$$f(e) = \alpha \cdot \mathcal{T}(e) + \beta \cdot \mathcal{V}(w) + \gamma \cdot \Delta(\tau) + \delta \cdot \mathcal{A}(v)$$

Where:
1. **$\mathcal{T}(e)$ (Taint Proportion):** Proportional taint score calculated from the upstream source ($0 \le \mathcal{T} \le 1$).
2. **$\mathcal{V}(w)$ (Value Significance):** Ratio of transaction amount to the total stolen amount:
   $$\mathcal{V}(w) = \min\left(1.0, \frac{w}{V_{original\_stolen}}\right)$$
3. **$\Delta(\tau)$ (Temporal Proximity Decay):** Criminals usually move funds quickly after a theft. Edges occurring shortly after the incoming theft get higher priority:
   $$\Delta(\tau) = \exp\left(-\lambda (\tau - \tau_{incident})\right)$$
4. **$\mathcal{A}(v)$ (Attribution Prior):** If vertex $v$ matches a known Centralized Exchange (CEX) deposit address, swap router, or high-risk entity, $\mathcal{A}(v)$ gives a strong heuristic boost.

### B. Pruning Conditions (Cutoff Rules)
To guarantee finite, real-time execution even over thousands of nodes:
1. **Taint Cutoff ($\tau_{min}$):** If the propagated taint value drops below a threshold (e.g., $T(e) < 0.02$ or ₹500 equivalent), the branch is pruned.
2. **Temporal Window ($\Delta t_{max}$):** Outgoing transactions occurring before the theft or long after dormancy are ignored.
3. **Top-$K$ Branching:** Out of all candidate outgoing transactions from a single high-fanout node, only the top $K$ edges ranking highest by $f(e)$ are queued for deep expansion.

---

## 3. Academic & Industry Literature Review

| Tool / Paper | Methodology | Strengths | Limitations |
| :--- | :--- | :--- | :--- |
| **BitIodine** (Spagnuolo et al.) | Multi-input clustering + Graph parsing on Bitcoin | Automatic entity classification | Designed strictly for UTXO, does not handle Account-based EVM |
| **BlockSci** (Kalodner et al.) | High-performance in-memory graph engine | Microsecond graph traversal | Requires running a full archival node (terabytes of local storage) |
| **TRacer** (Bao et al.) | Account-based Ethereum tracing with Personalized PageRank (PPR) | Handles Ethereum contract calls and token transfers | High compute overhead; complex offline preprocessing |
| **Chainalysis / Elliptic** (Commercial Industry Standards) | Proprietary clustering heuristics + Massive off-chain entity database | Ground-truth exchange attribution and law enforcement integration | Closed-source, prohibitively expensive licenses for state cyber units |

---

## 4. Key Takeaways for Our Solution

1. We implement a hybrid **FIFO + Proportional Haircut Taint Engine** specifically tailored for EVM / Account-based transfers (ETH & ERC-20/TRC-20 USDT).
2. We utilize a **Priority-Queue Graph Search** that prevents exponential explosion by mathematically scoring each path.
3. We maintain an offline **Exchange & Entity Database** (Binance, CoinDCX, WazirX, KuCoin, OKX) so that as soon as a branch strikes an exchange deposit cluster, the path terminates and generates an actionable law enforcement freeze notice.
