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
    def generate_problem_statement_case() -> Dict[str, List[ForensicWire]]:
        """
        Reproduces the exact scenario described in the SIH problem statement:
        
        Victim sends 50,000 USDT to Wallet S (Scammer)
        Wallet S sends:
          - 20,000 USDT to Wallet B
          - 30,000 USDT to Wallet C
        Wallet B sends:
          - 20,000 USDT to Wallet D
        Wallet C sends:
          - 15,000 USDT to Wallet E
          - 15,000 USDT to Wallet F
        Wallet D sends:
          - 20,000 USDT to Binance Deposit Address (Cash-out / Freeze target!)
        Wallet E sends:
          - 15,000 USDT to Wallet H
        Wallet F sends:
          - 15,000 USDT to CoinDCX Deposit Address (Cash-out / Freeze target!)
        """
        t0 = int(time.time()) - 3600 # 1 hour ago
        binance_hot = "0x28c6c06298d514db089934071355e5743bf21d60"
        coindcx_hot = "0x4a4754593444053896fa231b1e93c1ef7e068777"

        graph: Dict[str, List[ForensicWire]] = {
            "0xwallet_s": [
                ForensicWire("0xtx_s_b", "0xwallet_s", "0xwallet_b", 20000.0, gas_fee=0.002, timestamp=t0 + 60),
                ForensicWire("0xtx_s_c", "0xwallet_s", "0xwallet_c", 30000.0, gas_fee=0.002, timestamp=t0 + 120),
            ],
            "0xwallet_b": [
                ForensicWire("0xtx_b_d", "0xwallet_b", "0xwallet_d", 20000.0, gas_fee=0.002, timestamp=t0 + 300),
            ],
            "0xwallet_c": [
                ForensicWire("0xtx_c_e", "0xwallet_c", "0xwallet_e", 15000.0, gas_fee=0.002, timestamp=t0 + 400),
                ForensicWire("0xtx_c_f", "0xwallet_c", "0xwallet_f", 15000.0, gas_fee=0.002, timestamp=t0 + 450),
            ],
            "0xwallet_d": [
                ForensicWire("0xtx_d_binance", "0xwallet_d", binance_hot, 20000.0, gas_fee=0.002, timestamp=t0 + 600),
            ],
            "0xwallet_e": [
                ForensicWire("0xtx_e_h", "0xwallet_e", "0xwallet_h", 15000.0, gas_fee=0.002, timestamp=t0 + 700),
            ],
            "0xwallet_f": [
                ForensicWire("0xtx_f_coindcx", "0xwallet_f", coindcx_hot, 15000.0, gas_fee=0.002, timestamp=t0 + 800),
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
