import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInput } from '../ChatInput';

describe('ChatInput Component', () => {
  const mockOnSendMessage = jest.fn();
  const mockOnTyping = jest.fn();

  beforeEach(() => {
    mockOnSendMessage.mockClear();
    mockOnTyping.mockClear();
  });

  it('renders ChatInput with default props', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} />);
    expect(screen.getByPlaceholderText('Type a message...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('handles message sending', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} />);
    const input = screen.getByPlaceholderText('Type a message...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Hello world' } });
    fireEvent.click(sendButton);

    expect(mockOnSendMessage).toHaveBeenCalledWith('Hello world');
    expect(input).toHaveValue('');
  });

  it('handles Enter key to send message', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} />);
    const input = screen.getByPlaceholderText('Type a message...');

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message');
    expect(input).toHaveValue('');
  });

  it('handles Shift+Enter for new line', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} />);
    const input = screen.getByPlaceholderText('Type a message...');

    fireEvent.change(input, { target: { value: 'Line 1' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter', shiftKey: true });

    expect(mockOnSendMessage).not.toHaveBeenCalled();
    expect(input).toHaveValue('Line 1\n');
  });

  it('disables send button when input is empty', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} />);
    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeDisabled();
  });

  it('enables send button when input has text', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} />);
    const input = screen.getByPlaceholderText('Type a message...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Hello' } });
    expect(sendButton).not.toBeDisabled();
  });

  it('calls onTyping callback when typing', () => {
    jest.useFakeTimers();
    render(<ChatInput onSendMessage={mockOnSendMessage} onTyping={mockOnTyping} />);
    const input = screen.getByPlaceholderText('Type a message...');

    fireEvent.change(input, { target: { value: 'H' } });
    fireEvent.change(input, { target: { value: 'He' } });
    fireEvent.change(input, { target: { value: 'Hel' } });

    jest.advanceTimersByTime(1000);
    expect(mockOnTyping).toHaveBeenCalled();

    jest.useRealTimers();
  });

  it('applies custom className', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} className="custom-input" />);
    const container = screen.getByPlaceholderText('Type a message...').closest('div');
    expect(container).toHaveClass('custom-input');
  });

  it('shows character limit when provided', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} maxLength={100} />);
    expect(screen.getByText(/0\/100/)).toBeInTheDocument();
  });

  it('updates character count as user types', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} maxLength={100} />);
    const input = screen.getByPlaceholderText('Type a message...');

    fireEvent.change(input, { target: { value: 'Hello' } });
    expect(screen.getByText('5/100')).toBeInTheDocument();
  });

  it('prevents sending when character limit is exceeded', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} maxLength={5} />);
    const input = screen.getByPlaceholderText('Type a message...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Too long message' } });
    fireEvent.click(sendButton);

    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });

  it('handles disabled state', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} disabled />);
    const input = screen.getByPlaceholderText('Type a message...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  it('shows placeholder text when provided', () => {
    render(<ChatInput onSendMessage={mockOnSendMessage} placeholder="Custom placeholder" />);
    expect(screen.getByPlaceholderText('Custom placeholder')).toBeInTheDocument();
  });
});
