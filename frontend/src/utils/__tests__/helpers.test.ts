import {
  formatRelativeTime,
  truncate,
  formatFileSize,
  generateId,
  isEmpty,
  deepClone,
  debounce,
  throttle,
  formatCurrency,
  getRandomColor,
  copyToClipboard
} from '../helpers';

describe('Helper Functions', () => {
  describe('formatRelativeTime', () => {
    beforeEach(() => {
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2025-01-01T12:00:00.000Z'));
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('shows "just now" for recent times', () => {
      const result = formatRelativeTime('2025-01-01T11:59:30.000Z');
      expect(result).toBe('just now');
    });

    it('shows minutes for times under an hour', () => {
      const result = formatRelativeTime('2025-01-01T11:45:00.000Z');
      expect(result).toBe('15 minutes ago');
    });

    it('shows hours for times under a day', () => {
      const result = formatRelativeTime('2025-01-01T09:00:00.000Z');
      expect(result).toBe('3 hours ago');
    });

    it('shows days for times under a week', () => {
      const result = formatRelativeTime('2024-12-30T12:00:00.000Z');
      expect(result).toBe('2 days ago');
    });

    it('shows weeks for times under a month', () => {
      const result = formatRelativeTime('2024-12-18T12:00:00.000Z');
      expect(result).toBe('2 weeks ago');
    });

    it('shows months for times under a year', () => {
      const result = formatRelativeTime('2024-11-01T12:00:00.000Z');
      expect(result).toBe('2 months ago');
    });

    it('shows years for times over a year', () => {
      const result = formatRelativeTime('2023-01-01T12:00:00.000Z');
      expect(result).toBe('2 years ago');
    });

    it('handles singular forms correctly', () => {
      expect(formatRelativeTime('2025-01-01T11:59:00.000Z')).toBe('1 minute ago');
      expect(formatRelativeTime('2025-01-01T11:00:00.000Z')).toBe('1 hour ago');
      expect(formatRelativeTime('2024-12-31T12:00:00.000Z')).toBe('1 day ago');
      expect(formatRelativeTime('2024-12-25T12:00:00.000Z')).toBe('1 week ago');
      expect(formatRelativeTime('2024-12-01T12:00:00.000Z')).toBe('1 month ago');
      expect(formatRelativeTime('2024-01-01T12:00:00.000Z')).toBe('1 year ago');
    });
  });

  describe('truncate', () => {
    it('returns original text if shorter than maxLength', () => {
      const text = 'Short text';
      expect(truncate(text, 20)).toBe(text);
    });

    it('truncates text longer than maxLength', () => {
      const text = 'This is a very long text that should be truncated';
      expect(truncate(text, 20)).toBe('This is a very long...');
    });

    it('handles exact maxLength', () => {
      const text = 'Exactly 20 chars!!';
      expect(truncate(text, 20)).toBe(text);
    });

    it('handles empty string', () => {
      expect(truncate('', 10)).toBe('');
    });

    it('handles maxLength of 0', () => {
      const text = 'Some text';
      expect(truncate(text, 0)).toBe('...');
    });
  });

  describe('formatFileSize', () => {
    it('formats bytes correctly', () => {
      expect(formatFileSize(0)).toBe('0 Bytes');
      expect(formatFileSize(1024)).toBe('1.00 KB');
      expect(formatFileSize(1048576)).toBe('1.00 MB');
      expect(formatFileSize(1073741824)).toBe('1.00 GB');
      expect(formatFileSize(1099511627776)).toBe('1.00 TB');
    });

    it('handles decimal values correctly', () => {
      expect(formatFileSize(1536)).toBe('1.50 KB');
      expect(formatFileSize(1572864)).toBe('1.50 MB');
    });

    it('handles small file sizes', () => {
      expect(formatFileSize(500)).toBe('500.00 Bytes');
      expect(formatFileSize(999)).toBe('999.00 Bytes');
    });
  });

  describe('generateId', () => {
    it('generates ID with default prefix', () => {
      const id = generateId();
      expect(id).toMatch(/^id-[a-z0-9]{9}$/);
    });

    it('generates ID with custom prefix', () => {
      const id = generateId('custom');
      expect(id).toMatch(/^custom-[a-z0-9]{9}$/);
    });

    it('generates unique IDs', () => {
      const id1 = generateId();
      const id2 = generateId();
      expect(id1).not.toBe(id2);
    });

    it('handles empty prefix', () => {
      const id = generateId('');
      expect(id).match(/^[a-z0-9]{9}$/);
    });
  });

  describe('isEmpty', () => {
    it('returns true for null', () => {
      expect(isEmpty(null)).toBe(true);
    });

    it('returns true for undefined', () => {
      expect(isEmpty(undefined)).toBe(true);
    });

    it('returns true for empty string', () => {
      expect(isEmpty('')).toBe(true);
    });

    it('returns true for whitespace string', () => {
      expect(isEmpty('   ')).toBe(true);
    });

    it('returns true for empty array', () => {
      expect(isEmpty([])).toBe(true);
    });

    it('returns true for empty object', () => {
      expect(isEmpty({})).toBe(true);
    });

    it('returns false for non-empty string', () => {
      expect(isEmpty('hello')).toBe(false);
    });

    it('returns false for non-empty array', () => {
      expect(isEmpty([1, 2, 3])).toBe(false);
    });

    it('returns false for non-empty object', () => {
      expect(isEmpty({ key: 'value' })).toBe(false);
    });

    it('returns false for zero', () => {
      expect(isEmpty(0)).toBe(false);
    });

    it('returns false for false', () => {
      expect(isEmpty(false)).toBe(false);
    });
  });

  describe('deepClone', () => {
    it('clones primitive values', () => {
      expect(deepClone(42)).toBe(42);
      expect(deepClone('hello')).toBe('hello');
      expect(deepClone(true)).toBe(true);
    });

    it('clones objects', () => {
      const obj = { a: 1, b: 'hello', c: true };
      const cloned = deepClone(obj);
      expect(cloned).toEqual(obj);
      expect(cloned).not.toBe(obj);
    });

    it('clones nested objects', () => {
      const obj = { a: { b: { c: 1 } } };
      const cloned = deepClone(obj);
      expect(cloned).toEqual(obj);
      expect(cloned.a).not.toBe(obj.a);
      expect(cloned.a.b).not.toBe(obj.a.b);
    });

    it('clones arrays', () => {
      const arr = [1, 2, { a: 3 }];
      const cloned = deepClone(arr);
      expect(cloned).toEqual(arr);
      expect(cloned).not.toBe(arr);
      expect(cloned[2]).not.toBe(arr[2]);
    });

    it('handles complex objects', () => {
      const complex = {
        name: 'Test',
        items: [1, 2, 3],
        metadata: { created: new Date().toISOString() },
        nested: { level1: { level2: 'deep' } }
      };
      const cloned = deepClone(complex);
      expect(cloned).toEqual(complex);
      expect(cloned).not.toBe(complex);
    });
  });

  describe('debounce', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('debounces function calls', () => {
      const mockFn = jest.fn();
      const debouncedFn = debounce(mockFn, 100);

      debouncedFn('arg1');
      debouncedFn('arg2');
      debouncedFn('arg3');

      expect(mockFn).not.toHaveBeenCalled();

      jest.advanceTimersByTime(100);
      expect(mockFn).toHaveBeenCalledTimes(1);
      expect(mockFn).toHaveBeenCalledWith('arg3');
    });

    it('calls function with latest arguments', () => {
      const mockFn = jest.fn();
      const debouncedFn = debounce(mockFn, 100);

      debouncedFn('first');
      jest.advanceTimersByTime(50);
      debouncedFn('second');
      jest.advanceTimersByTime(100);

      expect(mockFn).toHaveBeenCalledWith('second');
    });

    it('can be called multiple times', () => {
      const mockFn = jest.fn();
      const debouncedFn = debounce(mockFn, 100);

      debouncedFn('call1');
      jest.advanceTimersByTime(100);
      expect(mockFn).toHaveBeenCalledWith('call1');

      debouncedFn('call2');
      jest.advanceTimersByTime(100);
      expect(mockFn).toHaveBeenCalledWith('call2');
    });
  });

  describe('throttle', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('throttles function calls', () => {
      const mockFn = jest.fn();
      const throttledFn = throttle(mockFn, 100);

      throttledFn('arg1');
      throttledFn('arg2');
      throttledFn('arg3');

      expect(mockFn).toHaveBeenCalledTimes(1);
      expect(mockFn).toHaveBeenCalledWith('arg1');

      jest.advanceTimersByTime(100);
      throttledFn('arg4');
      expect(mockFn).toHaveBeenCalledTimes(2);
      expect(mockFn).toHaveBeenCalledWith('arg4');
    });

    it('ignores calls during throttle period', () => {
      const mockFn = jest.fn();
      const throttledFn = throttle(mockFn, 100);

      throttledFn('first');
      throttledFn('second');
      throttledFn('third');

      expect(mockFn).toHaveBeenCalledTimes(1);
      expect(mockFn).toHaveBeenCalledWith('first');
    });

    it('allows calls after throttle period', () => {
      const mockFn = jest.fn();
      const throttledFn = throttle(mockFn, 100);

      throttledFn('first');
      jest.advanceTimersByTime(100);
      throttledFn('second');

      expect(mockFn).toHaveBeenCalledTimes(2);
      expect(mockFn).toHaveBeenNthCalledWith(1, 'first');
      expect(mockFn).toHaveBeenNthCalledWith(2, 'second');
    });
  });

  describe('formatCurrency', () => {
    it('formats USD currency correctly', () => {
      expect(formatCurrency(1234.56)).toBe('$1,234.56');
      expect(formatCurrency(0)).toBe('$0.00');
      expect(formatCurrency(1000000)).toBe('$1,000,000.00');
    });

    it('formats different currencies', () => {
      expect(formatCurrency(1234.56, 'EUR')).toBe('€1,234.56');
      expect(formatCurrency(1234.56, 'GBP')).toBe('£1,234.56');
      expect(formatCurrency(1234.56, 'JPY')).toBe('¥1,235');
    });

    it('handles negative values', () => {
      expect(formatCurrency(-1234.56)).toBe('-$1,234.56');
    });

    it('handles decimal values correctly', () => {
      expect(formatCurrency(1234.567)).toBe('$1,234.57');
      expect(formatCurrency(1234.564)).toBe('$1,234.56');
    });
  });

  describe('getRandomColor', () => {
    it('returns a valid hex color', () => {
      const color = getRandomColor();
      expect(color).toMatch(/^#[0-9A-F]{6}$/i);
    });

    it('generates different colors', () => {
      const color1 = getRandomColor();
      const color2 = getRandomColor();
      expect(color1).not.toBe(color2);
    });

    it('always returns 7 characters (including #)', () => {
      const color = getRandomColor();
      expect(color).toHaveLength(7);
    });
  });

  describe('copyToClipboard', () => {
    beforeEach(() => {
      // Mock clipboard API
      Object.assign(navigator, {
        clipboard: {
          writeText: jest.fn().mockResolvedValue(undefined),
        },
      });
    });

    it('copies text successfully', async () => {
      const result = await copyToClipboard('test text');
      expect(result).toBe(true);
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('test text');
    });

    it('handles clipboard errors', async () => {
      const mockError = new Error('Clipboard error');
      jest.spyOn(navigator.clipboard, 'writeText').mockRejectedValue(mockError);
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      const result = await copyToClipboard('test text');
      expect(result).toBe(false);
      expect(consoleSpy).toHaveBeenCalledWith('Failed to copy text: ', mockError);

      consoleSpy.mockRestore();
    });
  });
});
