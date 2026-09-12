"""
Module: mock_generator.py
Generates realistic, deterministic multi-hop cyber fraud scenarios for offline testing,
reproducible benchmarking, and hackathon jury demonstrations without live API dependencies.
"""

import time
from typing import Dict, List
from src.core.wire_edge import ForensicWire, TokenType


class MockFraudScenarioGenerator:
    """
    Generates realistic multi-hop fraud graphs reflecting actual MHA / I4C case typologies.
    """

    @staticmethod
    def generate_problem_statement_case(
        root_address: str = "0xwallet_s",
        stolen_amount: float = 50000.0,
        token_symbol: str = "USDT"
    ) -> Dict[str, List[ForensicWire]]:
        """
        Reproduces the scenario described in the SIH problem statement,
        dynamically adapted to the provided root_address, amount, and token.
        """
        t0 = int(time.time()) - 3600 # 1 hour ago
        binance_hot = "0x28c6c06298d514db089934071355e5743bf21d60"
        coindcx_hot = "0x4a4754593444053896fa231b1e93c1ef7e068777"
        clean_root = root_address.lower().strip()
        factor = (stolen_amount / 50000.0) if stolen_amount > 0 else 1.0

        graph: Dict[str, List[ForensicWire]] = {
            clean_root: [
                ForensicWire("0xtx_s_b", clean_root, "0xwallet_b", 20000.0 * factor, token_symbol=token_symbol, gas_fee=0.002, timestamp=t0 + 60),
                ForensicWire("0xtx_s_c", clean_root, "0xwallet_c", 30000.0 * factor, token_symbol=token_symbol, gas_fee=0.002, timestamp=t0 + 120),
            ],
            "0xwallet_b": [
                ForensicWire("0xtx_b_d", "0xwallet_b", "0xwallet_d", 20000.0 * factor, token_symbol=token_symbol, gas_fee=0.002, timestamp=t0 + 300),
            ],
            "0xwallet_c": [
                ForensicWire("0xtx_c_e", "0xwallet_c", "0xwallet_e", 15000.0 * factor, token_symbol=token_symbol, gas_fee=0.002, timestamp=t0 + 400),
                ForensicWire("0xtx_c_f", "0xwallet_c", "0xwallet_f", 15000.0 * factor, token_symbol=token_symbol, gas_fee=0.002, timestamp=t0 + 450),
            ],
            "0xwallet_d": [
                ForensicWire("0xtx_d_binance", "0xwallet_d", binance_hot, 20000.0 * factor, token_symbol=token_symbol, gas_fee=0.002, timestamp=t0 + 600),
            ],
            "0xwallet_e": [
                ForensicWire("0xtx_e_h", "0xwallet_e", "0xwallet_h", 15000.0 * factor, token_symbol=token_symbol, gas_fee=0.002, timestamp=t0 + 700),
            ],
            "0xwallet_f": [
                ForensicWire("0xtx_f_coindcx", "0xwallet_f", coindcx_hot, 15000.0 * factor, token_symbol=token_symbol, gas_fee=0.002, timestamp=t0 + 800),
            ]
        }
        if clean_root != "0xwallet_s":
            graph["0xwallet_s"] = graph[clean_root]
        return graph

    @staticmethod
    def generate_wazirx_case(
        root_address: str = "0x04b21735e10034a7810793ab97cb56041692ae2a",
        stolen_amount: float = 5000.0,
        token_symbol: str = "ETH"
    ) -> Dict[str, List[ForensicWire]]:
        """
        Reproduces the July 2024 WazirX hack multi-hop fund displacement and peel-chain pattern.
        """
        t0 = int(time.time()) - 3600
        binance_hot = "0x28c6c06298d514db089934071355e5743bf21d60"
        coindcx_hot = "0x4a4754593444053896fa231b1e93c1ef7e068777"
        clean_root = root_address.lower().strip()
        factor = (stolen_amount / 5000.0) if stolen_amount > 0 else 1.0

        graph: Dict[str, List[ForensicWire]] = {
            clean_root: [
                ForensicWire("0xtx_s_b", clean_root, "0xwallet_b", 2000.0 * factor, token_symbol=token_symbol, gas_fee=0.002, timestamp=t0 + 60),
                ForensicWire("0xtx_s_c", clean_root, "0xwallet_c", 3000.0 * factor, token_symbol=token_symbol, gas_fee=0.002, timestamp=t0 + 120),
            ],
            "0xwallet_b": [
                ForensicWire("0xtx_b_d", "0xwallet_b", "0xwallet_d", 2000.0 * factor, token_symbol=token_symbol, gas_fee=0.002, timestamp=t0 + 300),
            ],
            "0xwallet_c": [
                ForensicWire("0xtx_c_e", "0xwallet_c", "0xwallet_e", 1500.0 * factor, token_symbol=token_symbol, gas_fee=0.002, timestamp=t0 + 400),
                ForensicWire("0xtx_c_f", "0xwallet_c", "0xwallet_f", 1500.0 * factor, token_symbol=token_symbol, gas_fee=0.002, timestamp=t0 + 450),
            ],
            "0xwallet_d": [
                ForensicWire("0xtx_d_binance", "0xwallet_d", binance_hot, 2000.0 * factor, token_symbol=token_symbol, gas_fee=0.002, timestamp=t0 + 600),
            ],
            "0xwallet_e": [
                ForensicWire("0xtx_e_h", "0xwallet_e", "0xwallet_h", 1500.0 * factor, token_symbol=token_symbol, gas_fee=0.002, timestamp=t0 + 700),
            ],
            "0xwallet_f": [
                ForensicWire("0xtx_f_coindcx", "0xwallet_f", coindcx_hot, 1500.0 * factor, token_symbol=token_symbol, gas_fee=0.002, timestamp=t0 + 800),
            ]
        }
        return graph

    @staticmethod
    def generate_large_peel_chain(hops: int = 5) -> Dict[str, List[ForensicWire]]:
        """
        Generates a 5-hop peel chain stripping 2,000 USDT at each step to an exchange
        and forwarding the rest to a fresh transit address.
        """
        t0 = int(time.time()) - 7200
        binance_hot = "0x28c6c06298d514db089934071355e5743bf21d60"
        graph: Dict[str, List[ForensicWire]] = {}

        current_balance = 50000.0
        curr_addr = "0xroot_scammer"

        for i in range(1, hops + 1):
            peel_amt = 2000.0
            forward_amt = current_balance - peel_amt
            next_transit = f"0xtransit_hop_{i}"

            graph[curr_addr] = [
                ForensicWire(f"0xpeel_tx_{i}", curr_addr, binance_hot, peel_amt, timestamp=t0 + (i * 300)),
                ForensicWire(f"0xfwd_tx_{i}", curr_addr, next_transit, forward_amt, timestamp=t0 + (i * 300))
            ]

            curr_addr = next_transit
            current_balance = forward_amt

        return graph
