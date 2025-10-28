/**
 * Tests for useTerminalSearch hook
 * Phase 2.2 Feature 1
 */

import { renderHook, act } from '@testing-library/react';
import { useTerminalSearch } from '../useTerminalSearch';
import type { TerminalLine } from '../useTerminalSearch';

describe('useTerminalSearch', () => {
  const createLines = (contents: string[]): TerminalLine[] =>
    contents.map((content, i) => ({ content, timestamp: i }));

  describe('Basic Search', () => {
    it('should find all matches in terminal lines', () => {
      const lines = createLines([
        'Hello World',
        'hello again',
        'HELLO there',
      ]);

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('hello');
      });

      expect(result.current.totalMatches).toBe(3);
      expect(result.current.matches).toHaveLength(3);
    });

    it('should return empty matches for empty query', () => {
      const lines = createLines(['Hello World']);

      const { result } = renderHook(() => useTerminalSearch(lines));

      expect(result.current.totalMatches).toBe(0);
      expect(result.current.matches).toHaveLength(0);
    });

    it('should handle lines with no matches', () => {
      const lines = createLines(['foo', 'bar', 'baz']);

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('xyz');
      });

      expect(result.current.totalMatches).toBe(0);
    });
  });

  describe('Case Sensitivity', () => {
    it('should be case-insensitive by default', () => {
      const lines = createLines(['Hello', 'HELLO', 'hello']);

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('hello');
      });

      expect(result.current.totalMatches).toBe(3);
    });

    it('should respect case-sensitive option', () => {
      const lines = createLines(['Hello', 'HELLO', 'hello']);

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('hello');
        result.current.setOptions({ caseSensitive: true, useRegex: false });
      });

      expect(result.current.totalMatches).toBe(1);
      expect(result.current.matches[0].text).toBe('hello');
    });
  });

  describe('Regex Support', () => {
    it('should support regex patterns', () => {
      const lines = createLines(['test123', 'abc456', 'xyz789']);

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('\\d+'); // Match digits
        result.current.setOptions({ caseSensitive: false, useRegex: true });
      });

      expect(result.current.totalMatches).toBe(3);
    });

    it('should handle invalid regex gracefully', () => {
      const lines = createLines(['test']);

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('[invalid'); // Invalid regex
        result.current.setOptions({ caseSensitive: false, useRegex: true });
      });

      // Should not throw, should return empty matches
      expect(result.current.totalMatches).toBe(0);
    });
  });

  describe('Navigation', () => {
    it('should navigate to next match', () => {
      const lines = createLines(['test', 'test', 'test']);

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('test');
      });

      expect(result.current.currentMatchIndex).toBe(0);

      act(() => {
        result.current.nextMatch();
      });

      expect(result.current.currentMatchIndex).toBe(1);

      act(() => {
        result.current.nextMatch();
      });

      expect(result.current.currentMatchIndex).toBe(2);
    });

    it('should wrap around when navigating past last match', () => {
      const lines = createLines(['test', 'test']);

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('test');
      });

      act(() => {
        result.current.nextMatch();
        result.current.nextMatch();
      });

      // Should wrap to first match
      expect(result.current.currentMatchIndex).toBe(0);
    });

    it('should navigate to previous match', () => {
      const lines = createLines(['test', 'test', 'test']);

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('test');
      });

      act(() => {
        result.current.nextMatch();
        result.current.nextMatch();
      });

      expect(result.current.currentMatchIndex).toBe(2);

      act(() => {
        result.current.prevMatch();
      });

      expect(result.current.currentMatchIndex).toBe(1);
    });

    it('should wrap around when navigating before first match', () => {
      const lines = createLines(['test', 'test']);

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('test');
      });

      act(() => {
        result.current.prevMatch();
      });

      // Should wrap to last match
      expect(result.current.currentMatchIndex).toBe(1);
    });
  });

  describe('Clear Search', () => {
    it('should clear search query and reset state', () => {
      const lines = createLines(['test']);

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('test');
        result.current.nextMatch();
      });

      expect(result.current.searchQuery).toBe('test');
      expect(result.current.totalMatches).toBe(1);

      act(() => {
        result.current.clearSearch();
      });

      expect(result.current.searchQuery).toBe('');
      expect(result.current.totalMatches).toBe(0);
      expect(result.current.currentMatchIndex).toBe(0);
    });
  });

  describe('Multiple Matches Per Line', () => {
    it('should find multiple matches in same line', () => {
      const lines = createLines(['test test test']);

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('test');
      });

      expect(result.current.totalMatches).toBe(3);
      expect(result.current.matches.every(m => m.lineIndex === 0)).toBe(true);
    });

    it('should track correct positions for multiple matches', () => {
      const lines = createLines(['abc abc abc']);

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('abc');
      });

      const matches = result.current.matches;
      expect(matches[0].startIndex).toBe(0);
      expect(matches[1].startIndex).toBe(4);
      expect(matches[2].startIndex).toBe(8);
    });
  });

  describe('Highlighting', () => {
    it('should provide highlighted lines', () => {
      const lines = createLines(['Hello World']);

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('Hello');
      });

      expect(result.current.highlightedLines).toHaveLength(1);
      expect(result.current.highlightedLines[0]).toBeDefined();
    });

    it('should provide current match for scrolling', () => {
      const lines = createLines(['line 1', 'line 2', 'line 3']);

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('line');
      });

      expect(result.current.currentMatch).toBeDefined();
      expect(result.current.currentMatch?.lineIndex).toBe(0);

      act(() => {
        result.current.nextMatch();
      });

      expect(result.current.currentMatch?.lineIndex).toBe(1);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty lines array', () => {
      const lines: TerminalLine[] = [];

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('test');
      });

      expect(result.current.totalMatches).toBe(0);
    });

    it('should handle special regex characters in plain text search', () => {
      const lines = createLines(['test.* [abc] (foo)']);

      const { result } = renderHook(() => useTerminalSearch(lines));

      act(() => {
        result.current.setSearchQuery('.*');
        result.current.setOptions({ caseSensitive: false, useRegex: false });
      });

      // Should escape regex special chars in plain text mode
      expect(result.current.totalMatches).toBe(1);
    });

    it('should update matches when lines change', () => {
      const { result, rerender } = renderHook(
        ({ lines }) => useTerminalSearch(lines),
        {
          initialProps: { lines: createLines(['test']) },
        }
      );

      act(() => {
        result.current.setSearchQuery('test');
      });

      expect(result.current.totalMatches).toBe(1);

      // Update lines
      rerender({ lines: createLines(['test', 'test']) });

      expect(result.current.totalMatches).toBe(2);
    });
  });
});
