"""
Module: app.py
FastAPI Web Server for the Crypto Fraud Tracing Engine (MHA / SIH PS 26183).
Provides REST APIs for real-time graph tracing, dynamic entity attribution,
statutory notice generation, and interactive frontend serving.
"""

import os
import time
import math
import re
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.core.canvas import WhiteboardCanvas
from src.core.node_box import NodeRole
from src.core.wire_edge import ForensicWire, TokenType
from src.core.taint_engine import TaintEngine, TaintModel
from src.attribution.entity_resolver import EntityResolver
from src.algorithms.priority_search import PrioritySearchEngine, SearchConfig
from src.algorithms.peel_detector import PeelChainDetector
from src.algorithms.smurf_filter import SmurfingFilter
from src.algorithms.mixer_linker import MixerLinker, MixerDeposit, MixerWithdrawal
from src.fetchers.mock_generator import MockFraudScenarioGenerator
from src.fetchers.etherscan_fetcher import EtherscanFetcher
from src.fetchers.tron_fetcher import TronFetcher
from src.reporting.dossier_generator import LegalDossierGenerator, CaseDetails
from src.reporting.pdf_generator import LegalNoticePDFGenerator
from src.ml.transaction_classifier import TransactionMicroClassifier
from src.ml.campaign_classifier import CampaignMacroClassifier
from src.core.cff_engine import CryptoForensicFileEngine

app = FastAPI(
    title="Crypto Fraud Tracing Engine (MHA / SIH PS 26183)",
    description="Algorithmic Blockchain Forensic Engine for Indian Law Enforcement Agencies",
    version="1.0.0"
)

# Shared In-Memory Entities and Live Blockchain Fetchers
entity_resolver = EntityResolver()
etherscan_fetcher = EtherscanFetcher()
tron_fetcher = TronFetcher()
micro_classifier = TransactionMicroClassifier()
macro_classifier = CampaignMacroClassifier()

# Request Models
class TraceRequest(BaseModel):
    wallet_address: str
    chain: str = "evm" # "evm" or "tron"
    stolen_amount: float = 50000.0
    token_symbol: str = "USDT"
    mode: str = "auto" # "auto", "live", "benchmark"
    victim_address: Optional[str] = None
    incident_timestamp: Optional[int] = None
    fir_number: Optional[str] = "FIR No. 42/2026"
    ack_number: Optional[str] = "NCRP/2026/910283"
    complainant_name: Optional[str] = "Confidential Complainant"
    loss_inr: Optional[float] = 4250000.0

class CFFLoadRequest(BaseModel):
    cff_content: str

class NoticeRequest(BaseModel):
    ack_number: str = "NCRP/2026/881230"
    fir_number: str = "FIR 109/2026 (Cyber Crime PS)"
    police_station: str = "Cyber Crime Police Station, Central District"
    investigating_officer: str = "Inspector R. K. Sharma"
    victim_name: str = "Shri Rajesh Kumar"
    loss_inr: float = 4250000.0
    loss_crypto_str: str = "50,000 USDT"
    target_address: str
    practice_mode: bool = True # Defaults to True for safe practice/sandbox


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """
    Serves the primary interactive forensic whiteboard dashboard.
    """
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Forensic Dashboard Not Found. Please build static/index.html</h1>"


@app.get("/api/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "engine": "H-BFSTP Forensic Graph Engine",
        "jurisdiction": "Ministry of Home Affairs (MHA) / I4C",
        "live_connectors": ["Blockscout/Etherscan EVM", "Tronscan TRC-20"],
        "timestamp": int(time.time())
    }


@app.post("/api/trace")
async def execute_trace(req: TraceRequest):
    """
    Executes real-time priority graph traversal and returns Cytoscape elements and metrics.
    Supports both live on-chain mainnet traversal and deterministic offline forensic benchmarks.
    """
    clean_addr = req.wallet_address.strip()
    if not clean_addr:
        raise HTTPException(status_code=400, detail="Wallet address cannot be empty.")

    # Security Guard: Prevent string bombs, XSS, and command injection
    if len(clean_addr) > 128 or not re.match(r"^[a-zA-Z0-9_]{1,128}$", clean_addr):
        raise HTTPException(
            status_code=400,
            detail="Invalid wallet address format. Must be alphanumeric or standard identifier up to 128 characters."
        )

    # Numeric Boundary Guard: Positive finite amount
    if not math.isfinite(req.stolen_amount) or req.stolen_amount <= 0 or req.stolen_amount > 1e12:
        raise HTTPException(
            status_code=400,
            detail="Stolen amount must be a positive finite numeric value."
        )

    canvas = WhiteboardCanvas(canvas_id=f"Case_{clean_addr[:8]}")
    taint_engine = TaintEngine(model=TaintModel.HAIRCUT, min_taint_threshold=0.01)
    
    # Configure search engine budget
    search_cfg = SearchConfig(max_hops=4, max_nodes_budget=35, min_taint_ratio=0.01)
    search_engine = PrioritySearchEngine(canvas, taint_engine, entity_resolver, config=search_cfg)

    inc_time = req.incident_timestamp or (int(time.time()) - 3600)
    canvas.set_incident_root(clean_addr, req.stolen_amount, inc_time)
    
    # Determine network and format
    is_tron = req.chain.lower() == "tron" or clean_addr.startswith("T")
    chain_name = "TRON" if is_tron else "EVM"
    
    logs: List[str] = [
        f"Ingested reported wallet: {clean_addr}",
        f"Selected Network: {chain_name} | Reported Loss: {req.stolen_amount:,.2f} {req.token_symbol}"
    ]

    # Correlate Victim Entry if provided in Intake Form
    if req.victim_address and req.victim_address.strip():
        clean_victim = WhiteboardCanvas.normalize_address(req.victim_address)
        canvas.get_or_create_node(clean_victim, role=NodeRole.VICTIM)
        canvas.add_wire(
            tx_hash=f"0xtx_ingress_{int(time.time())}",
            from_address=clean_victim,
            to_address=clean_addr,
            value=req.stolen_amount,
            token_symbol=req.token_symbol,
            timestamp=inc_time
        )
        logs.append(f"Correlated Crime Origin: Victim ({clean_victim[:10]}...) -> Scammer Ingress ({clean_addr[:10]}...)")

    # Evaluate whether to trigger live on-chain ingestion
    is_real_candidate = False
    if is_tron and len(clean_addr) == 34 and clean_addr.startswith("T"):
        is_real_candidate = True
    elif (not is_tron) and len(clean_addr) == 42 and clean_addr.lower().startswith("0x"):
        is_real_candidate = True

    should_try_live = (req.mode.lower() == "live") or (
        req.mode.lower() == "auto" and is_real_candidate and not clean_addr.lower().startswith("0xscam")
    )

    is_live_traced = False
    source_label = "Forensic Benchmark"

    if should_try_live:
        live_fetcher = tron_fetcher if is_tron else etherscan_fetcher
        explorer_name = "Tronscan Mainnet" if is_tron else "Blockscout / EVM Explorer"
        logs.append(f"[LIVE CONNECTOR] Interfacing with {explorer_name} RPC nodes...")

        try:
            raw_wires = live_fetcher.fetch_outgoing_transactions(clean_addr)
            if raw_wires:
                is_live_traced = True
                source_label = f"Live Mainnet ({explorer_name})"
                logs.append(f"[LIVE ON-CHAIN] Verified {len(raw_wires)} genuine outgoing transactions for root account.")
                fetcher = lambda a: live_fetcher.fetch_outgoing_transactions(a)
            else:
                logs.append(f"[LIVE EXPLORER] Address has 0 outgoing transactions on record. Activating high-fidelity benchmark.")
        except Exception as ex:
            logs.append(f"[LIVE FAILOVER] Explorer communication error ({str(ex)}). Activating high-fidelity benchmark.")

    if not is_live_traced:
        # Load high-fidelity realistic benchmark scenario
        if is_tron:
            binance_tron = "TPY9W8PnmgCJnUqUrYJ7p4G93F6r8eH1e6"
            coindcx_tron = "TYDzsYUEpvnYmQk4zGP9sWWcTEd2MiAtW6"
            mule1 = "TMuleTransit_Beta_481029"
            mule2 = "TMuleTransit_Gamma_771928"

            tron_mock_db = {
                clean_addr: [
                    ForensicWire("0xtx_trc_1", clean_addr, mule1, req.stolen_amount * 0.6, token_symbol="USDT", token_type=TokenType.TRC20, gas_fee=13.5, timestamp=int(time.time()) - 3000),
                    ForensicWire("0xtx_trc_2", clean_addr, mule2, req.stolen_amount * 0.4, token_symbol="USDT", token_type=TokenType.TRC20, gas_fee=13.5, timestamp=int(time.time()) - 2800),
                ],
                mule1: [
                    ForensicWire("0xtx_trc_3", mule1, binance_tron, req.stolen_amount * 0.6, token_symbol="USDT", token_type=TokenType.TRC20, gas_fee=13.5, timestamp=int(time.time()) - 1500)
                ],
                mule2: [
                    ForensicWire("0xtx_trc_4", mule2, coindcx_tron, req.stolen_amount * 0.4, token_symbol="USDT", token_type=TokenType.TRC20, gas_fee=13.5, timestamp=int(time.time()) - 1200)
                ]
            }
            fetcher = lambda a: tron_mock_db.get(a if a.startswith("T") else a.lower(), [])
            logs.append("Ingested TRON (TRC-20 USDT) multi-mule transit benchmark.")
        else:
            mock_evm = MockFraudScenarioGenerator.generate_problem_statement_case()
            fetcher = lambda a: mock_evm.get(a.lower(), [])
            logs.append("Ingested EVM multi-hop structuring & peel-chain benchmark.")

    # Execute Priority Best-First Search
    actionable_cex_nodes = search_engine.run_trace(fetcher)
    logs.append(f"Priority Best-First Search evaluated {len(canvas.nodes)} accounts across {len(canvas.wires)} wires.")
    
    # Detect Peel Chains
    peel_detector = PeelChainDetector()
    peel_chains = peel_detector.detect_peel_chains(canvas)
    if peel_chains:
        logs.append(f"Topological Pattern: Detected {len(peel_chains)} active Peel Chains.")

    # Detect Smurfing
    smurf_filter = SmurfingFilter()
    smurf_clusters = smurf_filter.detect_smurfing_clusters(canvas)
    if smurf_clusters:
        logs.append(f"Topological Pattern: Identified {len(smurf_clusters)} structured Smurfing fan-out clusters.")

    # Check actionable targets
    for node in actionable_cex_nodes:
        logs.append(f"ACTIONABLE CASH-OUT IDENTIFIED: {node.entity_tag} ({node.address[:10]}...) holding {node.stolen_amount_held:,.2f} USDT ({node.stolen_taint_ratio*100:.1f}% taint)")

    stats = canvas.summary_stats()
    elements = canvas.to_cytoscape_elements()

    actionable_data = [
        {
            "address": n.address,
            "entity_tag": n.entity_tag,
            "stolen_held": n.stolen_amount_held,
            "taint_pct": round(n.stolen_taint_ratio * 100, 1),
            "paths": canvas.trace_paths_to_address(n.address)
        }
        for n in actionable_cex_nodes
    ]

    # Two-Tier ML Intelligence Evaluation
    macro_eval = macro_classifier.evaluate_canvas(canvas)
    logs.append(
        f"[AI/ML CLASSIFIER] Macro Campaign Profile: {macro_eval.campaign_name} "
        f"(Risk Score: {macro_eval.overall_risk_score}/100 | Priority: {macro_eval.investigation_priority})"
    )

    ml_intel = {
        "campaign_name": macro_eval.campaign_name,
        "overall_risk_score": macro_eval.overall_risk_score,
        "investigation_priority": macro_eval.investigation_priority,
        "topological_fingerprint": macro_eval.topological_fingerprint,
        "cex_offramps_detected": macro_eval.cex_offramps_detected,
        "summary": macro_eval.summary
    }

    # Export Sealed .cff Container (Section 63 BNSS Electronic Evidence)
    case_meta = CaseDetails(
        ack_number=req.ack_number or "NCRP/2026/910283",
        fir_number=req.fir_number or "FIR No. 42/2026",
        police_station="Cyber Crime Police Station, Central District",
        investigating_officer="Inspector R. K. Sharma",
        victim_name=req.complainant_name or "Confidential Complainant",
        loss_inr=req.loss_inr or (req.stolen_amount * 85.0),
        loss_crypto_str=f"{req.stolen_amount:,.2f} {req.token_symbol}"
    )
    cff_container = CryptoForensicFileEngine.export_cff(
        canvas=canvas,
        case=case_meta,
        ml_intelligence=ml_intel,
        chain=chain_name,
        victim_address=req.victim_address
    )

    return {
        "success": True,
        "chain": chain_name,
        "is_live": is_live_traced,
        "data_source": source_label,
        "stats": stats,
        "elements": elements,
        "actionable_cex": actionable_data,
        "ml_intelligence": ml_intel,
        "cff_container": cff_container,
        "logs": logs
    }


@app.post("/api/generate_notice")
async def create_legal_notice(req: NoticeRequest):
    """
    Generates statutory Section 94 BNSS (Sec 91 CrPC) requisition notice.
    Supports Practice/Simulation mode with forensic reasoning disclaimers.
    """
    clean_target = WhiteboardCanvas.normalize_address(req.target_address)
    
    # Reconstruct canvas state for notice
    canvas = WhiteboardCanvas(canvas_id="Notice_Reconstruction")
    canvas.set_incident_root("0xscammer_wallet", 50000.0, int(time.time()) - 3600)
    
    entity_info = entity_resolver.resolve(clean_target)
    entity_name = entity_info.name if entity_info else "Identified Centralized Exchange Target"

    # Target node
    target_node = canvas.get_or_create_node(
        address=clean_target,
        role=NodeRole.CEX_DEPOSIT,
        stolen_held=20000.0,
        stolen_taint=1.0,
        entity_tag=entity_name
    )
    
    # Wire sequence
    canvas.add_wire("0xtx_hop_1", "0xscammer_wallet", "0xmule_1", 20000.0, timestamp=int(time.time()) - 3000)
    canvas.add_wire("0xtx_hop_2", "0xmule_1", clean_target, 20000.0, timestamp=int(time.time()) - 1500)

    dossier_gen = LegalDossierGenerator(canvas)
    case = CaseDetails(
        ack_number=req.ack_number,
        fir_number=req.fir_number,
        police_station=req.police_station,
        investigating_officer=req.investigating_officer,
        victim_name=req.victim_name,
        loss_inr=req.loss_inr,
        loss_crypto_str=req.loss_crypto_str
    )

    base_notice = dossier_gen.generate_section_94_bnss_notice(case, target_node, entity_info)

    if req.practice_mode:
        disclaimer_header = (
            "================================================================================\n"
            "  [TRAINING & PRACTICE SIMULATION ONLY — NOT AN OFFICIAL NOTICE]  \n"
            "SIMULATION MODE IS ACTIVE. THIS DOCUMENT IS A DRY-RUN FORENSIC DRAFT.\n"
            "DO NOT SERVE OR TRANSMIT TO COMPLIANCE DESK / NODAL OFFICER.\n"
            "================================================================================\n\n"
        )
        logic_explanation = (
            "\n\n"
            "================================================================================\n"
            "  FORENSIC LOGIC BREAKDOWN (WHY THIS BRANCH WAS SELECTED FOR FREEZE)\n"
            "================================================================================\n"
            f"1. Target Entity: {entity_name}\n"
            f"2. Target Address: {clean_target}\n"
            "3. Address Role: User Deposit Proxy (Victor 2020 on-demand sweep heuristic)\n"
            "4. Taint Level: 100% Proportional Haircut taint mapped to crime root\n"
            "5. Evidence Integrity: Unbroken 2-hop cryptographic ledger trail\n"
            "6. Practice Objective: Validate the mathematical trail and KYC requirements\n"
            "   without triggering real-world statutory dispatch.\n"
            "================================================================================"
        )
        final_notice = disclaimer_header + base_notice + logic_explanation
    else:
        final_notice = base_notice

    return {
        "success": True,
        "practice_mode": req.practice_mode,
        "target_address": clean_target,
        "entity_name": entity_name,
        "notice_text": final_notice
    }


@app.post("/api/download_notice_pdf")
async def download_notice_pdf(req: NoticeRequest):
    """
    Generates and streams formal Section 94 BNSS Requisition Notice as a downloadable PDF.
    Watermarked as investigative draft with no unauthorized seals.
    """
    clean_target = WhiteboardCanvas.normalize_address(req.target_address)
    
    canvas = WhiteboardCanvas(canvas_id="PDF_Notice_Generation")
    canvas.set_incident_root("0xscammer_wallet", req.loss_inr / 85.0, int(time.time()) - 3600)
    
    entity_info = entity_resolver.resolve(clean_target)
    entity_name = entity_info.name if entity_info else "Identified Centralized Exchange Target"

    target_node = canvas.get_or_create_node(
        address=clean_target,
        role=NodeRole.CEX_DEPOSIT,
        stolen_held=req.loss_inr / 85.0,
        stolen_taint=1.0,
        entity_tag=entity_name
    )

    canvas.add_wire("0xtx_hop_1", "0xscammer_wallet", "0xmule_1", req.loss_inr / 85.0, timestamp=int(time.time()) - 3000)
    canvas.add_wire("0xtx_hop_2", "0xmule_1", clean_target, req.loss_inr / 85.0, timestamp=int(time.time()) - 1500)

    case = CaseDetails(
        ack_number=req.ack_number,
        fir_number=req.fir_number,
        police_station=req.police_station,
        investigating_officer=req.investigating_officer,
        victim_name=req.victim_name,
        loss_inr=req.loss_inr,
        loss_crypto_str=req.loss_crypto_str
    )

    pdf_gen = LegalNoticePDFGenerator(canvas)
    pdf_bytes = pdf_gen.generate_pdf_bytes(case, target_node, entity_info)

    safe_target = re.sub(r"[^a-zA-Z0-9]", "_", clean_target)[:12]
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=Section_94_BNSS_{safe_target}.pdf"
        }
    )


@app.post("/api/cff/load")
async def load_cff_file(req: CFFLoadRequest):
    """
    Parses, cryptographically verifies, and interprets an uploaded .cff forensic case file.
    Renders nodes and wires on the whiteboard canvas with zero external API calls.
    """
    try:
        canvas, case, ml_intel, is_tamper_free, status_msg = CryptoForensicFileEngine.import_cff(req.cff_content)
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"Failed to parse .cff file: {str(ex)}")

    stats = canvas.summary_stats()
    elements = canvas.to_cytoscape_elements()

    actionable_cex_nodes = [n for n in canvas.nodes.values() if n.role == NodeRole.CEX_DEPOSIT]
    actionable_data = [
        {
            "address": n.address,
            "entity_tag": n.entity_tag or "Centralized Exchange",
            "stolen_held": n.stolen_amount_held,
            "taint_pct": round(n.stolen_taint_ratio * 100, 1),
            "paths": canvas.trace_paths_to_address(n.address)
        }
        for n in actionable_cex_nodes
    ]

    logs = [
        f"[CFF INTERPRETER] Loaded case container: {canvas.canvas_id}",
        f"[CRYPTOGRAPHIC AUDIT] {status_msg} (Section 63 BNSS)",
        f"[OFFLINE RECONSTRUCTION] Interpreted {len(canvas.nodes)} accounts across {len(canvas.wires)} transactions without network calls."
    ]

    return {
        "success": True,
        "is_cff_import": True,
        "is_tamper_free": is_tamper_free,
        "status_message": status_msg,
        "case_metadata": {
            "ack_number": case.ack_number,
            "fir_number": case.fir_number,
            "police_station": case.police_station,
            "investigating_officer": case.investigating_officer,
            "victim_name": case.victim_name,
            "loss_inr": case.loss_inr,
            "loss_crypto_str": case.loss_crypto_str,
            "crime_root_address": canvas.incident_root_address
        },
        "stats": stats,
        "elements": elements,
        "actionable_cex": actionable_data,
        "ml_intelligence": ml_intel,
        "logs": logs
    }


