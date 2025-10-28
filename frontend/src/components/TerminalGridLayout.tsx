/**
 * TerminalGridLayout Component
 *
 * Displays multiple terminal windows in a responsive grid layout with:
 * - Automatic 2x2, 3x3 grid sizing based on number of terminals
 * - Drag-and-drop reordering
 * - Resizable panels
 * - Click-to-expand modal view
 *
 * Uses react-grid-layout for interactive grid management
 */

import { useState } from 'react';
import GridLayout, { type Layout } from 'react-grid-layout';
import { TerminalView } from './TerminalView';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

interface Terminal {
  id: string;
  workerId: string;
  title: string;
  terminalType: 'worker' | 'orchestrator';
}

interface TerminalGridLayoutProps {
  /** List of worker IDs to display */
  workerIds: string[];
  /** Optional CSS class name */
  className?: string;
}

export function TerminalGridLayout({
  workerIds,
  className = '',
}: TerminalGridLayoutProps) {
  const [expandedTerminal, setExpandedTerminal] = useState<string | null>(null);

  // Generate terminal list (worker + orchestrator for each worker)
  const terminals: Terminal[] = workerIds.flatMap((workerId) => [
    {
      id: `${workerId}-worker`,
      workerId,
      title: `🔵 ${workerId} Worker`,
      terminalType: 'worker' as const,
    },
    {
      id: `${workerId}-orchestrator`,
      workerId,
      title: `🟣 ${workerId} Orchestrator`,
      terminalType: 'orchestrator' as const,
    },
  ]);

  // Calculate optimal grid dimensions
  const totalTerminals = terminals.length;
  const cols = Math.ceil(Math.sqrt(totalTerminals));
  const rows = Math.ceil(totalTerminals / cols);

  // Generate layout configuration
  const layout: Layout[] = terminals.map((terminal, index) => ({
    i: terminal.id,
    x: index % cols,
    y: Math.floor(index / cols),
    w: 1,
    h: 1,
    minW: 1,
    minH: 1,
  }));

  // Handle layout change (for persistence later)
  const handleLayoutChange = (newLayout: Layout[]) => {
    // TODO: Persist layout to localStorage
    console.log('Layout changed:', newLayout);
  };

  // Handle terminal click to expand
  const handleTerminalClick = (terminalId: string) => {
    setExpandedTerminal(terminalId);
  };

  // Close expanded modal
  const handleCloseModal = () => {
    setExpandedTerminal(null);
  };

  return (
    <div className={`relative h-full w-full ${className}`}>
      {/* Grid Layout */}
      <GridLayout
        className="layout"
        layout={layout}
        cols={cols}
        rowHeight={(window.innerHeight - 200) / rows}
        width={window.innerWidth - 380}
        onLayoutChange={handleLayoutChange}
        draggableHandle=".terminal-drag-handle"
        compactType={null}
        preventCollision={true}
      >
        {terminals.map((terminal) => (
          <div
            key={terminal.id}
            className="cursor-pointer"
            onClick={() => handleTerminalClick(terminal.id)}
          >
            {/* Drag Handle */}
            <div className="terminal-drag-handle absolute top-0 left-0 right-0 h-8 cursor-move z-10 opacity-0 hover:opacity-100 bg-blue-600/20 transition-opacity" />

            <TerminalView
              workerId={terminal.workerId}
              title={terminal.title}
              terminalType={terminal.terminalType}
              className="h-full pointer-events-none"
            />
          </div>
        ))}
      </GridLayout>

      {/* Expanded Modal */}
      {expandedTerminal && (
        <div
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-8"
          onClick={handleCloseModal}
        >
          <div
            className="w-full h-full max-w-7xl max-h-[90vh]"
            onClick={(e) => e.stopPropagation()}
          >
            {terminals
              .filter((t) => t.id === expandedTerminal)
              .map((terminal) => (
                <div key={terminal.id} className="relative h-full">
                  {/* Close Button */}
                  <button
                    onClick={handleCloseModal}
                    className="absolute top-4 right-4 z-10 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg shadow-lg transition-colors"
                  >
                    ✕ Close
                  </button>

                  <TerminalView
                    workerId={terminal.workerId}
                    title={`${terminal.title} (Expanded)`}
                    terminalType={terminal.terminalType}
                    className="h-full"
                  />
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
