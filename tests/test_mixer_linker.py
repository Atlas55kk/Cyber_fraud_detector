"""
Unit tests for the Privacy Mixer De-Anonymization Linker (Cristodaro et al. 2025).
"""

import unittest
from src.core.canvas import WhiteboardCanvas
from src.core.node_box import NodeRole
from src.core.wire_edge import ForensicWire, TokenType
from src.algorithms.mixer_linker import (
    MixerLinker,
    MixerDeposit,
    MixerWithdrawal,
    MixerLinkage
)


class TestMixerLinker(unittest.TestCase):

    def setUp(self):
        self.canvas = WhiteboardCanvas(canvas_id="Mixer_Test_Canvas")
        self.mixer_linker = MixerLinker(max_time_window_hours=48.0, min_linkage_confidence=0.40)
        self.tornado_10eth_pool = "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf"

    def test_direct_address_reuse_heuristic(self):
        # Depositor deposits into 10 ETH pool, then withdraws to same address
        deposit = MixerDeposit(
            tx_hash="0xdep_tx_1",
            depositor_address="0xScammerAddressAlpha",
            pool_address=self.tornado_10eth_pool,
            pool_name="Tornado 10 ETH",
            denomination=10.0,
            timestamp=1700000000
        )
        withdrawal = MixerWithdrawal(
            tx_hash="0xwith_tx_1",
            recipient_address="0xScammerAddressAlpha", # Address reuse!
            pool_address=self.tornado_10eth_pool,
            denomination=10.0,
            timestamp=1700003600
        )

        links = self.mixer_linker.find_linked_withdrawals(deposit, [withdrawal])
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].confidence_score, 1.0)
        self.assertIn("DIRECT_ADDRESS_REUSE", links[0].heuristic_reasons[0])

    def test_gas_sponsor_heuristic(self):
        # Fresh withdrawal address funded by depositor for gas
        deposit = MixerDeposit(
            tx_hash="0xdep_tx_2",
            depositor_address="0xScammerAddressBeta",
            pool_address=self.tornado_10eth_pool,
            pool_name="Tornado 10 ETH",
            denomination=10.0,
            timestamp=1700000000
        )
        withdrawal = MixerWithdrawal(
            tx_hash="0xwith_tx_2",
            recipient_address="0xFreshWithdrawalWallet99",
            pool_address=self.tornado_10eth_pool,
            denomination=10.0,
            timestamp=1700007200,
            gas_funder_address="0xScammerAddressBeta" # Sponsored by depositor!
        )

        links = self.mixer_linker.find_linked_withdrawals(deposit, [withdrawal])
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].confidence_score, 0.98)
        self.assertIn("GAS_SPONSOR_LINK", links[0].heuristic_reasons[0])

    def test_fifo_temporal_matching(self):
        # Depositor deposits into 10 ETH pool.
        # Exactly 1 withdrawal happens 30 minutes later with ZERO intervening deposits.
        deposit = MixerDeposit(
            tx_hash="0xdep_tx_3",
            depositor_address="0xScammerAddressGamma",
            pool_address=self.tornado_10eth_pool,
            pool_name="Tornado 10 ETH",
            denomination=10.0,
            timestamp=1700000000
        )
        withdrawal = MixerWithdrawal(
            tx_hash="0xwith_tx_3",
            recipient_address="0xUnknownRecipientWallet11",
            pool_address=self.tornado_10eth_pool,
            denomination=10.0,
            timestamp=1700001800 # 30 mins later
        )

        links = self.mixer_linker.find_linked_withdrawals(deposit, [withdrawal], pool_all_deposits=[deposit])
        self.assertEqual(len(links), 1)
        self.assertGreater(links[0].confidence_score, 0.85)
        self.assertIn("FIFO_TEMPORAL_QUEUE", links[0].heuristic_reasons[0])

    def test_bridge_mixer_on_canvas(self):
        deposit = MixerDeposit(
            tx_hash="0xdep_tx_canvas",
            depositor_address="0xScamOrigin",
            pool_address=self.tornado_10eth_pool,
            pool_name="Tornado 10 ETH",
            denomination=10.0,
            timestamp=1700000000
        )
        withdrawal = MixerWithdrawal(
            tx_hash="0xwith_tx_canvas",
            recipient_address="0xLinkedTarget",
            pool_address=self.tornado_10eth_pool,
            denomination=10.0,
            timestamp=1700003600
        )

        link = MixerLinkage(
            deposit=deposit,
            withdrawal=withdrawal,
            confidence_score=0.92,
            heuristic_reasons=["FIFO_TEMPORAL_QUEUE: 0 intervening deposits"],
            intervening_deposits_count=0,
            time_delta_seconds=3600
        )

        dep_wire = self.canvas.add_wire("0xorig_wire", "0xScamOrigin", self.tornado_10eth_pool, 10.0)
        reconnected_wire = self.mixer_linker.bridge_mixer_on_canvas(self.canvas, dep_wire, link)

        self.assertIn(reconnected_wire.tx_hash, self.canvas.wires)
        linked_node = self.canvas.nodes["0xlinkedtarget"]
        self.assertEqual(linked_node.address, "0xlinkedtarget")
        self.assertAlmostEqual(linked_node.stolen_amount_held, 9.2, delta=0.01) # 10.0 * 0.92


if __name__ == "__main__":
    unittest.main()
