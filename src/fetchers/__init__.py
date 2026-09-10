"""
Fetchers package initialization.
"""
from src.fetchers.mock_generator import MockFraudScenarioGenerator
from src.fetchers.etherscan_fetcher import EtherscanFetcher
from src.fetchers.tron_fetcher import TronFetcher, TRON_USDT_CONTRACT

__all__ = [
    "MockFraudScenarioGenerator",
    "EtherscanFetcher",
    "TronFetcher",
    "TRON_USDT_CONTRACT"
]
