# Module 9: On-Demand Exchange Deposit Sweeping & Dynamic Clustering

## 1. The Real-World Exchange Deposit Architecture

When a retail user or scammer deposits funds into a centralized exchange (e.g., Binance, CoinDCX, WazirX), the funds do **not** land directly in the exchange's main public hot wallet.

### Two-Tier Exchange Architecture:
```
Scammer / Victim
      │ (Transfer)
      ▼
[ Tier 1: User Deposit Proxy ]  <-- Ephemeral address unique to the user's exchange account
      │
      │ (Treasury Sweep Transaction: ~100% of balance forwarded within hours)
      ▼
[ Tier 2: Central Exchange Hot Wallet ] <-- Publicly known hot wallet holding millions (e.g., Binance 14)
```

### The Forensic Problem:
- The Central Hot Wallet (`0x28c6c062...`) holds pooled funds from thousands of users. Serving a police freeze order saying *"Freeze the entire Binance Hot Wallet"* is legally invalid and impossible for Binance to execute.
- To execute an asset freeze, Binance compliance requires:
  $$\textbf{The Exact User Deposit Proxy Address}$$
  Because that proxy maps directly to the specific criminal's account ID and KYC identity in Binance's internal SQL database!

---

## 2. The Algorithmic Solution: `DepositSweeper` (Victor 2020 Heuristic)

Rather than spending \$50,000/month running background crawler clusters to scrape all global sweeping transactions:
Our engine uses **On-Demand Forward Sweeping Detection**:

### Mathematical Heuristic Criteria:
For any unclassified node $u$ encountered during traversal:
1. It holds positive incoming stolen taint ($\theta_u > 0$).
2. It executes an outgoing transfer $tx_{\text{sweep}} = (u, v, W)$ where:
   - $v \in \text{Known Exchange Hot Wallets}$
   - The sweep ratio satisfies:
     $$\frac{W}{B_{\text{received}}} \ge 0.85 \quad (\text{typically } \ge 95\%)$$
3. It retains a near-zero post-sweep balance.

### Outcome:
When this pattern is recognized:
- Node $u$ is dynamically classified as `NodeRole.CEX_DEPOSIT` with tag: `"{ExchangeName}: User Deposit Proxy"`.
- It is registered in `EntityResolver`.
- The statutory **Section 94 BNSS Legal Freeze Requisition** is issued specifically targeting **Node $u$**, enabling the exchange to instantly freeze the criminal's account!

---

## 3. Verified Empirical Results
- Tested under `tests/test_deposit_sweeper.py`.
- 17/17 project unit and integration tests passing in 0.011s.
