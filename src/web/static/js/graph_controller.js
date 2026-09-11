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
                // Global Nodes
                {
                    selector: 'node',
                    style: {
                        'content': 'data(label)',
                        'text-valign': 'bottom',
                        'text-halign': 'center',
                        'text-margin-y': 6,
                        'color': '#cbd5e1',
                        'font-size': '10px',
                        'font-family': 'Inter, sans-serif',
                        'font-weight': 600,
                        'background-color': '#334155',
                        'border-width': 2,
                        'border-color': '#475569',
                        'width': 36,
                        'height': 36,
                        'text-outline-color': '#06090e',
                        'text-outline-width': 2,
                        'transition-property': 'background-color, border-color, width, height',
                        'transition-duration': '0.2s'
                    }
                },
                // Role-Specific Nodes
                {
                    selector: 'node[role = "SCAMMER"]',
                    style: {
                        'background-color': '#ef4444',
                        'border-color': '#f87171',
                        'width': 44,
                        'height': 44,
                        'shape': 'hexagon',
                        'shadow-blur': 12,
                        'shadow-color': 'rgba(239, 68, 68, 0.4)',
                        'shadow-opacity': 0.8
                    }
                },
                {
                    selector: 'node[role = "VICTIM"]',
                    style: {
                        'background-color': '#06b6d4',
                        'border-color': '#38bdf8',
                        'width': 40,
                        'height': 40,
                        'shape': 'round-diamond'
                    }
                },
                {
                    selector: 'node[role = "MULE_TRANSIT"], node[role = "PEEL_CHANGE"]',
                    style: {
                        'background-color': '#f59e0b',
                        'border-color': '#fbbf24',
                        'width': 34,
                        'height': 34,
                        'shape': 'ellipse'
                    }
                },
                {
                    selector: 'node[role = "CEX_DEPOSIT"]',
                    style: {
                        'background-color': '#10b981',
                        'border-color': '#34d399',
                        'width': 44,
                        'height': 44,
                        'shape': 'rectangle',
                        'shadow-blur': 14,
                        'shadow-color': 'rgba(16, 185, 129, 0.4)',
                        'shadow-opacity': 0.8
                    }
                },
                {
                    selector: 'node[role = "MIXER_POOL"]',
                    style: {
                        'background-color': '#a855f7',
                        'border-color': '#c084fc',
                        'width': 40,
                        'height': 40,
                        'shape': 'diamond'
                    }
                },
                {
                    selector: 'node[role = "BRIDGE_CONTRACT"]',
                    style: {
                        'background-color': '#3b82f6',
                        'border-color': '#60a5fa',
                        'width': 40,
                        'height': 40,
                        'shape': 'round-rectangle'
                    }
                },
                // Selection State
                {
                    selector: 'node:selected',
                    style: {
                        'border-color': '#38bdf8',
                        'border-width': 4,
                        'shadow-blur': 18,
                        'shadow-color': '#38bdf8',
                        'shadow-opacity': 1.0
                    }
                },
                // Transaction Wires (Edges)
                {
                    selector: 'edge',
                    style: {
                        'curve-style': 'bezier',
                        'target-arrow-shape': 'triangle',
                        'target-arrow-color': '#64748b',
                        'line-color': '#334155',
                        'width': 2.5,
                        'opacity': 0.85,
                        'label': 'data(label)',
                        'font-size': '9px',
                        'font-family': 'JetBrains Mono, monospace',
                        'font-weight': 600,
                        'color': '#94a3b8',
                        'text-rotation': 'autorotate',
                        'text-background-opacity': 0.9,
                        'text-background-color': '#0c111a',
                        'text-background-padding': 3,
                        'text-background-shape': 'roundrectangle',
                        'text-border-opacity': 0.6,
                        'text-border-width': 0.5,
                        'text-border-color': '#334155'
                    }
                },
                {
                    selector: 'edge:selected',
                    style: {
                        'line-color': '#38bdf8',
                        'target-arrow-color': '#38bdf8',
                        'width': 4,
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
        this.cy.resize();
        this.cy.elements().remove();
        this.cy.add(elements);
        this.applyLayout(this.currentLayout);
    }

    applyLayout(layoutName) {
        this.currentLayout = layoutName;
        let layoutOptions = {};

        if (layoutName === 'dagre') {
            layoutOptions = {
                name: 'dagre',
                rankDir: 'LR',
                nodeSep: 70,
                rankSep: 120,
                animate: true,
                animationDuration: 400
            };
        } else if (layoutName === 'breadthfirst') {
            layoutOptions = {
                name: 'breadthfirst',
                directed: true,
                spacingFactor: 1.5,
                animate: true,
                animationDuration: 400
            };
        } else if (layoutName === 'cose') {
            layoutOptions = {
                name: 'cose',
                animate: true,
                randomize: false,
                componentSpacing: 120,
                nodeRepulsion: 500000,
                idealEdgeLength: 120,
                animationDuration: 500
            };
        }

        const l = this.cy.layout(layoutOptions);
        l.one('layoutstop', () => {
            this.cy.resize();
            this.cy.fit(null, 60);
        });
        l.run();
    }


    zoomIn() {
        if (this.cy) this.cy.zoom(this.cy.zoom() * 1.25);
    }

    zoomOut() {
        if (this.cy) this.cy.zoom(this.cy.zoom() * 0.8);
    }

    fitView() {
        if (this.cy) this.cy.fit(null, 40);
    }

    resetView() {
        if (this.cy) {
            this.cy.zoom(1);
            this.cy.center();
        }
    }
}
