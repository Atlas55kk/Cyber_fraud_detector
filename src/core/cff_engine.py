"""
Module: cff_engine.py
Crypto Forensic File (.cff) Specification and Compiler Engine.

Defines the proprietary, tamper-evident case container format (.cff) for
blockchain fraud tracing, designed specifically for Indian Law Enforcement (I4C/MHA).

Key Properties:
- Self-contained: Contains full graph topology (nodes, wires), case metadata, and ML verdict.
- Cryptographic Integrity: Sealed with SHA-256 digest under Section 63 of BNSS, 2023.
- Air-Gapped Portability: Can be transferred via pen drive and rendered without internet access.
"""

import json
import hashlib
import time
from typing import Dict, Any, List, Optional, Tuple
from src.core.canvas import WhiteboardCanvas
from src.core.node_box import ForensicNodeBox, NodeRole
from src.core.wire_edge import ForensicWire, TokenType
from src.reporting.dossier_generator import CaseDetails


CFF_FORMAT_VERSION = "1.0.0-FORENSIC-BNSS"


class CryptoForensicFileEngine:
    """
    Compiler and interpreter for the .cff case container file format.
    """

    @staticmethod
    def compute_payload_hash(payload_dict: Dict[str, Any]) -> str:
        """
        Computes deterministic SHA-256 digest of payload data excluding the seal itself.
        """
        data_copy = dict(payload_dict)
        data_copy.pop("cryptographic_seal", None)
        canonical_json = json.dumps(data_copy, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    @classmethod
    def export_cff(
        cls,
        canvas: WhiteboardCanvas,
        case: CaseDetails,
        ml_intelligence: Optional[Dict[str, Any]] = None,
        chain: str = "EVM",
        victim_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Serializes canvas, case metadata, and ML analysis into a sealed .cff structure.
        """
        export_time = int(time.time())

        # Serialize Nodes (The "Boxes")
        nodes_data = []
        for addr, node in canvas.nodes.items():
            nodes_data.append({
                "address": node.address,
                "role": node.role.value,
                "entity_tag": node.entity_tag,
                "current_balance": node.current_balance,
                "stolen_taint_ratio": round(node.stolen_taint_ratio, 4),
                "stolen_amount_held": round(node.stolen_amount_held, 2),
                "gas_burned_total": node.gas_burned_total,
                "first_seen": node.first_seen_timestamp,
                "last_seen": node.last_seen_timestamp
            })

        # Serialize Wires (The "Dots and Connections")
        wires_data = []
        for tx_hash, wire in canvas.wires.items():
            wires_data.append({
                "tx_hash": wire.tx_hash,
                "from_address": wire.from_address,
                "to_address": wire.to_address,
                "value": wire.value,
                "token_symbol": wire.token_symbol,
                "token_type": wire.token_type.value,
                "gas_fee": wire.gas_fee,
                "timestamp": wire.timestamp,
                "block_number": wire.block_number,
                "is_contract_call": wire.is_contract_call
            })

        # Actionable CEX off-ramps summary
        actionable_offramps = []
        for n in canvas.nodes.values():
            if n.role == NodeRole.CEX_DEPOSIT:
                actionable_offramps.append({
                    "address": n.address,
                    "entity_tag": n.entity_tag or "Centralized Exchange",
                    "stolen_held": n.stolen_amount_held,
                    "taint_pct": round(n.stolen_taint_ratio * 100, 1),
                    "trail_hops": len(canvas.trace_paths_to_address(n.address)[0]) if canvas.trace_paths_to_address(n.address) else 1
                })

        payload = {
            "cff_version": CFF_FORMAT_VERSION,
            "metadata": {
                "case_id": f"CASE-{canvas.incident_root_address[:10] if canvas.incident_root_address else 'GEN'}-{export_time}",
                "ncrp_ack_number": case.ack_number,
                "fir_number": case.fir_number,
                "police_station": case.police_station,
                "investigating_officer": case.investigating_officer,
                "complainant_name": case.victim_name,
                "loss_inr": case.loss_inr,
                "loss_crypto_str": case.loss_crypto_str,
                "chain": chain,
                "incident_timestamp": canvas.incident_timestamp or export_time,
                "crime_root_address": canvas.incident_root_address,
                "victim_address": victim_address or "Unspecified",
                "initial_stolen_amount": canvas.initial_stolen_amount,
                "export_timestamp": export_time,
                "export_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(export_time))
            },
            "graph": {
                "nodes": nodes_data,
                "wires": wires_data,
                "stats": canvas.summary_stats()
            },
            "actionable_freeze_targets": actionable_offramps,
            "ml_intelligence": ml_intelligence or {
                "campaign_name": "PENDING_ANALYSIS",
                "overall_risk_score": 50,
                "investigation_priority": "MEDIUM",
                "topological_fingerprint": "DIRECT_OFFRAMP",
                "summary": "Forensic case initialized."
            }
        }

        # Sign with Section 63 BNSS Cryptographic Seal
        seal_hash = cls.compute_payload_hash(payload)
        payload["cryptographic_seal"] = {
            "algorithm": "SHA-256",
            "statutory_reference": "Section 63 of Bharatiya Nagarik Suraksha Sanhita, 2023",
            "integrity_hash": seal_hash,
            "tamper_evident": True
        }

        return payload

    @classmethod
    def import_cff(cls, cff_data_or_json_str: Any) -> Tuple[WhiteboardCanvas, CaseDetails, Dict[str, Any], bool, str]:
        """
        Parses and verifies a .cff case file.
        
        Returns:
            Tuple of (reconstructed_canvas, case_details, ml_intelligence, is_tamper_free, status_message)
        """
        if isinstance(cff_data_or_json_str, str):
            try:
                data = json.loads(cff_data_or_json_str)
            except Exception as ex:
                raise ValueError(f"Invalid .cff file: JSON decode failure ({ex})")
        elif isinstance(cff_data_or_json_str, dict):
            data = cff_data_or_json_str
        else:
            raise TypeError("Expected string or dictionary for .cff parsing.")

        # 1. Verify Cryptographic Integrity Seal
        seal = data.get("cryptographic_seal", {})
        expected_hash = seal.get("integrity_hash", "")
        computed_hash = cls.compute_payload_hash(data)

        is_tamper_free = (expected_hash == computed_hash) and (len(expected_hash) == 64)
        if is_tamper_free:
            status_msg = "CRYPTOGRAPHIC INTEGRITY VERIFIED (SEC 63 BNSS ADMISSIBLE)"
        else:
            status_msg = f"TAMPER DETECTED: Hash mismatch! Expected {expected_hash[:12]}..., computed {computed_hash[:12]}..."

        # 2. Reconstruct Case Metadata
        meta = data.get("metadata", {})
        case = CaseDetails(
            ack_number=meta.get("ncrp_ack_number", "NCRP/UNKNOWN"),
            fir_number=meta.get("fir_number", "FIR/UNKNOWN"),
            police_station=meta.get("police_station", "Cyber Crime Police Station"),
            investigating_officer=meta.get("investigating_officer", "Investigating Officer"),
            victim_name=meta.get("complainant_name", "Complainant"),
            loss_inr=float(meta.get("loss_inr", 0.0)),
            loss_crypto_str=meta.get("loss_crypto_str", "USDT")
        )

        # 3. Reconstruct WhiteboardCanvas
        canvas = WhiteboardCanvas(canvas_id=meta.get("case_id", "Imported_CFF_Case"))
        root_addr = meta.get("crime_root_address")
        stolen_amt = float(meta.get("initial_stolen_amount", 0.0))
        inc_time = int(meta.get("incident_timestamp", 0))

        if root_addr:
            canvas.set_incident_root(root_addr, stolen_amt, inc_time)

        # Populate Nodes
        graph_data = data.get("graph", {})
        for n in graph_data.get("nodes", []):
            try:
                role = NodeRole(n.get("role", NodeRole.UNKNOWN.value))
            except ValueError:
                role = NodeRole.UNKNOWN

            canvas.get_or_create_node(
                address=n["address"],
                role=role,
                initial_balance=float(n.get("current_balance", 0.0)),
                stolen_taint=float(n.get("stolen_taint_ratio", 0.0)),
                stolen_held=float(n.get("stolen_amount_held", 0.0)),
                entity_tag=n.get("entity_tag")
            )

        # Populate Wires
        for w in graph_data.get("wires", []):
            try:
                token_type = TokenType(w.get("token_type", TokenType.ERC20.value))
            except ValueError:
                token_type = TokenType.ERC20

            canvas.add_wire(
                tx_hash=w["tx_hash"],
                from_address=w["from_address"],
                to_address=w["to_address"],
                value=float(w.get("value", 0.0)),
                token_symbol=w.get("token_symbol", "USDT"),
                token_type=token_type,
                gas_fee=float(w.get("gas_fee", 0.0)),
                timestamp=int(w.get("timestamp", 0)),
                block_number=int(w.get("block_number", 0)),
                is_contract_call=bool(w.get("is_contract_call", False))
            )

        ml_intel = data.get("ml_intelligence", {})
        return canvas, case, ml_intel, is_tamper_free, status_msg
