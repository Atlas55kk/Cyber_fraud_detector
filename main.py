"""
Main CLI entry point for the Crypto Fraud Tracing Engine (SIH PS 26183 - MHA).
Supports Multi-Chain Tracing:
1. Ethereum / EVM (ERC-20 USDT)
2. TRON (TRC-20 USDT - primary Indian cybercrime vector via 1930 / I4C)

Executes heuristic graph search, identifies exchange deposit off-ramps,
generates Section 94 BNSS / Section 91 CrPC notices, and creates the visual whiteboard.
"""

import sys
import os
import argparse
from src.core.canvas import WhiteboardCanvas
from src.core.taint_engine import TaintEngine, TaintModel
from src.core.wire_edge import ForensicWire, TokenType
from src.attribution.entity_resolver import EntityResolver
from src.algorithms.priority_search import PrioritySearchEngine, SearchConfig
from src.fetchers.mock_generator import MockFraudScenarioGenerator
from src.fetchers.tron_fetcher import TRON_USDT_CONTRACT
from src.reporting.dossier_generator import LegalDossierGenerator, CaseDetails
from src.reporting.visualizer import WhiteboardVisualizer


def trace_evm_case(entity_resolver: EntityResolver):
    print("\n" + "=" * 80)
    print("[CASE 1: ETHEREUM / EVM NETWORK - 50,000 ERC-20 USDT THEFT]")
    print("=" * 80)

    canvas = WhiteboardCanvas(canvas_id="EVM_Case_Live")
    taint_engine = TaintEngine(model=TaintModel.HAIRCUT, min_taint_threshold=0.02)
    search_engine = PrioritySearchEngine(canvas, taint_engine, entity_resolver)

    stolen_amount = 50000.0
    scam_wallet = "0xwallet_s"
    print(f"[*] Ingesting Victim Complaint (EVM):")
    print(f"    - Reported Scam Wallet: {scam_wallet}")
    print(f"    - Stolen Funds:         {stolen_amount:,.2f} USDT")

    canvas.set_incident_root(scam_wallet, stolen_amount, 1700000000)
    mock_graph = MockFraudScenarioGenerator.generate_problem_statement_case()

    actionable_cex_nodes = search_engine.run_trace(lambda addr: mock_graph.get(addr.lower(), []))
    print(f"[+] EVM Trace Finished: Located {len(actionable_cex_nodes)} Actionable Exchange Sinks.")

    for i, node in enumerate(actionable_cex_nodes, 1):
        print(f"    [{i}] {node.entity_tag} ({node.address}) | Held: {node.stolen_amount_held:,.2f} USDT | Taint: {node.stolen_taint_ratio*100:.1f}%")

    # Generate Section 94 BNSS Notice
    dossier_gen = LegalDossierGenerator(canvas)
    case = CaseDetails(
        ack_number="NCRP/2026/881230",
        fir_number="FIR 109/2026 (Cyber Crime PS)",
        investigating_officer="Inspector R. K. Sharma",
        victim_name="Shri Rajesh Kumar",
        loss_inr=4250000.0,
        loss_crypto_str="50,000 USDT (EVM)"
    )
    os.makedirs("reports", exist_ok=True)
    binance_node = actionable_cex_nodes[0]
    binance_entity = entity_resolver.resolve(binance_node.address)
    notice = dossier_gen.generate_section_94_bnss_notice(case, binance_node, binance_entity)
    with open("reports/SECTION_94_BNSS_EVM_NOTICE.txt", "w", encoding="utf-8") as f:
        f.write(notice)
    print(f"[+] Saved Police Requisition Notice: reports/SECTION_94_BNSS_EVM_NOTICE.txt")

    # Generate Whiteboard
    visualizer = WhiteboardVisualizer(canvas)
    visualizer.export_html("whiteboard_evm.html")
    print(f"[+] Saved EVM Interactive Whiteboard: whiteboard_evm.html")
    return canvas


def trace_tron_case(entity_resolver: EntityResolver):
    print("\n" + "=" * 80)
    print("[CASE 2: TRON NETWORK - 50,000 TRC-20 USDT THEFT (PRIMARY INDIAN FRAUD VECTOR)]")
    print("=" * 80)

    canvas = WhiteboardCanvas(canvas_id="TRON_Case_Live")
    taint_engine = TaintEngine(model=TaintModel.HAIRCUT, min_taint_threshold=0.02)
    search_engine = PrioritySearchEngine(canvas, taint_engine, entity_resolver)

    stolen_amount = 50000.0
    scam_wallet = "TScamSyndicate_Alpha_910283"
    mule_hop_1 = "TMuleTransit_Beta_481029"
    mule_hop_2 = "TMuleTransit_Gamma_771928"
    binance_tron_hot = "TPY9W8PnmgCJnUqUrYJ7p4G93F6r8eH1e6" # Binance TRON Hot Wallet
    coindcx_tron_hot = "TYDzsYUEpvnYmQk4zGP9sWWcTEd2MiAtW6" # CoinDCX TRON Hot Wallet

    print(f"[*] Ingesting Victim Complaint (TRON):")
    print(f"    - Reported Scam Wallet: {scam_wallet}")
    print(f"    - Stolen Funds:         {stolen_amount:,.2f} TRC-20 USDT")

    canvas.set_incident_root(scam_wallet, stolen_amount, 1700000000)

    # TRON Money Flow Topology:
    # ScamWallet -> Mule 1 (30k) & Mule 2 (20k)
    # Mule 1 -> Binance TRON Hot Wallet (30k USDT Cash-out)
    # Mule 2 -> CoinDCX TRON Hot Wallet (20k USDT Cash-out)
    tron_graph = {
        scam_wallet.lower(): [
            ForensicWire("0xtx_trc_1", scam_wallet, mule_hop_1, 30000.0, token_symbol="USDT", token_type=TokenType.TRC20, gas_fee=13.5, timestamp=1700000100),
            ForensicWire("0xtx_trc_2", scam_wallet, mule_hop_2, 20000.0, token_symbol="USDT", token_type=TokenType.TRC20, gas_fee=13.5, timestamp=1700000120),
        ],
        mule_hop_1.lower(): [
            ForensicWire("0xtx_trc_3", mule_hop_1, binance_tron_hot, 30000.0, token_symbol="USDT", token_type=TokenType.TRC20, gas_fee=13.5, timestamp=1700000300)
        ],
        mule_hop_2.lower(): [
            ForensicWire("0xtx_trc_4", mule_hop_2, coindcx_tron_hot, 20000.0, token_symbol="USDT", token_type=TokenType.TRC20, gas_fee=13.5, timestamp=1700000400)
        ]
    }

    actionable_cex_nodes = search_engine.run_trace(lambda addr: tron_graph.get(addr.lower(), []))
    print(f"[+] TRON Trace Finished: Located {len(actionable_cex_nodes)} Actionable Exchange Sinks.")

    for i, node in enumerate(actionable_cex_nodes, 1):
        print(f"    [{i}] {node.entity_tag} ({node.address}) | Held: {node.stolen_amount_held:,.2f} TRC-20 USDT | Taint: {node.stolen_taint_ratio*100:.1f}%")

    # Generate Section 94 BNSS Notice for TRON
    dossier_gen = LegalDossierGenerator(canvas)
    case = CaseDetails(
        ack_number="NCRP/2026/994102",
        fir_number="FIR 114/2026 (Cyber Crime PS)",
        investigating_officer="Inspector R. K. Sharma",
        victim_name="Smt. Sunita Verma",
        loss_inr=4250000.0,
        loss_crypto_str="50,000 TRC-20 USDT (TRON)"
    )
    binance_node = [n for n in actionable_cex_nodes if "binance" in (n.entity_tag or "").lower()][0]
    binance_entity = entity_resolver.resolve(binance_node.address)
    notice = dossier_gen.generate_section_94_bnss_notice(case, binance_node, binance_entity)
    with open("reports/SECTION_94_BNSS_TRON_NOTICE.txt", "w", encoding="utf-8") as f:
        f.write(notice)
    print(f"[+] Saved Police Requisition Notice: reports/SECTION_94_BNSS_TRON_NOTICE.txt")

    # Generate Whiteboard
    visualizer = WhiteboardVisualizer(canvas)
    visualizer.export_html("whiteboard_tron.html")
    # Also save as default whiteboard.html
    visualizer.export_html("whiteboard.html")
    print(f"[+] Saved TRON Interactive Whiteboard: whiteboard.html")
    return canvas


def main():
    parser = argparse.ArgumentParser(description="Multi-Chain Crypto Fraud Tracing Engine (MHA / SIH PS 26183)")
    parser.add_argument("--chain", choices=["evm", "tron", "both"], default="both", help="Blockchain network to trace (default: both)")
    args = parser.parse_args()

    print("=" * 80)
    print("SMART INDIA HACKATHON (SIH) - PS 26183: CRYPTO WALLET FRAUD TRACING")
    print("Ministry of Home Affairs (MHA) / I4C Cyber Crime Multi-Chain Forensics")
    print("=" * 80)

    entity_resolver = EntityResolver()

    if args.chain in ["evm", "both"]:
        trace_evm_case(entity_resolver)

    if args.chain in ["tron", "both"]:
        trace_tron_case(entity_resolver)

    print("\n" + "=" * 80)
    print("[SUCCESS] Multi-Chain Forensics Investigation Completed.")
    print("Actionable Requisitions: reports/SECTION_94_BNSS_*.txt")
    print("Interactive Whiteboards: whiteboard.html, whiteboard_evm.html, whiteboard_tron.html")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
