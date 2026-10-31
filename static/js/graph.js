/**
 * Reusable Cytoscape.js Automata Graph Renderer & Interaction Module
 */

const CytoscapeStyles = [
    // Base node style
    {
        selector: 'node',
        style: {
            'label': 'data(label)',
            'color': '#0f172a',
            'font-family': 'Fira Code, monospace',
            'font-size': '11px',
            'font-weight': '600',
            'text-valign': 'center',
            'text-halign': 'center',
            'text-wrap': 'wrap',
            'text-max-width': '75px',
            'background-color': '#ffffff',
            'border-width': 2.5,
            'border-color': '#334155',
            'width': 56,
            'height': 56,
            'transition-property': 'background-color, border-color, border-width, width, height',
            'transition-duration': '0.2s',
        }
    },
    // Initial state style
    {
        selector: 'node.initial',
        style: {
            'border-color': '#2563eb',
            'border-width': 3.5,
            'background-color': '#eff6ff',
        }
    },
    // Initial AND Accepting state style (Double circle with blue border)
    {
        selector: 'node.initial.accepting',
        style: {
            'border-style': 'double',
            'border-width': 6,
            'border-color': '#2563eb',
            'background-color': '#eff6ff',
        }
    },
    // Start Marker anchor (invisible point from nowhere - no bulky box)
    {
        selector: 'node.start-marker-node, node[type = "start_marker"]',
        style: {
            'width': 1,
            'height': 1,
            'opacity': 0,
            'background-opacity': 0,
            'border-opacity': 0,
            'label': '',
            'events': 'no',
            'z-index': 1,
        }
    },
    // Start Arrow directed edge pointing into initial state (Textbook -> arrow)
    {
        selector: 'edge.start-arrow-edge, edge[type = "start_arrow"]',
        style: {
            'width': 2.5,
            'line-color': '#2563eb',
            'target-arrow-color': '#2563eb',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 1.4,
            'curve-style': 'straight',
            'line-style': 'solid',
            'label': '',
            'z-index': 1000,
            'events': 'no',
        }
    },
    // Accepting state style (Double circle border)
    {
        selector: 'node.accepting',
        style: {
            'border-style': 'double',
            'border-width': 6,
            'border-color': '#059669',
            'background-color': '#f0fdf4',
        }
    },
    // Dead / Trap state style (Distinct vibrant crimson theme)
    {
        selector: 'node.dead-state',
        style: {
            'border-color': '#dc2626',
            'border-width': 4,
            'border-style': 'solid',
            'background-color': '#fee2e2',
            'color': '#991b1b',
            'font-weight': '700',
        }
    },
    // Active Source state during simulation or conversion (Gold Glow)
    {
        selector: 'node.highlighted, node.active-source-node',
        style: {
            'background-color': '#fef08a',
            'border-color': '#d97706',
            'border-width': 4.5,
            'width': 62,
            'height': 62,
            'z-index': 999,
        }
    },
    // Active Target state during step conversion (Emerald Green Glow)
    {
        selector: 'node.target-highlighted, node.active-target-node',
        style: {
            'background-color': '#bbf7d0',
            'border-color': '#059669',
            'border-width': 4.5,
            'width': 62,
            'height': 62,
            'z-index': 998,
        }
    },
    // Base edge style
    {
        selector: 'edge',
        style: {
            'label': 'data(label)',
            'color': '#1e293b',
            'font-family': 'Fira Code, monospace',
            'font-size': '11px',
            'font-weight': '600',
            'text-background-color': '#ffffff',
            'text-background-opacity': 0.92,
            'text-background-padding': '3px',
            'text-background-shape': 'roundrectangle',
            'text-border-color': '#cbd5e1',
            'text-border-width': 1,
            'text-border-opacity': 0.8,
            'width': 2,
            'line-color': '#64748b',
            'target-arrow-color': '#64748b',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'control-point-step-size': 45,
            'loop-direction': '-45deg',
            'loop-sweep': '-90deg',
            'arrow-scale': 1.15,
            'transition-property': 'line-color, target-arrow-color, width',
            'transition-duration': '0.2s',
        }
    },
    // Highlighted edge during simulation / step
    {
        selector: 'edge.highlighted, edge.active-edge',
        style: {
            'line-color': '#ea580c',
            'target-arrow-color': '#ea580c',
            'width': 4.5,
            'z-index': 999,
            'text-background-color': '#ffedd5',
            'text-border-color': '#ea580c',
            'text-border-width': 1.5,
        }
    }
];

class AutomataGraph {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.options = options;
        this.cy = null;
        this.onNodeClick = options.onNodeClick || null;
    }

    render(elements) {
        if (!this.container) return;

        if (this.cy) {
            this.cy.destroy();
        }

        this.cy = cytoscape({
            container: this.container,
            elements: elements || [],
            style: CytoscapeStyles,
            layout: {
                name: 'cose',
                animate: true,
                animationDuration: 350,
                nodeDimensionsIncludeLabels: true,
                fit: true,
                padding: 45,
                randomize: false,
                componentSpacing: 100,
                nodeRepulsion: function(node) { return 350000; },
                idealEdgeLength: function(edge) { return 120; },
            },
            minZoom: 0.35,
            maxZoom: 1.5,
            wheelSensitivity: 0.25,
        });

        if (this.onNodeClick) {
            this.cy.on('tap', 'node', (evt) => {
                const node = evt.target;
                if (node.data('type') === 'start_marker') return;
                this.onNodeClick(node.data());
            });
        }

        // When layout completes, position start marker arrow cleanly to the left of the initial state
        this.cy.on('layoutstop', () => {
            this.positionStartMarkers();
        });

        // Keep start marker attached when user drags the initial state node
        this.cy.on('drag', 'node', (evt) => {
            const node = evt.target;
            if (node.data('type') === 'start_marker') return;
            const marker = this.cy.getElementById(`__start_marker_${node.id()}`);
            if (marker && marker.length > 0) {
                const pos = node.position();
                marker.position({
                    x: pos.x - 65,
                    y: pos.y
                });
            }
        });

        // Trigger immediate position in case layout completes synchronously
        setTimeout(() => this.positionStartMarkers(), 50);

        return this.cy;
    }

    positionStartMarkers() {
        if (!this.cy) return;
        this.cy.nodes('[type = "start_marker"]').forEach(marker => {
            const outEdges = marker.outgoers('edge');
            if (outEdges && outEdges.length > 0) {
                const targetNode = outEdges[0].target();
                if (targetNode && targetNode.length > 0) {
                    const pos = targetNode.position();
                    marker.position({
                        x: pos.x - 65,
                        y: pos.y
                    });
                    marker.lock();
                }
            }
        });
    }

    fit() {
        if (this.cy) {
            this.positionStartMarkers();
            this.cy.fit(undefined, 40);
        }
    }

    resetLayout() {
        if (!this.cy) return;
        this.cy.nodes().unlock();
        const layout = this.cy.layout({
            name: 'cose',
            animate: true,
            animationDuration: 350,
            fit: true,
            padding: 45,
            nodeRepulsion: function(node) { return 350000; },
            idealEdgeLength: function(edge) { return 120; },
        });
        layout.run();
    }

    clearHighlights() {
        if (!this.cy) return;
        this.cy.nodes().removeClass('highlighted active-source-node target-highlighted active-target-node');
        this.cy.edges().removeClass('highlighted active-edge');
    }

    highlightActiveNodes(nodeIds) {
        this.highlightSourceNodes(nodeIds);
    }

    highlightSourceNodes(nodeIds) {
        if (!this.cy || !nodeIds) return;
        const ids = Array.isArray(nodeIds) ? nodeIds : [nodeIds];
        ids.forEach(id => {
            const node = this.cy.getElementById(id);
            if (node && node.length > 0) {
                node.addClass('active-source-node');
            }
        });
    }

    highlightTargetNode(nodeId) {
        if (!this.cy || !nodeId) return;
        const ids = Array.isArray(nodeId) ? nodeId : [nodeId];
        ids.forEach(id => {
            const node = this.cy.getElementById(id);
            if (node && node.length > 0) {
                node.addClass('active-target-node');
            }
        });
    }

    highlightTransitionEdge(sourceId, targetId, symbol) {
        if (!this.cy) return;
        this.cy.edges().forEach(edge => {
            if (edge.source().id() === sourceId && edge.target().id() === targetId) {
                const syms = edge.data('symbols') || [];
                if (!symbol || syms.includes(symbol) || edge.data('label').includes(symbol)) {
                    edge.addClass('active-edge');
                }
            }
        });
    }
}
