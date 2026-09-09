"""
Main CLI entry point for the Crypto Fraud Tracing Engine (SIH PS 26183 - MHA).
Executes heuristic graph search, identifies exchange deposit off-ramps,
generates Section 94 BNSS / Section 91 CrPC notices, and creates the visual whiteboard.
"""

import sys
import os
import argparse
from src.core.canvas import WhiteboardCanvas
from src.core.taint_engine import TaintEngine, TaintModel
from src.attribution.entity_resolver import EntityResolver
from src.algorithms.priority_search import PrioritySearchEngine, SearchConfig
from src.fetchers.mock_generator import MockFraudScenarioGenerator
from src.reporting.dossier_generator import LegalDossierGenerator, CaseDetails
from src.reporting.visualizer import WhiteboardVisualizer


def run_investigation_demo():
    print("=" * 80)
    print("SMART INDIA HACKATHON (SIH) - PS 26183: CRYPTO WALLET FRAUD TRACING")
    print("Ministry of Home Affairs (MHA) / I4C Cyber Crime Investigation Engine")
    print("=" * 80)

    # 1. Initialize Core Engine
    canvas = WhiteboardCanvas(canvas_id="MHA_Case_2026_Live")
    taint_engine = TaintEngine(model=TaintModel.HAIRCUT, min_taint_threshold=0.02)
    entity_resolver = EntityResolver()
    search_engine = PrioritySearchEngine(canvas, taint_engine, entity_resolver)

    # 2. Register Scam Wallet from Victim Complaint
    stolen_amount = 50000.0 # 50,000 USDT
    scam_wallet = "0xwallet_s"
    print(f"\n[*] INGESTING VICTIM COMPLAINT:")
    print(f"    - Reported Scam Wallet: {scam_wallet}")
    print(f"    - Total Stolen Assets:  {stolen_amount:,.2f} USDT")

    canvas.set_incident_root(
        address=scam_wallet,
        stolen_amount=stolen_amount,
        timestamp=1700000000
    )

    # 3. Load Money Flow Graph
    print(f"[*] Executing Heuristic-Guided Best-First Search (H-BFSTP)...")
    mock_graph = MockFraudScenarioGenerator.generate_problem_statement_case()

    def fetcher(addr: str):
        return mock_graph.get(addr.lower(), [])

    # 4. Run Search
    actionable_cex_nodes = search_engine.run_trace(fetcher)

    print(f"\n[+] TRACE COMPLETED SUCCESSFULLY!")
    print(f"    - Accounts Analyzed: {len(canvas.nodes)}")
    print(f"    - Transaction Wires: {len(canvas.wires)}")
    print(f"    - Actionable Exchange Off-Ramps Found: {len(actionable_cex_nodes)}")

    for i, cex_node in enumerate(actionable_cex_nodes, 1):
        print(f"\n    [{i}] TARGET OFF-RAMP: {cex_node.entity_tag}")
        print(f"        Deposit Address: {cex_node.address}")
        print(f"        Stolen Value Held: {cex_node.stolen_amount_held:,.2f} USDT")
        print(f"        Taint Proportion:  {cex_node.stolen_taint_ratio * 100:.1f}%")

        # Trace paths
        paths = canvas.trace_paths_to_address(cex_node.address)
        if paths:
            print(f"        Deterministic Chain of Custody:")
            for step_num, tx_h in enumerate(paths[0], 1):
                w = canvas.wires[tx_h]
                print(f"          Step {step_num}: {w.from_address} -> {w.to_address} ({w.value:,.2f} {w.token_symbol}) [Tx: {w.tx_hash}]")

    stats = canvas.summary_stats()
    print("\n" + "-" * 80)
    print(f"INVESTIGATION EXECUTIVE SUMMARY:")
    print(f"  • Total Stolen:             ${stats['initial_stolen_amount']:,.2f}")
    print(f"  • Located at Exchanges:     ${stats['total_funds_at_exchanges']:,.2f}")
    print(f"  • Actionable Recovery Rate:  {stats['recovery_potential_pct']}%")
    print(f"  • Total Network Gas Burned: {stats['total_network_gas_burned']} ETH")
    print("-" * 80)

    # 5. Generate Legal Notice
    dossier_gen = LegalDossierGenerator(canvas)
    case = CaseDetails(
        ack_number="NCRP/2026/881230",
        fir_number="FIR 109/2026 (Cyber Crime PS)",
        investigating_officer="Inspector R. K. Sharma",
        victim_name="Shri Rajesh Kumar",
        loss_inr=4250000.0,
        loss_crypto_str="50,000 USDT"
    )

    binance_node = actionable_cex_nodes[0]
    binance_entity = entity_resolver.resolve(binance_node.address)
    notice_text = dossier_gen.generate_section_94_bnss_notice(case, binance_node, binance_entity)

    os.makedirs("reports", exist_ok=True)
    notice_file = "reports/SECTION_94_BNSS_FREEZE_NOTICE_BINANCE.txt"
    with open(notice_file, "w", encoding="utf-8") as f:
        f.write(notice_text)
    print(f"\n[+] Generated Police Freeze Notice: {notice_file}")

    # 6. Generate Whiteboard HTML
    visualizer = WhiteboardVisualizer(canvas)
    html_file = visualizer.export_html("whiteboard.html")
    print(f"[+] Generated Interactive Whiteboard: {html_file}")
    print(f"    (Open 'whiteboard.html' in your browser to interact with the graph!)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_investigation_demo()
