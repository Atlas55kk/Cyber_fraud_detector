from fastapi.testclient import TestClient
from src.web.app import app
import json
import os

client = TestClient(app)

cases = {
    'evm_ps_bench': {'wallet_address': '0xwallet_s', 'chain': 'evm', 'stolen_amount': 50000, 'token_symbol': 'USDT', 'mode': 'benchmark'},
    'tron_1930_bench': {'wallet_address': 'TScamSyndicate_Alpha_910283', 'chain': 'tron', 'stolen_amount': 50000, 'token_symbol': 'USDT', 'mode': 'benchmark'},
    'wazirx_live': {'wallet_address': '0x04b21735E93Fa3f8df70e2Da89e6922616891a88', 'chain': 'evm', 'stolen_amount': 5000, 'token_symbol': 'ETH', 'mode': 'benchmark'},
    'tron_active_live': {'wallet_address': 'TYDzsYUEpvnYmQk4zGP9sWWcTEd2MiAtW6', 'chain': 'tron', 'stolen_amount': 50000, 'token_symbol': 'USDT', 'mode': 'benchmark'},
    'vitalik_live': {'wallet_address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045', 'chain': 'evm', 'stolen_amount': 100, 'token_symbol': 'ETH', 'mode': 'benchmark'}
}

results = {}
for p, req in cases.items():
    resp = client.post('/api/trace', json=req)
    if resp.status_code == 200:
        data = resp.json()
        results[p] = data
        n_elements = len(data.get('elements', []))
        nodes = [el for el in data.get('elements', []) if el.get('group') == 'nodes']
        edges = [el for el in data.get('elements', []) if el.get('group') == 'edges']
        print(f'{p}: {len(nodes)} nodes, {len(edges)} wires, total {n_elements} elements')
    else:
        print(f'Error on {p}: {resp.status_code}')

out_path = os.path.join('src', 'web', 'static', 'js', 'standalone_presets.js')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('// Auto-generated standalone presets data for GitHub Pages\n')
    f.write('window.STANDALONE_PRESETS = ' + json.dumps(results) + ';\n')

print('Export complete:', out_path)
