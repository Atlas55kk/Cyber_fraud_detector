/**
 * ==============================================================================
 * GRAPH_CONTROLLER.JS - Cytoscape Forensic Graph Canvas & Layout Engine
 * ==============================================================================
 */

class ForensicGraphController {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.cy = null;
        this.currentLayout = 'dagre';
        this.selectedElement = null;
    }

    init() {
        this.cy = cytoscape({
            container: this.container,
            elements: [],
            boxSelectionEnabled: false,
            autounselectify: false,
            wheelSensitivity: 0.2,
            style: [
                // Global Enterprise Entity Cards
                {
                    selector: 'node',
                    style: {
                        'shape': 'round-rectangle',
                        'corner-radius': 6,
                        'width': 116,
                        'height': 34,
                        'background-color': '#0f172a',
                        'border-width': 1.5,
                        'border-color': '#334155',
                        'content': 'data(display_label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'text-wrap': 'wrap',
                        'text-max-width': '126px',
                        'font-family': 'JetBrains Mono, monospace',
                        'font-size': '10px',
                        'font-weight': 600,
                        'line-height': 1.3,
                        'color': '#f8fafc',
                        'transition-property': 'background-color, border-color',
                        'transition-duration': '0.15s'
                    }
                },
                // Role-Specific Card Theming
                {
                    selector: 'node[role = "SCAMMER"]',
                    style: {
                        'background-color': '#210e14',
                        'border-color': '#ef4444',
                        'border-width': 2,
                        'color': '#fca5a5',
                        'shadow-blur': 6,
                        'shadow-color': 'rgba(239, 68, 68, 0.25)',
                        'shadow-opacity': 0.6
                    }
                },
                {
                    selector: 'node[role = "CEX_DEPOSIT"]',
                    style: {
                        'width': 136,
                        'height': 42,
                        'background-color': '#0b201a',
                        'border-color': '#10b981',
                        'border-width': 2,
                        'color': '#6ee7b7',
                        'font-family': 'Inter, sans-serif',
                        'shadow-blur': 6,
                        'shadow-color': 'rgba(16, 185, 129, 0.25)',
                        'shadow-opacity': 0.6
                    }
                },
                {
                    selector: 'node[role = "MULE_TRANSIT"], node[role = "PEEL_CHANGE"], node[role = "UNKNOWN"]',
                    style: {
                        'background-color': '#1a1912',
                        'border-color': '#f59e0b',
                        'border-width': 1.5,
                        'color': '#fde68a',
                        'shadow-blur': 4,
                        'shadow-color': 'rgba(245, 158, 11, 0.2)',
                        'shadow-opacity': 0.6
                    }
                },
                {
                    selector: 'node[role = "VICTIM"]',
                    style: {
                        'background-color': '#091d28',
                        'border-color': '#06b6d4',
                        'color': '#a5f3fc',
                        'shadow-blur': 8,
                        'shadow-color': 'rgba(6, 182, 212, 0.25)',
                        'shadow-opacity': 0.7
                    }
                },
                {
                    selector: 'node[role = "MIXER_POOL"]',
                    style: {
                        'background-color': '#1c112b',
                        'border-color': '#a855f7',
                        'color': '#e9d5ff',
                        'shadow-blur': 12,
                        'shadow-color': 'rgba(168, 85, 247, 0.35)',
                        'shadow-opacity': 0.8
                    }
                },
                {
                    selector: 'node[role = "BRIDGE_CONTRACT"]',
                    style: {
                        'background-color': '#0c1a30',
                        'border-color': '#38bdf8',
                        'color': '#bae6fd',
                        'shadow-blur': 10,
                        'shadow-color': 'rgba(56, 189, 248, 0.3)',
                        'shadow-opacity': 0.7
                    }
                },
                // Selection State
                {
                    selector: 'node:selected',
                    style: {
                        'border-color': '#3b82f6',
                        'border-width': 2,
                        'shadow-blur': 8,
                        'shadow-color': 'rgba(59, 130, 246, 0.4)',
                        'shadow-opacity': 0.8
                    }
                },
                // Transaction Wires (Edges)
                {
                    selector: 'edge',
                    style: {
                        'curve-style': 'bezier',
                        'target-arrow-shape': 'triangle',
                        'target-arrow-color': '#3b82f6',
                        'line-color': '#334155',
                        'width': 1.8,
                        'opacity': 0.85,
                        'label': 'data(label)',
                        'font-size': '9px',
                        'font-family': 'JetBrains Mono, monospace',
                        'font-weight': 600,
                        'color': '#cbd5e1',
                        'text-rotation': 'autorotate',
                        'text-background-opacity': 0.95,
                        'text-background-color': '#080c14',
                        'text-background-padding': '4px',
                        'text-background-shape': 'roundrectangle',
                        'text-border-opacity': 0.85,
                        'text-border-width': 1,
                        'text-border-color': '#1e293b'
                    }
                },
                {
                    selector: 'edge:selected',
                    style: {
                        'line-color': '#3b82f6',
                        'target-arrow-color': '#3b82f6',
                        'width': 3,
                        'opacity': 1.0
                    }
                }
            ]
        });

        // Tap Handlers
        this.cy.on('tap', 'node', (evt) => {
            const node = evt.target;
            this.selectedElement = node;
            if (window.onNodeSelected) {
                window.onNodeSelected(node.data());
            }
        });

        this.cy.on('tap', 'edge', (evt) => {
            const edge = evt.target;
            this.selectedElement = edge;
            if (window.onEdgeSelected) {
                window.onEdgeSelected(edge.data());
            }
        });

        this.cy.on('tap', (evt) => {
            if (evt.target === this.cy) {
                this.selectedElement = null;
                if (window.onCanvasDeselected) {
                    window.onCanvasDeselected();
                }
            }
        });
    }

    render(elements) {
        if (!this.cy) this.init();

        // Format entity display labels for enterprise card presentation
        elements.forEach(el => {
            if (el.group === 'nodes' && el.data) {
                const d = el.data;
                const addr = d.address || d.id || '';
                const shortAddr = addr.length > 14 
                    ? `${addr.substring(0, 6)}...${addr.substring(addr.length - 4)}` 
                    : addr;
                
                // If recognizable exchange entity, show its name and address.
                // Otherwise, show ONLY the address - color alone communicates Crime Root vs Mule vs CEX!
                if (d.role === 'CEX_DEPOSIT' && d.label && !d.label.startsWith('0x') && !d.label.startsWith('T') && !d.label.includes('..')) {
                    const cleanTag = d.label.replace('🏦 ', '');
                    d.display_label = `${cleanTag}\n${shortAddr}`;
                } else {
                    d.display_label = shortAddr;
                }
            }
        });

        this.cy.resize();
        this.cy.elements().remove();
        this.cy.add(elements);
        this.applyLayout(this.currentLayout);

        setTimeout(() => {
            if (this.cy) {
                this.cy.resize();
                this.cy.fit(null, 60);
                this.cy.center();
            }
        }, 120);
    }

    applyLayout(layoutName) {
        this.currentLayout = layoutName;
        this.cy.resize();
        let layoutOptions = {
            name: layoutName,
            animate: false,
            fit: true,
            padding: 60
        };

        if (layoutName === 'dagre') {
            layoutOptions.rankDir = 'LR';
            layoutOptions.nodeSep = 60;
            layoutOptions.rankSep = 140;
        } else if (layoutName === 'breadthfirst') {
            layoutOptions.directed = true;
            layoutOptions.spacingFactor = 1.75;
        } else if (layoutName === 'cose') {
            layoutOptions.componentSpacing = 160;
            layoutOptions.nodeRepulsion = 800000;
            layoutOptions.idealEdgeLength = 160;
        }

        const l = this.cy.layout(layoutOptions);
        l.run();
        this.cy.fit(null, 60);
        this.cy.center();
    }

    zoomIn() {
        if (this.cy) this.cy.zoom(this.cy.zoom() * 1.25);
    }

    zoomOut() {
        if (this.cy) this.cy.zoom(this.cy.zoom() * 0.8);
    }

    fitView() {
        if (this.cy) this.cy.fit(null, 60);
    }

    resetView() {
        if (this.cy) {
            this.cy.zoom(1);
            this.cy.center();
        }
    }
}
