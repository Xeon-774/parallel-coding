/**
 * Tests for SearchBar component
 * Phase 2.2 Feature 1
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { SearchBar } from '../SearchBar';
import type { SearchOptions } from '../SearchBar';

describe('SearchBar', () => {
  const defaultProps = {
    onSearch: jest.fn(),
    matchCount: 0,
    currentMatch: 0,
    onNext: jest.fn(),
    onPrevious: jest.fn(),
    onClear: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render search input', () => {
      render(<SearchBar {...defaultProps} />);

      const input = screen.getByPlaceholderText(/search terminal output/i);
      expect(input).toBeInTheDocument();
    });

    it('should render case-sensitive toggle', () => {
      render(<SearchBar {...defaultProps} />);

      const checkbox = screen.getByLabelText(/case sensitive/i);
      expect(checkbox).toBeInTheDocument();
    });

    it('should render regex toggle', () => {
      render(<SearchBar {...defaultProps} />);

      const checkbox = screen.getByLabelText(/use regex/i);
      expect(checkbox).toBeInTheDocument();
    });

    it('should render navigation buttons', () => {
      render(<SearchBar {...defaultProps} />);

      const prevButton = screen.getByLabelText(/previous match/i);
      const nextButton = screen.getByLabelText(/next match/i);

      expect(prevButton).toBeInTheDocument();
      expect(nextButton).toBeInTheDocument();
    });
  });

  describe('Search Input', () => {
    it('should call onSearch when typing in input', () => {
      render(<SearchBar {...defaultProps} />);

      const input = screen.getByPlaceholderText(/search terminal output/i);
      fireEvent.change(input, { target: { value: 'test' } });

      expect(defaultProps.onSearch).toHaveBeenCalledWith('test', {
        caseSensitive: false,
        useRegex: false,
      });
    });

    it('should show clear button when query exists', () => {
      render(<SearchBar {...defaultProps} />);

      const input = screen.getByPlaceholderText(/search terminal output/i);
      fireEvent.change(input, { target: { value: 'test' } });

      const clearButton = screen.getByLabelText(/clear search/i);
      expect(clearButton).toBeInTheDocument();
    });

    it('should clear search when clear button clicked', () => {
      render(<SearchBar {...defaultProps} />);

      const input = screen.getByPlaceholderText(/search terminal output/i);
      fireEvent.change(input, { target: { value: 'test' } });

      const clearButton = screen.getByLabelText(/clear search/i);
      fireEvent.click(clearButton);

      expect(defaultProps.onClear).toHaveBeenCalled();
    });
  });

  describe('Case-Sensitive Toggle', () => {
    it('should update case sensitivity when toggled', () => {
      render(<SearchBar {...defaultProps} />);

      const input = screen.getByPlaceholderText(/search terminal output/i);
      const checkbox = screen.getByLabelText(/case sensitive/i);

      // Type query first
      fireEvent.change(input, { target: { value: 'test' } });

      // Toggle case sensitivity
      fireEvent.click(checkbox);

      expect(defaultProps.onSearch).toHaveBeenCalledWith('test', {
        caseSensitive: true,
        useRegex: false,
      });
    });
  });

  describe('Regex Toggle', () => {
    it('should update regex mode when toggled', () => {
      render(<SearchBar {...defaultProps} />);

      const input = screen.getByPlaceholderText(/search terminal output/i);
      const checkbox = screen.getByLabelText(/use regex/i);

      // Type query first
      fireEvent.change(input, { target: { value: '\\d+' } });

      // Toggle regex
      fireEvent.click(checkbox);

      expect(defaultProps.onSearch).toHaveBeenCalledWith('\\d+', {
        caseSensitive: false,
        useRegex: true,
      });
    });
  });

  describe('Match Counter', () => {
    it('should display match count when query exists', () => {
      render(
        <SearchBar
          {...defaultProps}
          matchCount={12}
          currentMatch={3}
        />
      );

      const input = screen.getByPlaceholderText(/search terminal output/i);
      fireEvent.change(input, { target: { value: 'test' } });

      expect(screen.getByText('3 of 12')).toBeInTheDocument();
    });

    it('should show "0 matches" when no matches found', () => {
      render(
        <SearchBar
          {...defaultProps}
          matchCount={0}
          currentMatch={0}
        />
      );

      const input = screen.getByPlaceholderText(/search terminal output/i);
      fireEvent.change(input, { target: { value: 'test' } });

      expect(screen.getByText('0 matches')).toBeInTheDocument();
    });

    it('should not display counter when query is empty', () => {
      render(<SearchBar {...defaultProps} />);

      expect(screen.queryByText(/of/)).not.toBeInTheDocument();
    });
  });

  describe('Navigation Buttons', () => {
    it('should call onNext when next button clicked', () => {
      render(
        <SearchBar
          {...defaultProps}
          matchCount={5}
          currentMatch={2}
        />
      );

      const nextButton = screen.getByLabelText(/next match/i);
      fireEvent.click(nextButton);

      expect(defaultProps.onNext).toHaveBeenCalled();
    });

    it('should call onPrevious when previous button clicked', () => {
      render(
        <SearchBar
          {...defaultProps}
          matchCount={5}
          currentMatch={2}
        />
      );

      const prevButton = screen.getByLabelText(/previous match/i);
      fireEvent.click(prevButton);

      expect(defaultProps.onPrevious).toHaveBeenCalled();
    });

    it('should disable navigation buttons when no matches', () => {
      render(
        <SearchBar
          {...defaultProps}
          matchCount={0}
          currentMatch={0}
        />
      );

      const nextButton = screen.getByLabelText(/next match/i);
      const prevButton = screen.getByLabelText(/previous match/i);

      expect(nextButton).toBeDisabled();
      expect(prevButton).toBeDisabled();
    });

    it('should enable navigation buttons when matches exist', () => {
      render(
        <SearchBar
          {...defaultProps}
          matchCount={3}
          currentMatch={1}
        />
      );

      const nextButton = screen.getByLabelText(/next match/i);
      const prevButton = screen.getByLabelText(/previous match/i);

      expect(nextButton).not.toBeDisabled();
      expect(prevButton).not.toBeDisabled();
    });
  });

  describe('Combined Options', () => {
    it('should handle both case-sensitive and regex enabled', () => {
      render(<SearchBar {...defaultProps} />);

      const input = screen.getByPlaceholderText(/search terminal output/i);
      const caseCheckbox = screen.getByLabelText(/case sensitive/i);
      const regexCheckbox = screen.getByLabelText(/use regex/i);

      // Type query
      fireEvent.change(input, { target: { value: 'Test' } });

      // Enable both options
      fireEvent.click(caseCheckbox);
      fireEvent.click(regexCheckbox);

      expect(defaultProps.onSearch).toHaveBeenLastCalledWith('Test', {
        caseSensitive: true,
        useRegex: true,
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<SearchBar {...defaultProps} />);

      expect(screen.getByLabelText(/search terminal output/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/case sensitive/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/use regex/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/next match/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/previous match/i)).toBeInTheDocument();
    });
  });
});
