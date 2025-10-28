/**
 * TerminalView Component
 *
 * Displays raw terminal output from worker processes in a terminal-like interface.
 *
 * Features:
 * - Real-time terminal line streaming
 * - Terminal-style UI (black background, monospace font, green text)
 * - Auto-scroll to latest output
 * - Connection status indicator
 * - Loading and error states
 * - Terminal search with highlighting (Phase 2.2 Feature 1)
 * - Keyboard shortcuts (Ctrl+F, Enter, Shift+Enter, Escape)
 */

import { useEffect, useRef, useState } from 'react';
import { useTerminalWebSocket } from '../hooks/useTerminalWebSocket';
import { useTerminalSearch } from '../hooks/useTerminalSearch';
import { ConnectionStatus } from './ConnectionStatus';
import { SearchBar } from './SearchBar';
import type { SearchOptions } from './SearchBar';

interface TerminalViewProps {
  /** Worker ID to monitor */
  workerId: string;
  /** Optional CSS class name */
  className?: string;
  /** Optional title */
  title?: string;
  /** Terminal type: worker or orchestrator */
  terminalType?: 'worker' | 'orchestrator';
}

export function TerminalView({
  workerId,
  className = '',
  title = 'Worker Terminal',
  terminalType = 'worker',
}: TerminalViewProps) {
  const { lines, status, error, isReady, reconnect } =
    useTerminalWebSocket(workerId, { terminalType });
  const linesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const currentMatchRef = useRef<HTMLDivElement>(null);

  // Search functionality (Phase 2.2 Feature 1)
  const {
    searchQuery,
    setSearchQuery,
    setOptions,
    currentMatchIndex,
    totalMatches,
    nextMatch,
    prevMatch,
    clearSearch,
    highlightedLines,
    currentMatch,
  } = useTerminalSearch(lines);

  // Track if search is active (to disable auto-scroll)
  const [isSearchActive, setIsSearchActive] = useState(false);

  // Update search active state
  useEffect(() => {
    setIsSearchActive(searchQuery.length > 0);
  }, [searchQuery]);

  // Handle search callback
  const handleSearch = (query: string, searchOptions: SearchOptions) => {
    setSearchQuery(query);
    setOptions(searchOptions);
  };

  // Handle clear search
  const handleClearSearch = () => {
    clearSearch();
    setIsSearchActive(false);
  };

  // Auto-scroll to bottom when new lines arrive (only when not searching)
  useEffect(() => {
    if (!isSearchActive && linesEndRef.current) {
      linesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [lines.length, isSearchActive]);

  // Auto-scroll to current match when searching
  useEffect(() => {
    if (isSearchActive && currentMatch && currentMatchRef.current) {
      currentMatchRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  }, [currentMatch, isSearchActive]);

  // Keyboard shortcuts (Phase 2.2)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+F / Cmd+F: Focus search bar
      if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        searchInputRef.current?.focus();
      }

      // Enter: Next match (only if search is active)
      if (e.key === 'Enter' && !e.shiftKey && searchQuery && totalMatches > 0) {
        if (document.activeElement === searchInputRef.current) {
          e.preventDefault();
          nextMatch();
        }
      }

      // Shift+Enter: Previous match (only if search is active)
      if (e.key === 'Enter' && e.shiftKey && searchQuery && totalMatches > 0) {
        e.preventDefault();
        prevMatch();
      }

      // Escape: Clear search
      if (e.key === 'Escape' && searchQuery) {
        e.preventDefault();
        handleClearSearch();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [searchQuery, totalMatches, nextMatch, prevMatch, handleClearSearch]);

  return (
    <div
      className={`flex flex-col h-full bg-black rounded-lg shadow-xl overflow-hidden border border-gray-700 ${className}`}
    >
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-700 px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-green-400 font-mono">
              {title}
            </h2>
            <p className="text-xs text-gray-500 mt-1 font-mono">
              {workerId}
            </p>
          </div>

          <ConnectionStatus
            status={status}
            error={error}
            onReconnect={reconnect}
          />
        </div>
      </div>

      {/* Search Bar (Phase 2.2 Feature 1) */}
      <SearchBar
        onSearch={handleSearch}
        matchCount={totalMatches}
        currentMatch={currentMatchIndex + 1}
        onNext={nextMatch}
        onPrevious={prevMatch}
        onClear={handleClearSearch}
        inputRef={searchInputRef}
      />

      {/* Terminal Output */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto px-4 py-3 custom-scrollbar bg-black"
      >
        {/* Loading State */}
        {status === 'connecting' && lines.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-gray-600 border-t-green-400 mb-3"></div>
              <p className="text-gray-500 text-sm font-mono">
                Connecting to {workerId}...
              </p>
            </div>
          </div>
        )}

        {/* Error State */}
        {status === 'error' && lines.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md">
              <div className="text-red-500 text-4xl mb-3">⚠</div>
              <p className="text-red-400 text-sm font-semibold mb-2 font-mono">
                Connection Error
              </p>
              <p className="text-gray-500 text-xs mb-3 font-mono">
                {error || 'Failed to connect to terminal stream'}
              </p>
              <button
                onClick={reconnect}
                className="px-3 py-1.5 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition-colors font-mono"
              >
                Retry Connection
              </button>
            </div>
          </div>
        )}

        {/* Empty State (Connected but no output) */}
        {status === 'connected' && isReady && lines.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-gray-600 text-5xl mb-3">▶</div>
              <p className="text-gray-500 text-sm font-mono">
                No terminal output yet
              </p>
              <p className="text-gray-600 text-xs mt-2 font-mono">
                Waiting for worker activity...
              </p>
            </div>
          </div>
        )}

        {/* Terminal Lines (with search highlighting if active) */}
        {lines.map((line, index) => {
          const isCurrentMatchLine =
            currentMatch && currentMatch.lineIndex === index;

          return (
            <div
              key={`${line.timestamp}-${index}`}
              ref={isCurrentMatchLine ? currentMatchRef : null}
              className="text-green-400 text-sm font-mono whitespace-pre-wrap leading-relaxed terminal-line"
              data-line-index={index}
            >
              {isSearchActive ? highlightedLines[index] : line.content}
            </div>
          );
        })}

        {/* Auto-scroll anchor */}
        <div ref={linesEndRef} />
      </div>

      {/* Footer */}
      <div className="bg-gray-900 border-t border-gray-700 px-4 py-2">
        <div className="flex items-center justify-between text-xs text-gray-500 font-mono">
          <span>
            {lines.length} {lines.length === 1 ? 'line' : 'lines'}
          </span>
          {isReady && (
            <span className="flex items-center gap-2">
              <span className="inline-block w-2 h-2 bg-green-500 rounded-full live-pulse"></span>
              LIVE
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
