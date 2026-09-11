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
        this.isTracing = false;
        this.activeAbortController = null;
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
            this.isTracing = true;
            this.updateTraceButtonState(true);
            this.setExecutionStatus('Traversing hops on EVM...', 55, false, '● Traversing multi-hop transactions on EVM...');
            return;
        }

        if (urlParams.get('simulate_complete') === '1') {
            fetch('/api/trace', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet_address: '0xwallet_s',
                    chain: 'evm',
                    stolen_amount: 50000,
                    token_symbol: 'USDT',
                    mode: 'benchmark'
                })
            }).then(r => r.json()).then(data => {
                this.lastTraceData = data;
                this.updateHUD(data);
                this.updateMLCard(data.ml_intelligence);
                this.updateActionableList(data.actionable_cex);
                this.graphController.render(data.elements);
                const sealBadge = document.getElementById('cff-seal-badge');
                if (data.cff_container && data.cff_container.cryptographic_seal && sealBadge) {
                    sealBadge.style.display = 'inline-flex';
                    sealBadge.className = 'badge badge-seal';
                    sealBadge.innerHTML = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> SEC 63: ${data.cff_container.cryptographic_seal.integrity_hash.substring(0, 8)}`;
                }
                this.setExecutionStatus('Engine Ready (Active Graph)', 100, true, `✓ Rendered: ${data.stats.total_accounts_tracked} wallets, ${data.stats.total_transactions_tracked} wires.`);
            });
            return;
        }

        if (urlParams.get('case')) {
            const cKey = urlParams.get('case');
            const sel = document.getElementById('case-select');
            if (sel) sel.value = cKey;
            this.onCaseSelect(cKey);
        }

        if (urlParams.get('auto_trace') === '1') {
            this.triggerTrace();
            return;
        }

        this.setExecutionStatus('Engine Ready — Select Case & Click Trace', 0, false, '● System initialized. Ready to execute multi-hop trace.');
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
            if (!nodeData) return;
            this.openInspector();
            this.activateTab('tab-node');

            const hint = document.getElementById('no-select-hint');
            if (hint) hint.style.display = 'none';
            const details = document.getElementById('node-details');
            if (details) details.style.display = 'flex';

            const addrEl = document.getElementById('side-addr');
            if (addrEl) addrEl.innerText = nodeData.address || nodeData.id || '';
            
            // Role Badge styling
            const roleEl = document.getElementById('side-role');
            if (roleEl) {
                roleEl.innerText = nodeData.role || 'UNKNOWN';
                roleEl.className = 'badge';
                if (nodeData.role === 'SCAMMER') roleEl.classList.add('badge-crime');
                else if (nodeData.role === 'CEX_DEPOSIT') roleEl.classList.add('badge-cex');
                else if (nodeData.role === 'MULE_TRANSIT') roleEl.classList.add('badge-mule');
                else roleEl.classList.add('badge-subtle');
            }

            const entityEl = document.getElementById('side-entity');
            if (entityEl) entityEl.innerText = nodeData.label || 'Unlabeled Account';
            
            const taintPct = nodeData.taint_pct !== undefined ? nodeData.taint_pct : 0;
            const taintEl = document.getElementById('side-taint');
            if (taintEl) taintEl.innerText = `${taintPct}%`;
            
            const taintFill = document.getElementById('side-taint-bar');
            if (taintFill) {
                taintFill.style.width = `${taintPct}%`;
                taintFill.style.background = taintPct > 50 ? 'var(--accent-crime)' : (taintPct > 20 ? 'var(--accent-mule)' : 'var(--accent-cex)');
            }

            const heldEl = document.getElementById('side-held');
            if (heldEl) heldEl.innerText = '$' + Number(nodeData.held_amount || 0).toLocaleString();
            const gasEl = document.getElementById('side-gas');
            if (gasEl) gasEl.innerText = (nodeData.gas_burned || 0) + ' Gas';

            // If CEX deposit, enable direct notice drafting
            const actionBox = document.getElementById('node-cex-action');
            if (actionBox) {
                if (nodeData.role === 'CEX_DEPOSIT') {
                    actionBox.style.display = 'block';
                    const freezeBtn = document.getElementById('btn-freeze-single');
                    if (freezeBtn) {
                        freezeBtn.onclick = () => {
                            this.noticeManager.openModal(this.lastTraceData, nodeData.address);
                        };
                    }
                } else {
                    actionBox.style.display = 'none';
                }
            }
        };

        // Edge Selection Callback
        window.onEdgeSelected = (edgeData) => {
            if (!edgeData) return;
            this.openInspector();
            this.activateTab('tab-node');

            const hint = document.getElementById('no-select-hint');
            if (hint) hint.style.display = 'none';
            const details = document.getElementById('node-details');
            if (details) details.style.display = 'flex';

            const addrEl = document.getElementById('side-addr');
            if (addrEl) addrEl.innerText = edgeData.tx_hash || 'TX_HASH';
            
            const roleEl = document.getElementById('side-role');
            if (roleEl) {
                roleEl.innerText = 'TRANSACTION WIRE';
                roleEl.className = 'badge badge-subtle';
            }

            const entityEl = document.getElementById('side-entity');
            const s = edgeData.source ? edgeData.source.substring(0, 8) : 'unknown';
            const t = edgeData.target ? edgeData.target.substring(0, 8) : 'unknown';
            if (entityEl) entityEl.innerText = `${s}... → ${t}...`;
            
            const taintEl = document.getElementById('side-taint');
            if (taintEl) taintEl.innerText = '100% Flow';
            
            const taintFill = document.getElementById('side-taint-bar');
            if (taintFill) {
                taintFill.style.width = '100%';
                taintFill.style.background = 'var(--accent-cyan)';
            }

            const heldEl = document.getElementById('side-held');
            if (heldEl) heldEl.innerText = edgeData.label || '';
            const gasEl = document.getElementById('side-gas');
            if (gasEl) gasEl.innerText = (edgeData.gas_fee || 0) + ' Gas Fee';
            const actionBox = document.getElementById('node-cex-action');
            if (actionBox) actionBox.style.display = 'none';
        };

        // Deselection Callback
        window.onCanvasDeselected = () => {
            const hint = document.getElementById('no-select-hint');
            if (hint) hint.style.display = 'block';
            const details = document.getElementById('node-details');
            if (details) details.style.display = 'none';
            const actionBox = document.getElementById('node-cex-action');
            if (actionBox) actionBox.style.display = 'none';
        };

        // Case Loaded Callback (from .cff container)
        window.onCaseLoaded = (data) => {
            if (!data) return;
            this.lastTraceData = data;
            if (data.logs) data.logs.forEach(l => window.logInfo(l));

            // Update Seal Badge
            const sealBadge = document.getElementById('cff-seal-badge');
            if (sealBadge) {
                sealBadge.style.display = 'inline-flex';
                if (data.is_tamper_free) {
                    sealBadge.className = 'badge badge-seal';
                    sealBadge.innerHTML = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> SEC 63 BNSS: VERIFIED';
                } else {
                    sealBadge.className = 'badge badge-crime';
                    sealBadge.innerHTML = 'TAMPER DETECTED: INVALID SEAL';
                }
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

        window.logInfo(`Loaded preset parameters: ${caseKey.toUpperCase()}`);
        this.setExecutionStatus('Preset Loaded — Click Trace to Begin', 0, false, `● Scenario [${caseKey.toUpperCase()}] loaded. Configure parameters or click Trace.`);
    }

    handleTraceToggle() {
        if (this.isTracing) {
            this.stopTrace();
        } else {
            this.triggerTrace();
        }
    }

    stopTrace() {
        if (!this.isTracing) return;
        if (this.activeAbortController) {
            this.activeAbortController.abort();
            this.activeAbortController = null;
        }
        this.isTracing = false;
        this.updateTraceButtonState(false);
        this.setExecutionStatus('Trace Stopped by Operator', 0, false, '✕ Multi-hop trace halted by operator.');
        window.logAlert('[STOPPED] Trace process halted by operator.');
    }

    updateTraceButtonState(isRunning) {
        const btn = document.getElementById('btn-trace');
        const icon = document.getElementById('btn-trace-icon');
        const text = document.getElementById('btn-trace-text');
        if (!btn) return;

        if (isRunning) {
            btn.className = 'btn btn-stop btn-sm';
            btn.title = 'Halt active blockchain trace';
            if (icon) {
                icon.innerHTML = '<rect x="6" y="6" width="12" height="12" rx="1.5" fill="currentColor"></rect>';
            }
            if (text) text.innerText = 'Stop';
        } else {
            btn.className = 'btn btn-primary btn-sm';
            btn.title = 'Execute Multi-Hop Priority Trace';
            if (icon) {
                icon.innerHTML = '<circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>';
            }
            if (text) text.innerText = 'Trace';
        }
    }

    async triggerTrace() {
        if (this.isTracing) return;

        const wallet = document.getElementById('wallet-input').value.trim();
        const chain = document.getElementById('chain-select').value;
        const selectedCaseKey = document.getElementById('case-select') ? document.getElementById('case-select').value : null;
        const preset = selectedCaseKey ? PRESET_CASES[selectedCaseKey] : null;

        let amount = 50000.0;
        let mode = "auto";
        let tokenSymbol = (chain === 'evm' && (wallet.toLowerCase().startsWith('0x04b2') || wallet.toLowerCase().startsWith('0xd8da'))) ? 'ETH' : 'USDT';

        if (preset && preset.wallet && preset.wallet.toLowerCase() === wallet.toLowerCase()) {
            if (preset.amount) amount = preset.amount;
            if (preset.mode) mode = preset.mode;
            if (preset.token) tokenSymbol = preset.token;
        }

        const victim = document.getElementById('victim-input') ? document.getElementById('victim-input').value.trim() : '';
        const fir = document.getElementById('fir-input') ? document.getElementById('fir-input').value.trim() : '';
        const ack = document.getElementById('ack-input') ? document.getElementById('ack-input').value.trim() : '';
        const inrInput = document.getElementById('inr-input');
        const inr = (inrInput && parseFloat(inrInput.value)) ? parseFloat(inrInput.value) : (amount * 85.0);
        const dtInput = document.getElementById('datetime-input');
        const dtVal = dtInput ? dtInput.value : '';
        const incTimestamp = dtVal ? Math.floor(new Date(dtVal).getTime() / 1000) : null;

        if (!wallet) {
            alert("Please enter a target wallet address.");
            return;
        }

        this.isTracing = true;
        this.activeAbortController = new AbortController();
        this.updateTraceButtonState(true);

        // Reset canvas, HUD counters, and step logs for real-time progressive stream
        this.graphController.clearCanvas();
        const accEl = document.getElementById('hud-accounts');
        if (accEl) accEl.innerText = '0';
        const wiresEl = document.getElementById('hud-wires');
        if (wiresEl) wiresEl.innerText = '0';
        const locEl = document.getElementById('hud-located');
        if (locEl) locEl.innerText = '$0';
        const recEl = document.getElementById('hud-recovery');
        if (recEl) recEl.innerText = '0%';
        const sinksEl = document.getElementById('hud-sinks');
        if (sinksEl) sinksEl.innerText = '0';
        const sealBadge = document.getElementById('cff-seal-badge');
        if (sealBadge) sealBadge.style.display = 'none';

        const logList = document.getElementById('widget-log-list');
        if (logList) logList.innerHTML = '';

        this.setExecutionStatus('Connecting to RPC node...', 15, false, `● Connecting to RPC node & validating ${wallet.substring(0, 10)}...`);
        window.logInfo(`[STREAM] Connecting to network nodes & validating ${wallet.substring(0, 14)}...`);

        try {
            const resp = await fetch('/api/trace/stream', {
                method: 'POST',
                signal: this.activeAbortController.signal,
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

            if (!resp.ok) {
                const errText = await resp.text();
                throw new Error(`HTTP ${resp.status}: ${errText}`);
            }

            const reader = resp.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';
            let accountsCount = 0;
            let wiresCount = 0;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const parts = buffer.split('\n\n');
                buffer = parts.pop();

                for (const part of parts) {
                    if (!part.trim()) continue;
                    const lines = part.split('\n');
                    let eventType = 'message';
                    let dataStr = '';

                    for (const line of lines) {
                        if (line.startsWith('event:')) {
                            eventType = line.substring(6).trim();
                        } else if (line.startsWith('data:')) {
                            dataStr = line.substring(5).trim();
                        }
                    }

                    if (!dataStr) continue;

                    try {
                        const parsed = JSON.parse(dataStr);

                        if (eventType === 'progress') {
                            this.setExecutionStatus(parsed.message, parsed.percent || 0, false, '● ' + parsed.message);
                            if (parsed.message) window.logInfo(parsed.message);
                        } else if (eventType === 'node') {
                            this.graphController.addNodeProgressive(parsed);
                            accountsCount++;
                            if (accEl) accEl.innerText = accountsCount;
                        } else if (eventType === 'wire') {
                            this.graphController.addWireProgressive(parsed);
                            wiresCount++;
                            if (wiresEl) wiresEl.innerText = wiresCount;
                        } else if (eventType === 'complete') {
                            const data = parsed;
                            this.lastTraceData = data;
                            if (data.logs) {
                                data.logs.forEach(l => window.logInfo(l));
                            }
                            if (data.cff_container && data.cff_container.cryptographic_seal && sealBadge) {
                                sealBadge.style.display = 'inline-flex';
                                sealBadge.className = 'badge badge-seal';
                                sealBadge.innerHTML = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> SEC 63: ${data.cff_container.cryptographic_seal.integrity_hash.substring(0, 8)}`;
                            }
                            this.updateHUD(data);
                            this.updateMLCard(data.ml_intelligence);
                            this.updateActionableList(data.actionable_cex);
                            this.graphController.runIncrementalLayout(true);
                            window.logSuccess(`[COMPLETED] Stream complete: ${data.stats.total_accounts_tracked} wallets, ${data.stats.total_transactions_tracked} wires tracked.`);
                            this.setExecutionStatus('Engine Ready (Active Graph)', 100, true, `✓ Streaming complete: ${data.stats.total_accounts_tracked} wallets, ${data.stats.total_transactions_tracked} wires.`);
                        } else if (eventType === 'error') {
                            window.logAlert(`Trace Error: ${parsed.detail || 'Unknown stream error'}`);
                            this.setExecutionStatus('Trace Failed', 0, false, `✕ Error: ${parsed.detail || 'Unknown stream error'}`);
                        }
                    } catch (e) {
                        console.error('SSE parse error', e, dataStr);
                    }
                }
            }

        } catch (err) {
            if (err.name === 'AbortError') {
                this.graphController.runIncrementalLayout(false);
                return;
            }
            window.logAlert(`Trace Error: ${err.message}`);
            this.setExecutionStatus('Trace Error', 0, false, `✕ Error: ${err.message}`);
        } finally {
            this.isTracing = false;
            this.activeAbortController = null;
            this.updateTraceButtonState(false);
        }
    }

    applyLayoutMode(mode) {
        const layoutMapping = {
            'flow': 'dagre',
            'dagre': 'dagre',
            'tree': 'breadthfirst',
            'breadthfirst': 'breadthfirst',
            'cluster': 'cose',
            'cose': 'cose'
        };
        const idMapping = {
            'dagre': 'btn-layout-dagre',
            'breadthfirst': 'btn-layout-tree',
            'cose': 'btn-layout-cluster'
        };
        const engineLayout = layoutMapping[mode] || 'dagre';
        ['btn-layout-dagre', 'btn-layout-tree', 'btn-layout-cluster'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.classList.remove('active');
        });
        const activeId = idMapping[engineLayout];
        if (activeId) {
            const el = document.getElementById(activeId);
            if (el) el.classList.add('active');
        }

        if (this.graphController) {
            this.graphController.applyLayout(engineLayout);
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
