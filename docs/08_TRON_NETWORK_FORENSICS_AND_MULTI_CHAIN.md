# Module 8: TRON (TRC-20 USDT) Forensics & Multi-Chain Architecture

## 1. Why TRON is the Primary Cybercrime Vector in India

According to threat intelligence from the **Indian Cyber Crime Coordination Centre (I4C)** under the **Ministry of Home Affairs (MHA)**:
- Over **90% of cryptocurrency fraud proceeds** reported on the National Cyber Crime Reporting Portal (`cybercrime.gov.in` / **1930 Helpline**) do **not** use Bitcoin or Ethereum mainnet.
- Fraud syndicates overwhelmingly choose **Tether USD on the TRON network (TRC-20 USDT)**.

### Primary Drivers:
1. **Negligible Transaction Fees:** Transferring USDT on TRON costs ~13.5 TRX (<\$1.00 USD), compared to \$5–\$50+ on Ethereum. This allows fraudsters to execute multi-hop peel chains and rapid smurfing splits at virtually zero cost.
2. **High P2P Liquidity on Asian / Offshore Desks:** Offshore exchanges (Binance P2P, Bybit, KuCoin, OKX) feature massive INR-to-USDT (TRC-20) P2P order books.
3. **Speed of Finality:** TRON blocks are produced every 3 seconds (DPoS consensus), enabling syndicates to move funds across 5 hops in under 90 seconds.

---

## 2. Technical Implementation: `TronFetcher`

We implemented `src/fetchers/tron_fetcher.py` to ingest and normalize TRON transactions into our unified forensic pipeline.

### A. Contract Address Standard
Tether on TRON is an official smart contract deployed at:
$$\text{Contract Address: } \texttt{TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t}$$

### B. Address Encoding & Normalization
- TRON uses **Base58Check** encoding starting with `'T'` (21 bytes starting with byte `0x41`).
- `TronFetcher` parses the raw 6-decimal transfer amounts ($\text{Amount}_{\text{USDT}} = \frac{\text{quant}}{10^6}$) and converts energy/bandwidth burn fees into TRX equivalents.
- Transactions are mapped into `ForensicWire` objects with `token_type = TokenType.TRC20`.

### C. Rate-Limit Shielding & Local Cache
- TRON public APIs (Tronscan / TronGrid) limit unauthenticated queries to 3–5 req/sec.
- `TronFetcher` includes a thread-safe delay governor ($\Delta t \ge 0.35\text{s}$) and stores responses in `data/cache/tron/`, preventing HTTP 429 bans.

---

## 3. Verified TRON Exchange Hot Wallets in `data/known_entities/registry.json`

| Exchange Name | Hot / Deposit Address | Compliance Jurisdiction |
| :--- | :--- | :--- |
| **Binance TRON Hot Wallet 1** | `TPY9W8PnmgCJnUqUrYJ7p4G93F6r8eH1e6` | Global VASP (`compliance@binance.com`) |
| **Binance TRON Hot Wallet 2** | `TJDnQoxM2w8BsukZuv41RLNttb4kYtqJ8n` | Global VASP |
| **CoinDCX TRON Hot Wallet** | `TYDzsYUEpvnYmQk4zGP9sWWcTEd2MiAtW6` | India (FIU-IND Registered, `legal@coindcx.com`) |
| **WazirX TRON Hot Wallet** | `TLyBzAU5kZ7XnZ98M1v3E6VwB8kL5yA4z1` | India (FIU-IND Registered, `nodal@wazirx.com`) |
| **OKX TRON Hot Wallet** | `TFFv9F6m4vY891jF1N5vX8L1zK9J2b7Ye4` | Global VASP (`compliance@okx.com`) |
| **SunSwap V2 Router (TRON DEX)**| `TKzxdSv2FZKQrEqkKVgp5DcwEXBEKMg2Ax` | Smart Contract |

---

## 4. Multi-Chain CLI Execution
The engine can now trace both EVM and TRON incidents via `main.py`:
```bash
# Trace both Ethereum ERC-20 and TRON TRC-20 simultaneously
python main.py --chain both

# Trace only TRON cybercrime incidents
python main.py --chain tron

# Trace only EVM incidents
python main.py --chain evm
```

Both paths automatically generate statutory **Section 94 BNSS Legal Requisition Notices** and dedicated interactive whiteboard canvases.
