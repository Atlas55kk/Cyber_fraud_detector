"""
Module: dossier_generator.py
Generates statutory Law Enforcement Legal Requisition Notices under:
- Section 91 of the Code of Criminal Procedure, 1973 (CrPC)
- Section 94 of the Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)

Provides the exact evidence package required by Centralized Exchange Compliance Desks
(Binance, CoinDCX, WazirX, OKX) to immediately freeze accounts during the golden hours.
"""

import time
from typing import Dict, List, Optional, Any
from src.core.canvas import WhiteboardCanvas
from src.core.node_box import ForensicNodeBox
from src.attribution.entity_resolver import EntityInfo


class CaseDetails:
    """
    Police FIR / NCRP Incident metadata.
    """
    def __init__(
        self,
        ack_number: str = "NCRP/2026/910283",
        fir_number: str = "FIR No. 42/2026",
        police_station: str = "Cyber Crime Police Station, Central District",
        investigating_officer: str = "Inspector R. K. Sharma",
        victim_name: str = "Confidential / Victim",
        loss_inr: float = 50000.0,
        loss_crypto_str: str = "50,000 USDT"
    ):
        self.ack_number = ack_number
        self.fir_number = fir_number
        self.police_station = police_station
        self.investigating_officer = investigating_officer
        self.victim_name = victim_name
        self.loss_inr = loss_inr
        self.loss_crypto_str = loss_crypto_str


class LegalDossierGenerator:
    """
    Generates formal legal notice documents for law enforcement officers.
    """

    def __init__(self, canvas: WhiteboardCanvas):
        self.canvas = canvas

    def generate_section_94_bnss_notice(
        self,
        case: CaseDetails,
        target_cex_node: ForensicNodeBox,
        entity_info: Optional[EntityInfo] = None
    ) -> str:
        """
        Generates formal Section 94 BNSS (Sec 91 CrPC) Freeze Requisition Notice.
        """
        current_date = time.strftime("%d-%B-%Y %H:%M:%S IST", time.localtime())
        exchange_name = entity_info.name if entity_info else (target_cex_node.entity_tag or "Centralized Exchange")
        compliance_email = entity_info.compliance_email if entity_info else "compliance-desk@exchange.com"
        
        # Get path from crime root to target
        paths = self.canvas.trace_paths_to_address(target_cex_node.address)
        trail_hashes = paths[0] if paths else []

        trail_table_lines = []
        for i, h in enumerate(trail_hashes, 1):
            wire = self.canvas.wires.get(h)
            if wire:
                trail_table_lines.append(
                    f"| Hop {i} | `{wire.from_address[:10]}...` | `{wire.to_address[:10]}...` | "
                    f"{wire.value:.2f} {wire.token_symbol} | `{wire.tx_hash}` | {wire.timestamp} |"
                )

        trail_table = "\n".join(trail_table_lines)

        notice_content = f"""
================================================================================
OFFICE OF THE INVESTIGATING OFFICER, CYBER CRIME POLICE
GOVERNMENT OF INDIA / STATE POLICE
================================================================================

LEGAL REQUISITION NOTICE UNDER SECTION 94 OF BHARATIYA NAGARIK SURAKSHA SANHITA (BNSS), 2023
(FORMERLY SECTION 91 OF CODE OF CRIMINAL PROCEDURE, 1973 - CrPC)

To:
The Nodal Officer / Compliance Desk
{exchange_name}
Email: {compliance_email}

Date & Time of Requisition: {current_date}
Subject: IMMEDIATE FREEZE ORDER & INFORMATION REQUISITION REGARDING ILLICIT CRYPTOCURRENCY ASSETS

Reference:
- National Cyber Crime Reporting Portal (NCRP) Ack No: {case.ack_number}
- Police Station Case / FIR No: {case.fir_number}
- Police Station: {case.police_station}
- Investigating Officer: {case.investigating_officer}

--------------------------------------------------------------------------------
1. STATUTORY NOTICE & OPERATIVE INSTRUCTION
--------------------------------------------------------------------------------
WHEREAS, the undersigned Investigating Officer is inquiring into a cognizable offense 
involving online financial fraud under the Bharatiya Nyaya Sanhita (BNS) and Information 
Technology Act, 2000, wherein stolen funds amounting to INR {case.loss_inr:,.2f} ({case.loss_crypto_str}) 
were siphoned from the victim ({case.victim_name}).

NOW THEREFORE, in exercise of powers conferred under Section 94 of BNSS, 2023 (Section 91 CrPC), 
YOU ARE HEREBY DIRECTED TO:

1. IMMEDIATELY FREEZE / PLACE A RESTRICTIVE LIEN on the below-identified deposit account/wallet 
   and all associated fiat/crypto balances:
   TARGET DEPOSIT ADDRESS: `{target_cex_node.address}`
   IDENTIFIED STOLEN VALUE HELD: {target_cex_node.stolen_amount_held:,.2f} USDT
   CALCULATED TAINT PROPORTION: {target_cex_node.stolen_taint_ratio * 100:.1f}%

2. PREVENT ANY WITHDRAWAL, P2P TRADING, OR INTERNAL TRANSFER from the user account 
   associated with this deposit address with immediate effect.

3. FURNISH THE COMPLETE KYC DOSSIER of the account holder within 24 hours:
   a) Full Legal Name, Registered Mobile Number, and Email Address.
   b) Government ID Document copies (Passport, Aadhaar, PAN, or National ID).
   c) Associated Bank Account details used for P2P/fiat deposits or withdrawals.
   d) Complete IP login logs (with timestamps and port numbers).

--------------------------------------------------------------------------------
2. DETERMINISTIC CHAIN OF CUSTODY (BLOCKCHAIN EVIDENCE TRAIL)
--------------------------------------------------------------------------------
The flow of stolen assets from the crime origin to your exchange deposit endpoint 
was deterministically reconstructed and verified via conservation-of-mass taint analysis:

- Crime Origin Wallet: `{self.canvas.incident_root_address}`
- Total Stolen Ingress: {self.canvas.initial_stolen_amount:,.2f} USDT
- Total Hops to Cash-Out: {len(trail_hashes)}

| Step | Sender Address | Receiver Address | Value | Transaction Hash | Timestamp |
| :--- | :--- | :--- | :--- | :--- | :--- |
{trail_table}

--------------------------------------------------------------------------------
3. LEGAL PENALTY CLAUSE
--------------------------------------------------------------------------------
Failure to comply with this statutory requisition or any willful dissipation of the 
subject assets after receipt of this notice shall attract penal action under Section 
223 (Disobedience to order duly promulgated by public servant) and Section 249 of the 
Bharatiya Nyaya Sanhita, 2023.

Issued under my Hand and Seal of the Cyber Crime Police Station.

(Investigating Officer)
{case.investigating_officer}
{case.police_station}
================================================================================
"""
        return notice_content.strip()
