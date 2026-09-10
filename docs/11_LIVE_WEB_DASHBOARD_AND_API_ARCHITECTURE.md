# Module 11: Live Web Application & REST API Architecture

## 1. System Overview

To bridge the gap between algorithmic graph engines and operational law enforcement officers, we created a self-contained, real-time web application running on **FastAPI** and **Cytoscape.js**.

### Key Capabilities for Investigating Officers:
1. **Interactive Control Bar:** Allows officers to input any reported scam wallet (EVM or TRON), select the currency, and click `⚡ Initiate Forensic Trace`.
2. **Real-Time Graph Rendering:** Dynamically draws the money trail across an infinite whiteboard canvas, color-coding nodes by their role (Crime Root, Mule Transit, Privacy Mixer, Actionable CEX Deposit Proxy).
3. **Forensic Evidence Inspector:** Clicking any node or wire displays address attributes, current balances, calculated stolen taint percentages, and gas burned.
4. **One-Click Section 94 BNSS Legal Freeze Requisition:** Generates a statutory requisition notice pre-formatted for Binance, CoinDCX, or WazirX compliance desks with an in-browser copy and export option.
5. **Live Event Console:** Displays a typewriter-style audit log of every heuristic decision (PPR score, peel chain detected, sweep detected, CEX sink located).

---

## 2. API Endpoints

| Endpoint | Method | Purpose | Input / Output |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | Serves the interactive HTML/JS dashboard | HTML Document |
| `/api/health` | `GET` | Health check & engine status | JSON status |
| `/api/trace` | `POST` | Executes real-time $H\text{-BFSTP}$ graph search | Request: `{wallet_address, chain, stolen_amount}`<br>Response: `{elements, stats, actionable_cex, logs}` |
| `/api/generate_notice` | `POST` | Generates formal Section 94 BNSS notice | Request: `{ack_number, fir_number, target_address}`<br>Response: `{notice_text}` |

---

## 3. How to Launch & Access

To start the local investigation server:
```bash
python server.py
```
Open your browser and navigate to:
$$\texttt{http://localhost:8000}$$

---

## 4. Test Verification
Validated under `tests/test_web_api.py`:
- 26/26 full project unit and integration tests passing in 0.048s.
