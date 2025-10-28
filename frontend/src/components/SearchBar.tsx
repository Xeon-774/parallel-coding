/**
 * SearchBar Component
 *
 * Terminal search interface with case-sensitive and regex options.
 * Part of Phase 2.2 Feature 1 (Terminal Search & Filtering).
 *
 * Features:
 * - Real-time search input
 * - Case-sensitive toggle
 * - Regex pattern support (optional)
 * - Match counter display
 * - Next/Previous navigation buttons
 * - Clear search button
 *
 * @example
 * ```tsx
 * <SearchBar
 *   onSearch={(query, opts) => handleSearch(query, opts)}
 *   matchCount={12}
 *   currentMatch={3}
 *   onNext={() => goToNext()}
 *   onPrevious={() => goToPrevious()}
 *   onClear={() => clearSearch()}
 * />
 * ```
 */

import { useState, useRef, useEffect } from 'react';

export interface SearchOptions {
  caseSensitive: boolean;
  useRegex: boolean;
}

export interface SearchBarProps {
  /** Callback when search query or options change */
  onSearch: (query: string, options: SearchOptions) => void;
  /** Total number of matches found */
  matchCount: number;
  /** Current match index (1-based for display) */
  currentMatch: number;
  /** Navigate to next match */
  onNext: () => void;
  /** Navigate to previous match */
  onPrevious: () => void;
  /** Clear search and reset state */
  onClear: () => void;
  /** Optional CSS class name */
  className?: string;
  /** Optional ref for search input (for keyboard shortcuts) */
  inputRef?: React.RefObject<HTMLInputElement | null>;
}

export function SearchBar({
  onSearch,
  matchCount,
  currentMatch,
  onNext,
  onPrevious,
  onClear,
  className = '',
  inputRef: externalInputRef,
}: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [caseSensitive, setCaseSensitive] = useState(false);
  const [useRegex, setUseRegex] = useState(false);
  const internalInputRef = useRef<HTMLInputElement>(null);

  // Use external ref if provided, otherwise use internal ref
  const inputRef = externalInputRef || internalInputRef;

  // Update search when query or options change
  const handleQueryChange = (newQuery: string) => {
    setQuery(newQuery);
    onSearch(newQuery, { caseSensitive, useRegex });
  };

  const handleCaseSensitiveChange = (checked: boolean) => {
    setCaseSensitive(checked);
    onSearch(query, { caseSensitive: checked, useRegex });
  };

  const handleRegexChange = (checked: boolean) => {
    setUseRegex(checked);
    onSearch(query, { caseSensitive, useRegex: checked });
  };

  const handleClear = () => {
    setQuery('');
    setCaseSensitive(false);
    setUseRegex(false);
    onClear();
    inputRef.current?.focus();
  };

  // Focus input when component mounts
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const hasMatches = matchCount > 0;
  const showMatchCounter = query.length > 0;

  return (
    <div
      className={`flex items-center gap-2 px-4 py-2 bg-gray-800 border-b border-gray-700 ${className}`}
    >
      {/* Search Input */}
      <div className="flex-1 relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => handleQueryChange(e.target.value)}
          placeholder="Search terminal output... (Ctrl+F)"
          className="w-full px-3 py-1.5 bg-gray-900 text-white text-sm rounded border border-gray-600 focus:border-blue-500 focus:outline-none font-mono transition-colors"
          aria-label="Search terminal output"
        />
        {query && (
          <button
            onClick={handleClear}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
            aria-label="Clear search"
            title="Clear search (Escape)"
          >
            ×
          </button>
        )}
      </div>

      {/* Case-Sensitive Toggle */}
      <label className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-300 cursor-pointer transition-colors">
        <input
          type="checkbox"
          checked={caseSensitive}
          onChange={(e) => handleCaseSensitiveChange(e.target.checked)}
          className="w-4 h-4 rounded border-gray-600 bg-gray-900 text-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer"
          aria-label="Case sensitive search"
        />
        <span className="font-mono select-none">Case</span>
      </label>

      {/* Regex Toggle */}
      <label className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-300 cursor-pointer transition-colors">
        <input
          type="checkbox"
          checked={useRegex}
          onChange={(e) => handleRegexChange(e.target.checked)}
          className="w-4 h-4 rounded border-gray-600 bg-gray-900 text-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer"
          aria-label="Use regex"
        />
        <span className="font-mono select-none">Regex</span>
      </label>

      {/* Match Counter */}
      {showMatchCounter && (
        <div className="text-sm text-gray-400 font-mono min-w-[80px] text-center">
          {hasMatches ? (
            <span className="text-green-400">
              {currentMatch} of {matchCount}
            </span>
          ) : (
            <span className="text-yellow-500">0 matches</span>
          )}
        </div>
      )}

      {/* Navigation Buttons */}
      <div className="flex items-center gap-1">
        <button
          onClick={onPrevious}
          disabled={!hasMatches}
          className="p-1.5 rounded hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-transparent transition-colors"
          aria-label="Previous match (Shift+Enter)"
          title="Previous match (Shift+Enter)"
        >
          <svg
            className="w-4 h-4 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 15l7-7 7 7"
            />
          </svg>
        </button>

        <button
          onClick={onNext}
          disabled={!hasMatches}
          className="p-1.5 rounded hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-transparent transition-colors"
          aria-label="Next match (Enter)"
          title="Next match (Enter)"
        >
          <svg
            className="w-4 h-4 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}