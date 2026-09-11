/**
 * ==============================================================================
 * APP.JS - Tactical Forensic Workstation Main Orchestrator
 * ==============================================================================
 */

// Global Logger
window.logInfo = function(msg) { appendLog(msg, 'log-info'); };
window.logAlert = function(msg) { appendLog(msg, 'log-alert'); };
window.logSuccess = function(msg) { appendLog(msg, 'log-success'); };

function appendLog(msg, typeClass) {
    const time = new Date().toLocaleTimeString();
    
    // 1. Update mini bottom status bar text
    const statusText = document.getElementById('status-bar-text');
    if (statusText) {
        statusText.innerHTML = `<span style="color:var(--text-muted);">[${time}]</span> ${msg}`;
    }

    // 2. Append to expandable drawer
    const drawer = document.getElementById('log-drawer');
    if (!drawer) return;
    const entry = document.createElement('div');
    entry.className = `log-entry ${typeClass || ''}`;
    entry.innerHTML = `<span class="log-time">[${time}]</span> ${msg}`;
    drawer.appendChild(entry);
    drawer.scrollTop = drawer.scrollHeight;
}

// Preset Incident Profiles
const PRESET_CASES = {
    evm_ps_bench: {
        wallet: '0xwallet_s',
        chain: 'evm',
        amount: 50000,
        token: 'USDT',
        mode: 'benchmark',
        inr: 4250000,
        victim: ''
    },
    tron_1930_bench: {
        wallet: 'TScamSyndicate_Alpha_910283',
        chain: 'tron',
        amount: 50000,
        token: 'USDT',
        mode: 'benchmark',
        inr: 4250000,
        victim: ''
    },
    wazirx_live: {
        wallet: '0x04b21735E93Fa3f8df70e2Da89e6922616891a88',
        chain: 'evm',
        amount: 5000,
        token: 'ETH',
        mode: 'live',
        inr: 1250000000,
        victim: ''
    },
    tron_active_live: {
        wallet: 'TYDzsYUEpvnYmQk4zGP9sWWcTEd2MiAtW6',
        chain: 'tron',
        amount: 50000,
        token: 'USDT',
        mode: 'live',
        inr: 4250000,
        victim: ''
    },
    vitalik_live: {
        wallet: '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
        chain: 'evm',
        amount: 100,
        token: 'ETH',
        mode: 'live',
        inr: 25000000,
        victim: ''
    },
    custom: null
};

class ForensicApp {
    constructor() {
        this.graphController = new ForensicGraphController('cy');
        this.cffManager = new CFFManager();
        this.noticeManager = new StatutoryNoticeManager();
        this.lastTraceData = null;
        this.isTerminalExpanded = false;
    }

    init() {
        this.graphController.init();
        this.cffManager.init();
        this.noticeManager.init();
        this.setupTabNavigation();
        this.setupCallbacks();

        window.logInfo("Forensic Engine ready. Select a case preset or enter an incident wallet.");
        
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('simulate_running') === '1') {
            this.setExecutionStatus('Traversing hops on EVM...', 55, false, '● Traversing multi-hop transactions on EVM...');
            const traceBtn = document.getElementById('btn-trace');
            if (traceBtn) traceBtn.disabled = true;
            return;
        }

        // Auto-run initial case
        this.triggerTrace();
    }

    setupTabNavigation() {
        const tabs = document.querySelectorAll('.tab-btn');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

                tab.classList.add('active');
                const targetContent = document.getElementById(tab.dataset.tab);
                if (targetContent) targetContent.classList.add('active');
            });
        });
    }

    toggleInspector() {
        const drawer = document.getElementById('inspector-drawer');
        const edgeTab = document.getElementById('btn-open-inspector');
        if (drawer) {
            drawer.classList.toggle('collapsed');
            const isCollapsed = drawer.classList.contains('collapsed');
            if (edgeTab) edgeTab.style.display = isCollapsed ? 'inline-flex' : 'none';
            setTimeout(() => {
                if (this.graphController && this.graphController.cy) {
                    this.graphController.cy.resize();
                }
            }, 250);
        }
    }

    openInspector() {
        const drawer = document.getElementById('inspector-drawer');
        const edgeTab = document.getElementById('btn-open-inspector');
        if (drawer && drawer.classList.contains('collapsed')) {
            drawer.classList.remove('collapsed');
            if (edgeTab) edgeTab.style.display = 'none';
            setTimeout(() => {
                if (this.graphController && this.graphController.cy) {
                    this.graphController.cy.resize();
                }
            }, 250);
        }
    }

    toggleTerminal() {
        const drawer = document.getElementById('log-drawer');
        const chevron = document.getElementById('terminal-chevron');
        if (!drawer) return;
        
        this.isTerminalExpanded = !this.isTerminalExpanded;
        if (this.isTerminalExpanded) {
            drawer.classList.add('expanded');
            if (chevron) chevron.innerText = '▼';
        } else {
            drawer.classList.remove('expanded');
            if (chevron) chevron.innerText = '▲';
        }
    }

    toggleExecutionCard() {
        const dropdown = document.getElementById('widget-dropdown');
        const btn = document.getElementById('btn-widget-toggle');
        if (dropdown) {
            dropdown.classList.toggle('expanded');
            const isExp = dropdown.classList.contains('expanded');
            if (btn) btn.classList.toggle('expanded', isExp);
        }
    }

    setExecutionStatus(statusText, percent = 0, isComplete = false, milestoneItem = null) {
        const statusEl = document.getElementById('widget-status-text');
        const percentEl = document.getElementById('widget-percent');
        const spinnerEl = document.getElementById('widget-spinner');
        const barEl = document.getElementById('widget-progress-bar');
        const logList = document.getElementById('widget-log-list');

        if (statusEl && statusText) {
            statusEl.innerText = statusText;
        }

        // Rotating circle indicator placed right near the % age number
        if (spinnerEl) {
            if (percent > 0 && !isComplete) {
                spinnerEl.style.display = 'inline-block';
            } else {
                spinnerEl.style.display = 'none';
            }
        }

        if (percentEl) {
            if (percent > 0 && !isComplete) {
                percentEl.style.display = 'inline';
                percentEl.innerText = `${percent}%`;
            } else if (isComplete) {
                percentEl.style.display = 'inline';
                percentEl.innerText = '100%';
                setTimeout(() => {
                    if (percentEl) percentEl.style.display = 'none';
                }, 2000);
            } else {
                percentEl.style.display = 'none';
            }
        }

        if (barEl) {
            barEl.style.width = `${percent}%`;
            if (isComplete) {
                setTimeout(() => {
                    if (barEl) barEl.style.width = '0%';
                }, 1500);
            }
        }

        if (milestoneItem && logList) {
            const item = document.createElement('div');
            item.className = `widget-log-item ${isComplete ? 'success' : 'active'}`;
            item.innerText = milestoneItem;
            logList.appendChild(item);
            const dropdown = document.getElementById('widget-dropdown');
            if (dropdown) dropdown.scrollTop = dropdown.scrollHeight;
        }
    }

    // Modal Dialogs
    openIntakeModal() {
        const m = document.getElementById('intake-modal');
        if (m) m.style.display = 'flex';
    }

    closeIntakeModal() {
        const m = document.getElementById('intake-modal');
        if (m) m.style.display = 'none';
    }

    setupCallbacks() {
        // Node Selection Callback
        window.onNodeSelected = (nodeData) => {
            this.openInspector();
            this.activateTab('tab-node');

            document.getElementById('no-select-hint').style.display = 'none';
            document.getElementById('node-details').style.display = 'flex';

            document.getElementById('side-addr').innerText = nodeData.address || nodeData.id;
            
            // Role Badge styling
            const roleEl = document.getElementById('side-role');
            roleEl.innerText = nodeData.role || 'UNKNOWN';
            roleEl.className = 'badge';
            if (nodeData.role === 'SCAMMER') roleEl.classList.add('badge-crime');
            else if (nodeData.role === 'CEX_DEPOSIT') roleEl.classList.add('badge-cex');
            else if (nodeData.role === 'MULE_TRANSIT') roleEl.classList.add('badge-mule');
            else roleEl.classList.add('badge-subtle');

            document.getElementById('side-entity').innerText = nodeData.label || 'Unlabeled Account';
            
            const taintPct = nodeData.taint_pct !== undefined ? nodeData.taint_pct : 0;
            document.getElementById('side-taint').innerText = `${taintPct}%`;
            
            const taintFill = document.getElementById('side-taint-bar');
            if (taintFill) {
                taintFill.style.width = `${taintPct}%`;
                taintFill.style.background = taintPct > 50 ? 'var(--accent-crime)' : (taintPct > 20 ? 'var(--accent-mule)' : 'var(--accent-cex)');
            }

            document.getElementById('side-held').innerText = '$' + Number(nodeData.held_amount || 0).toLocaleString();
            document.getElementById('side-gas').innerText = (nodeData.gas_burned || 0) + ' Gas';

            // If CEX deposit, enable direct notice drafting
            const actionBox = document.getElementById('node-cex-action');
            if (nodeData.role === 'CEX_DEPOSIT') {
                actionBox.style.display = 'block';
                document.getElementById('btn-freeze-single').onclick = () => {
                    this.noticeManager.openModal(this.lastTraceData, nodeData.address);
                };
            } else {
                actionBox.style.display = 'none';
            }
        };

        // Edge Selection Callback
        window.onEdgeSelected = (edgeData) => {
            this.openInspector();
            this.activateTab('tab-node');

            document.getElementById('no-select-hint').style.display = 'none';
            document.getElementById('node-details').style.display = 'flex';

            document.getElementById('side-addr').innerText = edgeData.tx_hash || 'TX_HASH';
            
            const roleEl = document.getElementById('side-role');
            roleEl.innerText = 'TRANSACTION WIRE';
            roleEl.className = 'badge badge-subtle';

            document.getElementById('side-entity').innerText = `${edgeData.source.substring(0, 8)}... → ${edgeData.target.substring(0, 8)}...`;
            document.getElementById('side-taint').innerText = '100% Flow';
            
            const taintFill = document.getElementById('side-taint-bar');
            if (taintFill) {
                taintFill.style.width = '100%';
                taintFill.style.background = 'var(--accent-cyan)';
            }

            document.getElementById('side-held').innerText = edgeData.label || '';
            document.getElementById('side-gas').innerText = (edgeData.gas_fee || 0) + ' Gas Fee';
            document.getElementById('node-cex-action').style.display = 'none';
        };

        // Deselection Callback
        window.onCanvasDeselected = () => {
            document.getElementById('no-select-hint').style.display = 'block';
            document.getElementById('node-details').style.display = 'none';
            document.getElementById('node-cex-action').style.display = 'none';
        };

        // Case Loaded Callback (from .cff container)
        window.onCaseLoaded = (data) => {
            this.lastTraceData = data;
            data.logs.forEach(l => window.logInfo(l));

            // Update Seal Badge
            const sealBadge = document.getElementById('cff-seal-badge');
            sealBadge.style.display = 'inline-flex';
            if (data.is_tamper_free) {
                sealBadge.className = 'badge badge-seal';
                sealBadge.innerHTML = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> SEC 63 BNSS: VERIFIED';
            } else {
                sealBadge.className = 'badge badge-crime';
                sealBadge.innerHTML = 'TAMPER DETECTED: INVALID SEAL';
            }

            // Populate Form fields from metadata
            if (data.case_metadata) {
                if (data.case_metadata.fir_number) document.getElementById('fir-input').value = data.case_metadata.fir_number;
                if (data.case_metadata.ack_number) document.getElementById('ack-input').value = data.case_metadata.ack_number;
                if (data.case_metadata.loss_inr) document.getElementById('inr-input').value = data.case_metadata.loss_inr;
                if (data.case_metadata.crime_root_address) document.getElementById('wallet-input').value = data.case_metadata.crime_root_address;
            }

            this.updateHUD(data);
            this.updateMLCard(data.ml_intelligence);
            this.updateActionableList(data.actionable_cex);

            this.graphController.render(data.elements);
            this.setExecutionStatus('Offline Case Mounted', 100, true, `✓ Verified .cff container loaded with ${data.stats.total_accounts_tracked} accounts.`);
            window.logSuccess("Graph whiteboard reconstructed offline from .cff container.");
        };
    }

    activateTab(tabId) {
        document.querySelectorAll('.tab-btn').forEach(t => {
            if (t.dataset.tab === tabId) t.classList.add('active');
            else t.classList.remove('active');
        });
        document.querySelectorAll('.tab-content').forEach(c => {
            if (c.id === tabId) c.classList.add('active');
            else c.classList.remove('active');
        });
    }

    onCaseSelect(caseKey) {
        const c = PRESET_CASES[caseKey];
        if (!c) return;

        document.getElementById('wallet-input').value = c.wallet;
        document.getElementById('chain-select').value = c.chain;
        if (c.inr) document.getElementById('inr-input').value = c.inr;

        window.logInfo(`Loaded scenario: ${caseKey.toUpperCase()}`);
        this.triggerTrace();
    }

    async triggerTrace() {
        const wallet = document.getElementById('wallet-input').value.trim();
        const chain = document.getElementById('chain-select').value;
        const amount = 50000.0;
        const mode = "auto";
        const tokenSymbol = (chain === 'evm' && (wallet.startsWith('0x04b2') || wallet.startsWith('0xd8da'))) ? 'ETH' : 'USDT';

        const victim = document.getElementById('victim-input').value.trim();
        const fir = document.getElementById('fir-input').value.trim();
        const ack = document.getElementById('ack-input').value.trim();
        const inr = parseFloat(document.getElementById('inr-input').value) || (amount * 85.0);
        const dtVal = document.getElementById('datetime-input').value;
        const incTimestamp = dtVal ? Math.floor(new Date(dtVal).getTime() / 1000) : null;

        if (!wallet) {
            alert("Please enter a target wallet address.");
            return;
        }

        const traceBtn = document.getElementById('btn-trace');
        if (traceBtn) traceBtn.disabled = true;

        // Reset step logs for new trace
        const logList = document.getElementById('widget-log-list');
        if (logList) logList.innerHTML = '';

        this.setExecutionStatus('Validating node...', 25, false, `● Connecting to RPC node & validating ${wallet.substring(0, 10)}...`);
        window.logInfo(`[STEP 1/4] Connecting to network nodes & validating ${wallet.substring(0, 14)}...`);

        try {
            this.setExecutionStatus(`Traversing hops on ${chain.toUpperCase()}...`, 55, false, `● Traversing multi-hop transactions on ${chain.toUpperCase()}...`);
            window.logInfo(`[STEP 2/4] Traversing multi-hop transactions on ${chain.toUpperCase()}...`);

            const resp = await fetch('/api/trace', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet_address: wallet,
                    chain: chain,
                    stolen_amount: amount,
                    token_symbol: tokenSymbol,
                    mode: mode,
                    victim_address: victim || null,
                    incident_timestamp: incTimestamp,
                    fir_number: fir,
                    ack_number: ack,
                    loss_inr: inr
                })
            });

            this.setExecutionStatus('Analyzing off-ramps...', 80, false, `● Parsing transaction graph & identifying exchange off-ramps...`);
            window.logInfo(`[STEP 3/4] Parsing transaction graph & identifying exchange off-ramps...`);

            const data = await resp.json();
            if (!data.success) {
                alert("Trace Failed: " + (data.detail || "Unknown error"));
                if (traceBtn) traceBtn.disabled = false;
                this.setExecutionStatus('Trace Failed', 0, false, `✕ Error: ${data.detail || 'Unknown error'}`);
                return;
            }

            this.lastTraceData = data;
            data.logs.forEach(l => window.logInfo(l));

            // Update CFF Seal Badge (Compact)
            const sealBadge = document.getElementById('cff-seal-badge');
            if (data.cff_container && data.cff_container.cryptographic_seal) {
                sealBadge.style.display = 'inline-flex';
                sealBadge.className = 'badge badge-seal';
                sealBadge.innerHTML = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> SEC 63: ${data.cff_container.cryptographic_seal.integrity_hash.substring(0, 8)}`;
            }

            this.updateHUD(data);
            this.updateMLCard(data.ml_intelligence);
            this.updateActionableList(data.actionable_cex);

            window.logSuccess(`[STEP 4/4] Graph rendered: ${data.stats.total_accounts_tracked} wallets, ${data.stats.total_transactions_tracked} wires.`);
            this.graphController.render(data.elements);

            this.setExecutionStatus('Engine Ready (Active Graph)', 100, true, `✓ Rendered: ${data.stats.total_accounts_tracked} wallets, ${data.stats.total_transactions_tracked} wires.`);

        } catch (err) {
            window.logAlert(`Trace Error: ${err.message}`);
            this.setExecutionStatus('Trace Error', 0, false, `✕ Error: ${err.message}`);
        } finally {
            if (traceBtn) traceBtn.disabled = false;
        }
    }

    applyLayoutMode(layoutName) {
        ['dagre', 'tree', 'cluster'].forEach(k => {
            const el = document.getElementById(`btn-layout-${k}`);
            if (el) el.classList.remove('active');
        });
        const activeBtn = document.getElementById(`btn-layout-${layoutName}`);
        if (activeBtn) activeBtn.classList.add('active');

        if (this.graphController) {
            this.graphController.applyLayout(layoutName);
        }
    }

    updateHUD(data) {
        // Live / Benchmark Feed Indicator
        const srcEl = document.getElementById('hud-source');
        if (srcEl) {
            let dotColor = 'var(--accent-cyan)';
            let label = data.data_source || 'Benchmark Feed';
            if (data.is_cff_import) {
                dotColor = 'var(--accent-cex)';
                label = 'Offline .CFF Container';
            } else if (data.is_live) {
                dotColor = 'var(--accent-cex)';
            }
            srcEl.innerHTML = `<span class="chip-live-dot" style="background:${dotColor}; box-shadow:0 0 6px ${dotColor};"></span> ${label}`;
        }

        const accEl = document.getElementById('hud-accounts');
        if (accEl) accEl.innerText = data.stats.total_accounts_tracked;

        const wiresEl = document.getElementById('hud-wires');
        if (wiresEl) wiresEl.innerText = data.stats.total_transactions_tracked;

        const locEl = document.getElementById('hud-located');
        if (locEl) locEl.innerText = '$' + Number(data.stats.total_funds_at_exchanges).toLocaleString();

        const recEl = document.getElementById('hud-recovery');
        if (recEl) recEl.innerText = data.stats.recovery_potential_pct + '%';

        const sinksEl = document.getElementById('hud-sinks');
        if (sinksEl) sinksEl.innerText = data.actionable_cex.length;
    }

    updateMLCard(ml) {
        if (!ml) return;
        document.getElementById('ml-campaign').innerText = ml.campaign_name.replace(/_/g, " ");
        document.getElementById('ml-score').innerText = ml.overall_risk_score + ' / 100';
        
        const scoreBar = document.getElementById('ml-score-bar');
        if (scoreBar) {
            scoreBar.style.width = `${ml.overall_risk_score}%`;
            scoreBar.style.background = ml.overall_risk_score > 70 ? 'var(--accent-crime)' : (ml.overall_risk_score > 40 ? 'var(--accent-mule)' : 'var(--accent-cex)');
        }

        const prioEl = document.getElementById('ml-priority');
        prioEl.innerText = ml.investigation_priority;
        prioEl.className = 'badge';
        if (ml.investigation_priority === 'CRITICAL') prioEl.classList.add('badge-crime');
        else if (ml.investigation_priority === 'HIGH') prioEl.classList.add('badge-mule');
        else prioEl.classList.add('badge-cex');

        document.getElementById('ml-topo').innerText = ml.topological_fingerprint.replace(/_/g, " ");
        document.getElementById('ml-summary').innerText = ml.summary;
    }

    updateActionableList(actionableCexList) {
        const list = document.getElementById('actionable-list');
        list.innerHTML = '';

        if (!actionableCexList || actionableCexList.length === 0) {
            list.innerHTML = '<span style="font-size:11px; color:var(--text-muted);">No exchange cash-out endpoints identified yet.</span>';
            return;
        }

        actionableCexList.forEach(node => {
            const item = document.createElement('div');
            item.className = 'card';
            item.style.borderLeft = '3px solid var(--accent-cex)';
            item.innerHTML = `
                <div class="card-header">
                    <strong style="color:var(--accent-cex); font-size:12px;">${node.entity_tag}</strong>
                    <span class="badge badge-cex">${node.taint_pct}% Taint</span>
                </div>
                <div style="font-family:var(--font-mono); font-size:11px; color:var(--text-secondary); word-break:break-all;">${node.address}</div>
                <div class="field-row">
                    <span class="field-lbl">Stolen Held:</span>
                    <span class="field-val" style="color:var(--accent-cex);">$${Number(node.stolen_held).toLocaleString()} USDT</span>
                </div>
                <button class="btn btn-blue btn-sm" style="margin-top:4px;" onclick="window.app.noticeManager.openModal(window.app.lastTraceData, '${node.address}')">
                    Draft Sec 94 BNSS Notice
                </button>
            `;
            list.appendChild(item);
        });
    }
}

// Instantiate on DOM Ready
window.addEventListener('DOMContentLoaded', () => {
    window.app = new ForensicApp();
    window.app.init();
});
