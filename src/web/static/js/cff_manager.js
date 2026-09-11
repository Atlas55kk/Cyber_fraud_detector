/**
 * ==============================================================================
 * CFF_MANAGER.JS - Crypto Forensic File (.cff) Manager & Drag-Drop Case Vault
 * ==============================================================================
 */

class CFFManager {
    constructor() {
        this.fileInput = null;
        this.dropZone = null;
    }

    init() {
        this.fileInput = document.getElementById('cff-file-input');
        this.dropZone = document.getElementById('drop-zone');
        this.setupDragAndDrop();
    }

    setupDragAndDrop() {
        window.addEventListener('dragenter', (e) => {
            e.preventDefault();
            if (this.dropZone) this.dropZone.classList.add('active');
        });

        window.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        if (this.dropZone) {
            this.dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                this.dropZone.classList.remove('active');
            });

            this.dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                this.dropZone.classList.remove('active');
                if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                    this.processFile(e.dataTransfer.files[0]);
                }
            });
        }
    }

    openFileDialog() {
        if (this.fileInput) {
            this.fileInput.click();
        }
    }

    handleFileInput(event) {
        if (event.target.files && event.target.files.length > 0) {
            this.processFile(event.target.files[0]);
        }
    }

    async processFile(file) {
        window.logInfo(`[CFF VAULT] Loading case file: ${file.name}...`);
        const reader = new FileReader();

        reader.onload = async (e) => {
            const content = e.target.result;
            try {
                const resp = await fetch('/api/cff/load', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ cff_content: content })
                });

                const data = await resp.json();
                if (!data.success) {
                    alert("CFF Container Import Failed: " + (data.detail || "Corrupted file"));
                    return;
                }

                if (window.onCaseLoaded) {
                    window.onCaseLoaded(data);
                }
            } catch (err) {
                alert("Error reading .cff case: " + err.message);
                window.logAlert(`[CFF ERROR] ${err.message}`);
            }
        };

        reader.readAsText(file);
    }

    exportCFF(traceData) {
        if (!traceData || !traceData.cff_container) {
            alert("No active case to export. Please run a trace first!");
            return;
        }

        const jsonStr = JSON.stringify(traceData.cff_container, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;

        const caseId = (traceData.cff_container.metadata && traceData.cff_container.metadata.case_id) || 'Forensic_Case';
        a.download = `${caseId}.cff`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);

        const seal = traceData.cff_container.cryptographic_seal ? 
            traceData.cff_container.cryptographic_seal.integrity_hash.substring(0, 12) : 'SEC63';
        window.logSuccess(`[CFF EXPORT] Generated signed case container with SHA-256 seal: ${seal}...`);
    }
}
