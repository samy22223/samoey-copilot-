import { cn, formatDate, absoluteUrl, formatBytes, formatTimeAgo } from '../utils';

describe('Utility Functions', () => {
  describe('cn', () => {
    it('combines class names correctly', () => {
      expect(cn('class1', 'class2')).toBe('class1 class2');
    });

    it('handles conditional classes', () => {
      const condition = true;
      expect(cn('base-class', condition && 'conditional-class')).toBe('base-class conditional-class');
    });

    it('handles undefined and null values', () => {
      expect(cn('class1', undefined, null, 'class2')).toBe('class1 class2');
    });

    it('handles empty strings', () => {
      expect(cn('class1', '', 'class2')).toBe('class1 class2');
    });

    it('handles arrays of classes', () => {
      expect(cn(['class1', 'class2'], 'class3')).toBe('class1 class2 class3');
    });

    it('handles object-based conditional classes', () => {
      expect(cn({
        'class1': true,
        'class2': false,
        'class3': true
      })).toBe('class1 class3');
    });
  });

  describe('formatDate', () => {
    it('formats date string correctly', () => {
      const result = formatDate('2025-01-01T00:00:00.000Z');
      expect(result).toContain('2025');
      expect(result).toContain('January');
      expect(result).toContain('1');
    });

    it('formats Date object correctly', () => {
      const date = new Date('2025-06-15T12:30:00.000Z');
      const result = formatDate(date);
      expect(result).toContain('2025');
      expect(result).toContain('June');
      expect(result).toContain('15');
    });

    it('formats timestamp correctly', () => {
      const timestamp = new Date('2025-12-25T00:00:00.000Z').getTime();
      const result = formatDate(timestamp);
      expect(result).toContain('2025');
      expect(result).toContain('December');
      expect(result).toContain('25');
    });

    it('handles invalid date gracefully', () => {
      const result = formatDate('invalid-date');
      expect(result).toContain('Invalid Date');
    });
  });

  describe('absoluteUrl', () => {
    beforeEach(() => {
      // Clear environment variable
      delete process.env.NEXT_PUBLIC_APP_URL;
    });

    it('uses localhost when no environment variable is set', () => {
      const result = absoluteUrl('/path');
      expect(result).toBe('http://localhost:3000/path');
    });

    it('uses environment variable when set', () => {
      process.env.NEXT_PUBLIC_APP_URL = 'https://example.com';
      const result = absoluteUrl('/path');
      expect(result).toBe('https://example.com/path');
    });

    it('handles path without leading slash', () => {
      const result = absoluteUrl('path');
      expect(result).toBe('http://localhost:3000/path');
    });

    it('handles empty path', () => {
      const result = absoluteUrl('');
      expect(result).toBe('http://localhost:3000/');
    });

    it('handles root path', () => {
      const result = absoluteUrl('/');
      expect(result).toBe('http://localhost:3000/');
    });
  });

  describe('formatBytes', () => {
    it('formats bytes correctly', () => {
      expect(formatBytes(0)).toBe('0 Bytes');
      expect(formatBytes(1024)).toBe('1 KB');
      expect(formatBytes(1048576)).toBe('1 MB');
      expect(formatBytes(1073741824)).toBe('1 GB');
      expect(formatBytes(1099511627776)).toBe('1 TB');
    });

    it('handles decimal precision', () => {
      expect(formatBytes(1536, { decimals: 2 })).toBe('1.50 KB');
      expect(formatBytes(1572864, { decimals: 3 })).toBe('1.500 MB');
    });

    it('handles binary size type', () => {
      expect(formatBytes(1024, { sizeType: 'binary' })).toBe('1 KB');
      expect(formatBytes(1048576, { sizeType: 'binary' })).toBe('1 MB');
    });

    it('handles small values', () => {
      expect(formatBytes(500)).toBe('500 Bytes');
      expect(formatBytes(999)).toBe('999 Bytes');
    });

    it('handles default options', () => {
      expect(formatBytes(2048)).toBe('2 KB');
    });

    it('handles very large numbers', () => {
      expect(formatBytes(1234567890123)).toBe('1.12 TB');
    });
  });

  describe('formatTimeAgo', () => {
    beforeEach(() => {
      // Mock current time
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2025-01-01T12:00:00.000Z'));
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('shows "just now" for recent times', () => {
      const date = new Date('2025-01-01T11:59:30.000Z'); // 30 seconds ago
      expect(formatTimeAgo(date)).toBe('just now');
    });

    it('shows minutes for times under an hour', () => {
      const date = new Date('2025-01-01T11:45:00.000Z'); // 15 minutes ago
      expect(formatTimeAgo(date)).toBe('15 minutes ago');
    });

    it('shows singular minute for one minute', () => {
      const date = new Date('2025-01-01T11:59:00.000Z'); // 1 minute ago
      expect(formatTimeAgo(date)).toBe('1 minute ago');
    });

    it('shows hours for times under a day', () => {
      const date = new Date('2025-01-01T09:00:00.000Z'); // 3 hours ago
      expect(formatTimeAgo(date)).toBe('3 hours ago');
    });

    it('shows singular hour for one hour', () => {
      const date = new Date('2025-01-01T11:00:00.000Z'); // 1 hour ago
      expect(formatTimeAgo(date)).toBe('1 hour ago');
    });

    it('shows days for times under a month', () => {
      const date = new Date('2024-12-30T12:00:00.000Z'); // 2 days ago
      expect(formatTimeAgo(date)).toBe('2 days ago');
    });

    it('shows singular day for one day', () => {
      const date = new Date('2024-12-31T12:00:00.000Z'); // 1 day ago
      expect(formatTimeAgo(date)).toBe('1 day ago');
    });

    it('shows months for times under a year', () => {
      const date = new Date('2024-11-01T12:00:00.000Z'); // 2 months ago
      expect(formatTimeAgo(date)).toBe('2 months ago');
    });

    it('shows singular month for one month', () => {
      const date = new Date('2024-12-01T12:00:00.000Z'); // 1 month ago
      expect(formatTimeAgo(date)).toBe('1 month ago');
    });

    it('shows years for times over a year', () => {
      const date = new Date('2023-01-01T12:00:00.000Z'); // 2 years ago
      expect(formatTimeAgo(date)).toBe('2 years ago');
    });

    it('shows singular year for one year', () => {
      const date = new Date('2024-01-01T12:00:00.000Z'); // 1 year ago
      expect(formatTimeAgo(date)).toBe('1 year ago');
    });

    it('handles exact time boundaries', () => {
      const date = new Date('2025-01-01T11:00:01.000Z'); // Just over 1 hour
      expect(formatTimeAgo(date)).toBe('1 hour ago');
    });
  });
});
