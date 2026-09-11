/**
 * ==============================================================================
 * NOTICE_MANAGER.JS - Section 94 BNSS Statutory Notice & PDF Dispatch Controller
 * ==============================================================================
 */

class StatutoryNoticeManager {
    constructor() {
        this.modal = null;
        this.bodyEl = null;
        this.titleEl = null;
        this.isOfficialDispatch = false;
    }

    init() {
        this.modal = document.getElementById('notice-modal');
        this.bodyEl = document.getElementById('notice-body');
        this.titleEl = document.getElementById('modal-title');
    }

    onToggleDispatch(isOfficial) {
        this.isOfficialDispatch = isOfficial;
        const badge = document.getElementById('dispatch-status-badge');
        const btn = document.getElementById('btn-generate-notice');
        const title = document.getElementById('notice-card-title');
        const desc = document.getElementById('notice-card-desc');

        if (isOfficial) {
            badge.innerHTML = '🚨 OFFICIAL DISPATCH MODE';
            badge.style.color = '#38bdf8';
            title.innerText = 'Statutory Notice Dispatch';
            title.style.color = '#38bdf8';
            desc.innerText = 'Official mode active. Generates Section 94 BNSS requisition for submission to exchange nodal officers.';
            btn.innerText = '📄 Draft Official Section 94 Notice';
            btn.className = 'btn btn-action';
            window.logAlert('[MODE] Official Dispatch Mode activated. Notice unlocked for formal service.');
        } else {
            badge.innerHTML = '🧪 PRACTICE MODE (Sandbox)';
            badge.style.color = '#e3b341';
            title.innerText = '🧪 Practice Mode: Forensic Reasoning';
            title.style.color = '#e3b341';
            desc.innerText = 'Practice sandbox active. Notice compiles mathematical reasoning and dry-run drafts without live statutory dispatch.';
            btn.innerText = '🧪 Preview Simulated Notice (Practice)';
            btn.className = 'btn btn-subtle';
            btn.style.color = '#e3b341';
            window.logInfo('[MODE] Practice Sandbox active. Safe simulation enabled — no real service.');
        }
    }

    async openModal(lastTraceData, targetAddressOverride) {
        if (!lastTraceData || lastTraceData.actionable_cex.length === 0) {
            alert("Please execute a trace that locates an exchange off-ramp target first!");
            return;
        }

        const targetAddr = targetAddressOverride || lastTraceData.actionable_cex[0].address;
        
        if (this.titleEl) {
            this.titleEl.innerText = this.isOfficialDispatch ?
                "OFFICIAL LEGAL REQUISITION (SECTION 94 BNSS / 91 CrPC)" :
                "SIMULATED FORENSIC DRAFT (PRACTICE SANDBOX)";
            this.titleEl.style.color = this.isOfficialDispatch ? "#38bdf8" : "#e3b341";
        }

        if (this.modal) this.modal.style.display = 'flex';
        if (this.bodyEl) this.bodyEl.innerText = "Drafting statutory Section 94 BNSS requisition notice...";

        try {
            const resp = await fetch('/api/generate_notice', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    target_address: targetAddr,
                    practice_mode: !this.isOfficialDispatch
                })
            });

            const data = await resp.json();
            if (this.bodyEl) this.bodyEl.innerText = data.notice_text;
        } catch (err) {
            if (this.bodyEl) this.bodyEl.innerText = "Error generating requisition notice: " + err.message;
        }
    }

    closeModal() {
        if (this.modal) this.modal.style.display = 'none';
    }

    copyNotice() {
        if (this.bodyEl) {
            navigator.clipboard.writeText(this.bodyEl.innerText);
            alert("Section 94 BNSS Notice copied to clipboard!");
        }
    }

    async downloadPDF(lastTraceData, targetAddressOverride) {
        if (!lastTraceData || lastTraceData.actionable_cex.length === 0) {
            alert("Please execute a trace that locates an exchange off-ramp target first!");
            return;
        }

        const targetAddr = targetAddressOverride || lastTraceData.actionable_cex[0].address;
        window.logInfo('[PDF ENGINE] Compiling Section 94 BNSS Legal Requisition PDF...');

        try {
            const resp = await fetch('/api/download_notice_pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    target_address: targetAddr,
                    practice_mode: !this.isOfficialDispatch
                })
            });

            if (!resp.ok) throw new Error('PDF Generation failed on server.');
            const blob = await resp.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `Section_94_BNSS_Notice_${targetAddr.substring(0, 10)}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            window.logSuccess('[PDF DOWNLOAD] Downloaded Section 94 BNSS Notice (.PDF).');
        } catch (err) {
            alert("Error downloading notice PDF: " + err.message);
            window.logAlert(`[PDF ERROR] ${err.message}`);
        }
    }
}
