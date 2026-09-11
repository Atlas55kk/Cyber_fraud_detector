/**
 * ==============================================================================
 * APP.JS - Tactical Forensic Workstation Main Orchestrator
 * ==============================================================================
 */

// Global Logging Engine
window.logInfo = function(msg) {
    appendLog(msg, 'log-info');
};

window.logAlert = function(msg) {
    appendLog(msg, 'log-alert');
};

window.logSuccess = function(msg) {
    appendLog(msg, 'log-success');
};

function appendLog(msg, typeClass) {
    const drawer = document.getElementById('log-drawer');
    if (!drawer) return;
    const time = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = `log-entry ${typeClass || ''}`;
    entry.innerHTML = `<span class="log-time">[${time}]</span> ${msg}`;
    drawer.appendChild(entry);
    drawer.scrollTop = drawer.scrollHeight;
}

// Preset Fraud Scenarios
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

// Application State
class ForensicApp {
    constructor() {
        this.graphController = new ForensicGraphController('cy');
        this.cffManager = new CFFManager();
        this.noticeManager = new StatutoryNoticeManager();
        this.lastTraceData = null;
    }

    init() {
        this.graphController.init();
        this.cffManager.init();
        this.noticeManager.init();
        this.setupTabNavigation();
        this.setupCallbacks();

        window.logInfo("[SYSTEM] Forensic Graph Engine initialized. Ready for investigation.");

        // Automatically run initial benchmark case
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

    setupCallbacks() {
        // Node Selection Callback
        window.onNodeSelected = (nodeData) => {
            // Switch to Inspector tab
            this.activateTab('tab-node');
            document.getElementById('no-select-hint').style.display = 'none';
            document.getElementById('node-details').style.display = 'flex';

            document.getElementById('side-addr').innerText = nodeData.address || nodeData.id;
            document.getElementById('side-role').innerText = nodeData.role || 'UNKNOWN';
            document.getElementById('side-entity').innerText = nodeData.label || 'Unlabeled EOA';
            document.getElementById('side-taint').innerText = (nodeData.taint_pct !== undefined ? nodeData.taint_pct : 0) + '%';
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
            this.activateTab('tab-node');
            document.getElementById('no-select-hint').style.display = 'none';
            document.getElementById('node-details').style.display = 'flex';

            document.getElementById('side-addr').innerText = edgeData.tx_hash || 'TX_HASH';
            document.getElementById('side-role').innerText = 'TRANSACTION WIRE';
            document.getElementById('side-entity').innerText = `${edgeData.source.substring(0, 8)}... ➔ ${edgeData.target.substring(0, 8)}...`;
            document.getElementById('side-taint').innerText = 'Direct Flow';
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

        // Case Loaded Callback (from .cff file)
        window.onCaseLoaded = (data) => {
            this.lastTraceData = data;
            data.logs.forEach(l => window.logInfo(l));

            // Update Seal Badge
            const sealBadge = document.getElementById('cff-seal-badge');
            sealBadge.style.display = 'inline-block';
            if (data.is_tamper_free) {
                sealBadge.className = 'badge badge-seal';
                sealBadge.innerHTML = '🛡️ SEC 63 BNSS SEAL: VERIFIED';
            } else {
                sealBadge.className = 'badge badge-alert';
                sealBadge.innerHTML = '⚠️ TAMPER DETECTED: INVALID SEAL';
            }

            // Populate Form fields from metadata
            if (data.case_metadata) {
                if (data.case_metadata.fir_number) document.getElementById('fir-input').value = data.case_metadata.fir_number;
                if (data.case_metadata.ack_number) document.getElementById('ack-input').value = data.case_metadata.ack_number;
                if (data.case_metadata.loss_inr) document.getElementById('inr-input').value = data.case_metadata.loss_inr;
                if (data.case_metadata.crime_root_address) document.getElementById('wallet-input').value = data.case_metadata.crime_root_address;
            }

            // Update KPIs & ML Cards
            this.updateKPIs(data);
            this.updateMLCard(data.ml_intelligence);
            this.updateActionableList(data.actionable_cex);

            // Render Canvas
            this.graphController.render(data.elements);
            window.logSuccess(`[CFF RECONSTRUCTION] Graph whiteboard reconstructed offline.`);
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
        document.getElementById('amount-input').value = c.amount;
        document.getElementById('mode-select').value = c.mode;
        if (c.inr) document.getElementById('inr-input').value = c.inr;

        window.logInfo(`[CASE PRESET] Loaded configuration: ${caseKey.toUpperCase()}`);
        this.triggerTrace();
    }

    async triggerTrace() {
        const wallet = document.getElementById('wallet-input').value.trim();
        const chain = document.getElementById('chain-select').value;
        const amount = parseFloat(document.getElementById('amount-input').value) || 50000.0;
        const mode = document.getElementById('mode-select').value;
        const tokenSymbol = (chain === 'evm' && wallet.startsWith('0x04b2')) ? 'ETH' : (chain === 'evm' && wallet.startsWith('0xd8da') ? 'ETH' : 'USDT');

        const victim = document.getElementById('victim-input').value.trim();
        const fir = document.getElementById('fir-input').value.trim();
        const ack = document.getElementById('ack-input').value.trim();
        const inr = parseFloat(document.getElementById('inr-input').value) || (amount * 85.0);
        const dtVal = document.getElementById('datetime-input').value;
        const incTimestamp = dtVal ? Math.floor(new Date(dtVal).getTime() / 1000) : null;

        if (!wallet) {
            alert("Please enter a wallet address.");
            return;
        }

        window.logInfo(`[TRACE INITIATED] Priority traversal for ${wallet.substring(0, 12)}... on ${chain.toUpperCase()}`);

        try {
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

            const data = await resp.json();
            if (!data.success) {
                alert("Trace Failed: " + (data.detail || "Unknown error"));
                return;
            }

            this.lastTraceData = data;
            data.logs.forEach(l => window.logInfo(l));

            // Update CFF Seal Badge
            const sealBadge = document.getElementById('cff-seal-badge');
            if (data.cff_container && data.cff_container.cryptographic_seal) {
                sealBadge.style.display = 'inline-block';
                sealBadge.className = 'badge badge-seal';
                sealBadge.innerHTML = `🛡️ SEC 63 BNSS SEAL: ${data.cff_container.cryptographic_seal.integrity_hash.substring(0, 8)}...`;
            }

            // Update KPIs & ML Cards
            this.updateKPIs(data);
            this.updateMLCard(data.ml_intelligence);
            this.updateActionableList(data.actionable_cex);

            // Render Cytoscape Canvas
            this.graphController.render(data.elements);

        } catch (err) {
            window.logAlert(`[TRACE ERROR] ${err.message}`);
        }
    }

    updateKPIs(data) {
        const srcEl = document.getElementById('kpi-source');
        if (data.is_cff_import) {
            srcEl.innerHTML = `<span style="color:#10b981; font-weight:bold;">📁 Standalone .CFF File (Offline)</span>`;
        } else if (data.is_live) {
            srcEl.innerHTML = `<span style="color:#10b981; font-weight:bold;">🟢 ${data.data_source}</span>`;
        } else {
            srcEl.innerHTML = `<span style="color:#a855f7; font-weight:bold;">🟣 ${data.data_source}</span>`;
        }

        document.getElementById('kpi-accounts').innerText = data.stats.total_accounts_tracked;
        document.getElementById('kpi-wires').innerText = data.stats.total_transactions_tracked;
        document.getElementById('kpi-located').innerText = '$' + Number(data.stats.total_funds_at_exchanges).toLocaleString();
        document.getElementById('kpi-recovery').innerText = data.stats.recovery_potential_pct + '%';
        document.getElementById('kpi-sinks').innerText = data.actionable_cex.length;
    }

    updateMLCard(ml) {
        if (!ml) return;
        document.getElementById('ml-campaign').innerText = ml.campaign_name.replace(/_/g, " ");
        document.getElementById('ml-score').innerText = ml.overall_risk_score + '/100';
        
        const prioEl = document.getElementById('ml-priority');
        prioEl.innerText = ml.investigation_priority;
        if (ml.investigation_priority === 'CRITICAL') prioEl.style.color = 'var(--accent-crime)';
        else if (ml.investigation_priority === 'HIGH') prioEl.style.color = 'var(--accent-mule)';
        else prioEl.style.color = 'var(--accent-cex)';

        document.getElementById('ml-topo').innerText = ml.topological_fingerprint.replace(/_/g, " ");
        document.getElementById('ml-summary').innerText = ml.summary;
    }

    updateActionableList(actionableCexList) {
        const list = document.getElementById('actionable-list');
        list.innerHTML = '';

        if (!actionableCexList || actionableCexList.length === 0) {
            list.innerHTML = '<span style="font-size:11px; color:var(--text-muted);">No centralized exchange endpoints identified yet.</span>';
            return;
        }

        actionableCexList.forEach(node => {
            const item = document.createElement('div');
            item.className = 'card';
            item.style.borderLeft = '3px solid var(--accent-cex)';
            item.innerHTML = `
                <div class="card-header">
                    <strong style="color:var(--accent-cex); font-size:12px;">${node.entity_tag}</strong>
                    <span class="badge badge-seal">${node.taint_pct}% Taint</span>
                </div>
                <div style="font-family:var(--font-mono); font-size:11px; color:var(--text-secondary);">${node.address.substring(0, 16)}...</div>
                <div class="field-row">
                    <span class="field-lbl">Stolen Held:</span>
                    <span class="field-val" style="color:var(--accent-cex);">$${Number(node.stolen_held).toLocaleString()} USDT</span>
                </div>
                <button class="btn btn-action" style="margin-top:6px; height:28px; font-size:11px;" onclick="window.app.noticeManager.openModal(window.app.lastTraceData, '${node.address}')">
                    ⚖️ Draft Sec 94 BNSS Order
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
