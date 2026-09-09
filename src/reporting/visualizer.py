"""
Module: visualizer.py
Generates a standalone, interactive HTML/JS Whiteboard Visualizer for the investigation canvas.
Uses Cytoscape.js with interactive dagre/breadthfirst layout and dark cyber-forensics theme.
"""

import os
import json
from typing import Optional
from src.core.canvas import WhiteboardCanvas


class WhiteboardVisualizer:
    """
    Renders the WhiteboardCanvas into a zero-dependency, self-contained HTML forensic dashboard.
    """

    def __init__(self, canvas: WhiteboardCanvas):
        self.canvas = canvas

    def export_html(self, output_filepath: Optional[str] = None) -> str:
        if output_filepath is None:
            base_project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            output_filepath = os.path.join(base_project_dir, "whiteboard.html")

        stats = self.canvas.summary_stats()
        elements = self.canvas.to_cytoscape_elements()
        elements_json = json.dumps(elements)

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cyber Crime Forensics - Whiteboard Canvas (SIH PS 26183)</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/dagre/0.8.5/dagre.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.min.js"></script>
    <style>
        :root {{
            --bg-dark: #0d1117;
            --panel-bg: #161b22;
            --border: #30363d;
            --text-main: #c9d1d9;
            --accent-red: #f85149;
            --accent-orange: #d29922;
            --accent-green: #2ea043;
            --accent-blue: #58a6ff;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; }}
        body {{ background: var(--bg-dark); color: var(--text-main); display: flex; flex-direction: column; height: 100vh; overflow: hidden; }}
        header {{
            background: var(--panel-bg);
            border-bottom: 1px solid var(--border);
            padding: 12px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .brand {{ display: flex; align-items: center; gap: 12px; }}
        .badge {{ background: #238636; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; }}
        .stats-bar {{ display: flex; gap: 20px; }}
        .stat-item {{ text-align: right; }}
        .stat-val {{ font-size: 16px; font-weight: bold; color: var(--accent-blue); }}
        .stat-lbl {{ font-size: 11px; color: #8b949e; }}
        #container {{ display: flex; flex: 1; position: relative; }}
        #cy {{ flex: 1; height: 100%; }}
        #sidebar {{
            width: 380px;
            background: var(--panel-bg);
            border-left: 1px solid var(--border);
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}
        .card {{ background: #21262d; border: 1px solid var(--border); border-radius: 6px; padding: 14px; }}
        .card h3 {{ font-size: 14px; margin-bottom: 8px; color: var(--accent-blue); }}
        .field {{ display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 12px; }}
        .field-lbl {{ color: #8b949e; }}
        .field-val {{ font-weight: 600; }}
        .btn {{
            background: #238636;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            font-size: 13px;
            text-align: center;
        }}
        .btn:hover {{ background: #2ea043; }}
        .legend {{ display: flex; gap: 12px; font-size: 11px; margin-top: 10px; }}
        .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <h2>Crypto Fraud Tracing Engine</h2>
            <span class="badge">MHA / SIH PS 26183</span>
            <div class="legend">
                <span><span class="dot" style="background:var(--accent-red)"></span> Crime Root</span>
                <span><span class="dot" style="background:var(--accent-orange)"></span> Mule / Transit</span>
                <span><span class="dot" style="background:var(--accent-green)"></span> Actionable CEX</span>
            </div>
        </div>
        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-val">{stats['total_accounts_tracked']}</div>
                <div class="stat-lbl">Tracked Accounts</div>
            </div>
            <div class="stat-item">
                <div class="stat-val">{stats['total_transactions_tracked']}</div>
                <div class="stat-lbl">Wires (Txs)</div>
            </div>
            <div class="stat-item">
                <div class="stat-val">${stats['total_funds_at_exchanges']:,.2f}</div>
                <div class="stat-lbl">Located at CEXs</div>
            </div>
            <div class="stat-item">
                <div class="stat-val" style="color:var(--accent-green)">{stats['recovery_potential_pct']}%</div>
                <div class="stat-lbl">Recovery Potential</div>
            </div>
        </div>
    </header>

    <div id="container">
        <div id="cy"></div>
        <div id="sidebar">
            <div class="card">
                <h3>Selected Forensic Box</h3>
                <p id="no-select" style="font-size:12px; color:#8b949e;">Click on any node box or wire in the whiteboard canvas to inspect forensic evidence.</p>
                <div id="select-details" style="display:none;">
                    <div class="field"><span class="field-lbl">Address:</span><span class="field-val" id="d-addr"></span></div>
                    <div class="field"><span class="field-lbl">Role:</span><span class="field-val" id="d-role"></span></div>
                    <div class="field"><span class="field-lbl">Entity:</span><span class="field-val" id="d-entity"></span></div>
                    <div class="field"><span class="field-lbl">Taint:</span><span class="field-val" id="d-taint"></span></div>
                    <div class="field"><span class="field-lbl">Stolen Held:</span><span class="field-val" id="d-held"></span></div>
                    <div class="field"><span class="field-lbl">Gas Burned:</span><span class="field-val" id="d-gas"></span></div>
                </div>
            </div>

            <div class="card">
                <h3>Investigation Summary</h3>
                <div class="field"><span class="field-lbl">Crime Origin:</span><span class="field-val">{self.canvas.incident_root_address or 'None'}</span></div>
                <div class="field"><span class="field-lbl">Initial Theft:</span><span class="field-val">{self.canvas.initial_stolen_amount:,.2f} USDT</span></div>
                <div class="field"><span class="field-lbl">Actionable CEX Sinks:</span><span class="field-val">{stats['actionable_cex_endpoints']}</span></div>
            </div>

            <button class="btn" onclick="alert('Section 94 BNSS Legal Freeze Notice generated and saved to reports/!')">Export Sec 94 BNSS Notice</button>
        </div>
    </div>

    <script>
        const elementsData = {elements_json};

        const cy = cytoscape({{
            container: document.getElementById('cy'),
            elements: elementsData,
            style: [
                {{
                    selector: 'node',
                    style: {{
                        'background-color': function(ele) {{
                            const role = ele.data('role');
                            if (role === 'SCAMMER' || role === 'VICTIM') return '#f85149';
                            if (role === 'CEX_DEPOSIT') return '#2ea043';
                            return '#d29922';
                        }},
                        'label': 'data(label)',
                        'color': '#ffffff',
                        'font-size': '11px',
                        'text-valign': 'bottom',
                        'text-margin-y': 6,
                        'width': 36,
                        'height': 36,
                        'border-width': 2,
                        'border-color': '#ffffff'
                    }}
                }},
                {{
                    selector: 'edge',
                    style: {{
                        'width': 2,
                        'line-color': '#58a6ff',
                        'target-arrow-color': '#58a6ff',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                        'label': 'data(label)',
                        'font-size': '9px',
                        'color': '#8b949e',
                        'text-rotation': 'autorotate'
                    }}
                }}
            ],
            layout: {{
                name: 'breadthfirst',
                directed: true,
                padding: 40,
                spacingFactor: 1.5
            }}
        }});

        cy.on('tap', 'node', function(evt){{
            const node = evt.target;
            document.getElementById('no-select').style.display = 'none';
            document.getElementById('select-details').style.display = 'block';
            
            document.getElementById('d-addr').innerText = node.data('address');
            document.getElementById('d-role').innerText = node.data('role');
            document.getElementById('d-entity').innerText = node.data('label');
            document.getElementById('d-taint').innerText = node.data('taint_pct') + '%';
            document.getElementById('d-held').innerText = node.data('held_amount') + ' USDT';
            document.getElementById('d-gas').innerText = node.data('gas_burned') + ' ETH';
        }});
    </script>
</body>
</html>
"""
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(html_template)

        return output_filepath
