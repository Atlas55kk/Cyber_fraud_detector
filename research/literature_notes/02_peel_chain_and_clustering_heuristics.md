# Literature Deep-Dive: Peel Chains & Address Clustering Heuristics
**Papers:**  
- *How to Peel a Million: Validating and Expanding Bitcoin Clusters* (Kappos et al., 2022, arXiv:2205.13882)  
- *A Fistful of Bitcoins: Characterizing Payments Among Men with No Names* (Meiklejohn et al., IMC 2013)  
- *Exploring Unconfirmed Transactions for Effective Address Clustering* (Wang et al., 2023, arXiv:2303.01012)

---

## 1. The Anatomy of a Peel Chain

A **Peel Chain** is the most widely documented money laundering topology in cryptocurrency crime. It represents a single entity laundering a large sum through sequential, micro-stripping steps:

$$\text{Root Wallet } (S) \xrightarrow{\text{Peel } p_1} \text{Deposit Address } (D_1)$$
$$\downarrow \text{Bulk } (B_1)$$
$$\text{Hop 1 } (H_1) \xrightarrow{\text{Peel } p_2} \text{Deposit Address } (D_2)$$
$$\downarrow \text{Bulk } (B_2)$$
$$\text{Hop 2 } (H_2) \xrightarrow{\text{Peel } p_3} \text{Deposit Address } (D_3) \dots$$

### Formal Mathematical Criteria for Peel Chain Detection:
1. **Asymmetric Out-Degree:** Exactly two dominant outputs ($|Out(H_i)| = 2$).
2. **Value Asymmetry:**
   $$\frac{v_{\text{peel}}}{v_{\text{bulk}}} < \delta_{\text{ratio}} \quad (\text{typically } \delta_{\text{ratio}} \le 0.20)$$
   One output receives the lion's share ($\ge 80\%$), while the smaller output is the "peeled" fraction.
3. **Fresh Next-Hop Address:** The address receiving $v_{\text{bulk}}$ has **no prior transaction history** before this incoming transfer (a freshly generated wallet).
4. **Short Dormancy / High Velocity:** The bulk address initiates its next transaction within a tight temporal window ($\Delta t < 6 \text{ hours}$).
5. **Chain Length Criterion:** The pattern repeats for $L \ge 3$ consecutive hops.

---

## 2. Adaptation to Account-Based Systems (Ethereum & TRON)

In UTXO systems (Bitcoin), peel chains are constrained by transaction output structure. In Account-based systems (Ethereum, TRON USDT):
- The scammer sends two separate transactions from wallet $H_i$:
  1. Transfer amount $v_{\text{peel}}$ to a centralized exchange (CEX) deposit address.
  2. Transfer amount $v_{\text{bulk}} \approx \text{Balance} - v_{\text{peel}} - \text{Gas}$ to a brand new intermediate transit wallet $H_{i+1}$.
- Because the transactions are separate, standard UTXO heuristics miss them!
- **Our Algorithmic Innovation:** Group outgoing transactions from an account within temporal window $W$ into a **virtual transaction bundle**, then apply the value asymmetry and fresh-address test.

---

## 3. Implementation in Our SIH Engine
- When a peel chain pattern is recognized, our engine **collapses the linear chain** into a single logical entity (Cluster $C_{scam}$).
- This stops the engine from wasting graph-traversal quota on intermediate hops $H_1, H_2, \dots, H_n$ and immediately flags all peeled addresses $D_1, D_2, \dots, D_n$ for exchange freeze requests.
