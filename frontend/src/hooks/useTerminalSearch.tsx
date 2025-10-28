/**
 * useTerminalSearch Hook
 *
 * Client-side terminal search with match highlighting and navigation.
 * Part of Phase 2.2 Feature 1 (Terminal Search & Filtering).
 *
 * Features:
 * - Real-time search across terminal lines
 * - Case-sensitive and case-insensitive search
 * - Regex pattern support
 * - Match highlighting (current match vs other matches)
 * - Navigation through matches (next/previous)
 * - Performance optimized with useMemo
 *
 * @example
 * ```tsx
 * const {
 *   searchQuery,
 *   setSearchQuery,
 *   options,
 *   setOptions,
 *   matches,
 *   currentMatchIndex,
 *   totalMatches,
 *   nextMatch,
 *   prevMatch,
 *   clearSearch,
 *   highlightedLines
 * } = useTerminalSearch(lines);
 * ```
 */

import { useState, useMemo, useCallback } from 'react';
import type { ReactNode } from 'react';
import type { SearchOptions } from '../components/SearchBar';

/** Terminal line structure from useTerminalWebSocket */
export interface TerminalLine {
  content: string;
  timestamp: number;
}

/** Match location within a line */
export interface Match {
  lineIndex: number;
  startIndex: number;
  endIndex: number;
  text: string;
}

/** Hook return value */
export interface UseTerminalSearchResult {
  /** Current search query */
  searchQuery: string;
  /** Update search query */
  setSearchQuery: (query: string) => void;
  /** Current search options */
  options: SearchOptions;
  /** Update search options */
  setOptions: (options: SearchOptions) => void;
  /** All matches found */
  matches: Match[];
  /** Current match index (0-based) */
  currentMatchIndex: number;
  /** Total number of matches */
  totalMatches: number;
  /** Navigate to next match */
  nextMatch: () => void;
  /** Navigate to previous match */
  prevMatch: () => void;
  /** Clear search and reset state */
  clearSearch: () => void;
  /** Lines with highlighted matches (ReactNode array) */
  highlightedLines: ReactNode[];
  /** Current match for auto-scroll */
  currentMatch: Match | null;
}

/**
 * Custom hook for terminal search functionality
 *
 * @param lines - Terminal lines to search through
 * @returns Search state and control functions
 */
export function useTerminalSearch(
  lines: TerminalLine[]
): UseTerminalSearchResult {
  const [searchQuery, setSearchQuery] = useState('');
  const [options, setOptions] = useState<SearchOptions>({
    caseSensitive: false,
    useRegex: false,
  });
  const [currentMatchIndex, setCurrentMatchIndex] = useState(0);

  // Find all matches in terminal lines
  const matches = useMemo<Match[]>(() => {
    if (!searchQuery) return [];

    const results: Match[] = [];

    try {
      lines.forEach((line, lineIndex) => {
        const content = line.content;

        if (options.useRegex) {
          // Regex search
          const flags = options.caseSensitive ? 'g' : 'gi';
          const regex = new RegExp(searchQuery, flags);

          let match;
          while ((match = regex.exec(content)) !== null) {
            results.push({
              lineIndex,
              startIndex: match.index,
              endIndex: match.index + match[0].length,
              text: match[0],
            });

            // Prevent infinite loop with zero-length matches
            if (match[0].length === 0) {
              regex.lastIndex++;
            }
          }
        } else {
          // Plain text search
          const searchLine = options.caseSensitive
            ? content
            : content.toLowerCase();
          const searchText = options.caseSensitive
            ? searchQuery
            : searchQuery.toLowerCase();

          let index = 0;
          while ((index = searchLine.indexOf(searchText, index)) !== -1) {
            results.push({
              lineIndex,
              startIndex: index,
              endIndex: index + searchQuery.length,
              text: content.substring(index, index + searchQuery.length),
            });
            index += searchQuery.length;
          }
        }
      });
    } catch (error) {
      // Invalid regex or other error - return empty results
      console.warn('Search error:', error);
    }

    return results;
  }, [lines, searchQuery, options]);

  // Reset current match index when matches change
  useMemo(() => {
    if (matches.length > 0 && currentMatchIndex >= matches.length) {
      setCurrentMatchIndex(0);
    } else if (matches.length === 0) {
      setCurrentMatchIndex(0);
    }
  }, [matches.length, currentMatchIndex]);

  // Navigate to next match
  const nextMatch = useCallback(() => {
    if (matches.length === 0) return;
    setCurrentMatchIndex((prev) => (prev + 1) % matches.length);
  }, [matches.length]);

  // Navigate to previous match
  const prevMatch = useCallback(() => {
    if (matches.length === 0) return;
    setCurrentMatchIndex((prev) => (prev - 1 + matches.length) % matches.length);
  }, [matches.length]);

  // Clear search and reset state
  const clearSearch = useCallback(() => {
    setSearchQuery('');
    setCurrentMatchIndex(0);
  }, []);

  // Generate highlighted lines
  const highlightedLines = useMemo<ReactNode[]>(() => {
    return lines.map((line, lineIndex) => {
      const lineMatches = matches.filter((m) => m.lineIndex === lineIndex);

      if (lineMatches.length === 0) {
        return line.content;
      }

      return highlightLine(
        line.content,
        lineMatches,
        matches[currentMatchIndex],
        lineIndex
      );
    });
  }, [lines, matches, currentMatchIndex]);

  // Get current match for auto-scroll
  const currentMatch = matches.length > 0 ? matches[currentMatchIndex] : null;

  return {
    searchQuery,
    setSearchQuery,
    options,
    setOptions,
    matches,
    currentMatchIndex,
    totalMatches: matches.length,
    nextMatch,
    prevMatch,
    clearSearch,
    highlightedLines,
    currentMatch,
  };
}

/**
 * Highlight matches in a single line
 *
 * @param line - Line content
 * @param lineMatches - Matches within this line
 * @param currentMatch - Currently selected match (for different highlighting)
 * @param lineIndex - Line index for comparison
 * @returns ReactNode with highlighted segments
 */
function highlightLine(
  line: string,
  lineMatches: Match[],
  currentMatch: Match | undefined,
  lineIndex: number
): ReactNode {
  const segments: ReactNode[] = [];
  let lastIndex = 0;

  // Sort matches by start index
  const sortedMatches = [...lineMatches].sort(
    (a, b) => a.startIndex - b.startIndex
  );

  sortedMatches.forEach((match, i) => {
    // Add text before match
    if (match.startIndex > lastIndex) {
      segments.push(
        <span key={`text-${i}`}>{line.substring(lastIndex, match.startIndex)}</span>
      );
    }

    // Determine if this is the current match
    const isCurrent =
      currentMatch &&
      match.lineIndex === currentMatch.lineIndex &&
      match.startIndex === currentMatch.startIndex &&
      match.endIndex === currentMatch.endIndex;

    // Add highlighted match
    segments.push(
      <mark
        key={`match-${i}`}
        className={
          isCurrent
            ? 'bg-orange-400 text-black font-bold px-0.5 rounded'
            : 'bg-yellow-500 text-black px-0.5 rounded'
        }
        data-match-line={lineIndex}
        data-match-index={i}
      >
        {match.text}
      </mark>
    );

    lastIndex = match.endIndex;
  });

  // Add remaining text after last match
  if (lastIndex < line.length) {
    segments.push(
      <span key="text-end">{line.substring(lastIndex)}</span>
    );
  }

  return <>{segments}</>;
}
