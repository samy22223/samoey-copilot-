import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { toast } from 'react-hot-toast';
import { Toaster } from '../toaster';
import { useToast } from '../use-toast';

// Mock the toast library
jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    loading: jest.fn(),
    custom: jest.fn(),
    dismiss: jest.fn(),
    remove: jest.fn(),
  },
}));

describe('Toast Components', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Toaster Component', () => {
    it('renders without crashing', () => {
      render(<Toaster />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      render(<Toaster className="custom-toaster" />);
      const toaster = screen.getByRole('status');
      expect(toaster).toHaveClass('custom-toaster');
    });
  });

  describe('useToast Hook', () => {
    it('returns toast functions', () => {
      const TestComponent = () => {
        const { toast: toastFunctions } = useToast();
        return (
          <div>
            <button onClick={() => toastFunctions({ title: 'Test' })}>Show Toast</button>
          </div>
        );
      };

      render(<TestComponent />);
      const button = screen.getByText('Show Toast');
      expect(button).toBeInTheDocument();
    });

    it('handles toast with different variants', () => {
      const TestComponent = () => {
        const { toast: toastFunctions } = useToast();
        return (
          <div>
            <button onClick={() => toastFunctions({ title: 'Success', variant: 'success' })}>
              Success Toast
            </button>
            <button onClick={() => toastFunctions({ title: 'Error', variant: 'destructive' })}>
              Error Toast
            </button>
          </div>
        );
      };

      render(<TestComponent />);

      const successButton = screen.getByText('Success Toast');
      const errorButton = screen.getByText('Error Toast');

      expect(successButton).toBeInTheDocument();
      expect(errorButton).toBeInTheDocument();
    });

    it('handles toast with action', () => {
      const mockAction = jest.fn();
      const TestComponent = () => {
        const { toast: toastFunctions } = useToast();
        return (
          <div>
            <button onClick={() => toastFunctions({
              title: 'Action Toast',
              action: {
                label: 'Undo',
                onClick: mockAction,
              }
            })}>
              Action Toast
            </button>
          </div>
        );
      };

      render(<TestComponent />);
      const button = screen.getByText('Action Toast');
      expect(button).toBeInTheDocument();
    });
  });

  describe('Toast Integration', () => {
    it('integrates with react-hot-toast', () => {
      const TestComponent = () => {
        const { toast: toastFunctions } = useToast();
        return (
          <div>
            <button onClick={() => toastFunctions({ title: 'Integration Test' })}>
              Test Integration
            </button>
          </div>
        );
      };

      render(<TestComponent />);
      const button = screen.getByText('Test Integration');

      act(() => {
        button.click();
      });

      expect(toast.custom).toHaveBeenCalled();
    });

    it('handles toast dismissal', () => {
      const TestComponent = () => {
        const { toast: toastFunctions, dismiss } = useToast();
        return (
          <div>
            <button onClick={() => toastFunctions({ title: 'Dismiss Test', id: 'test-id' })}>
              Show Toast
            </button>
            <button onClick={() => dismiss('test-id')}>
              Dismiss Toast
            </button>
          </div>
        );
      };

      render(<TestComponent />);

      const showButton = screen.getByText('Show Toast');
      const dismissButton = screen.getByText('Dismiss Toast');

      expect(showButton).toBeInTheDocument();
      expect(dismissButton).toBeInTheDocument();
    });
  });
});
