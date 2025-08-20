import React from 'react';
import { render, screen } from '@testing-library/react';
import { Message } from '../Message';

describe('Message Component', () => {
  const mockMessage = {
    id: '1',
    content: 'Hello world',
    sender: 'user',
    timestamp: new Date('2025-01-01T12:00:00Z'),
    isEdited: false,
    reactions: [],
  };

  const mockOtherMessage = {
    ...mockMessage,
    id: '2',
    sender: 'assistant',
    content: 'Hello! How can I help you today?',
  };

  it('renders user message correctly', () => {
    render(<Message message={mockMessage} isCurrentUser={true} />);
    expect(screen.getByText('Hello world')).toBeInTheDocument();
    expect(screen.getByText('You')).toBeInTheDocument();
  });

  it('renders other user message correctly', () => {
    render(<Message message={mockOtherMessage} isCurrentUser={false} />);
    expect(screen.getByText('Hello! How can I help you today?')).toBeInTheDocument();
    expect(screen.getByText('Assistant')).toBeInTheDocument();
  });

  it('shows timestamp', () => {
    render(<Message message={mockMessage} isCurrentUser={true} />);
    expect(screen.getByText('12:00 PM')).toBeInTheDocument();
  });

  it('shows edited indicator when message is edited', () => {
    const editedMessage = { ...mockMessage, isEdited: true };
    render(<Message message={editedMessage} isCurrentUser={true} />);
    expect(screen.getByText('(edited)')).toBeInTheDocument();
  });

  it('does not show edited indicator when message is not edited', () => {
    render(<Message message={mockMessage} isCurrentUser={true} />);
    expect(screen.queryByText('(edited)')).not.toBeInTheDocument();
  });

  it('applies different styling for current user vs other user', () => {
    const { rerender } = render(<Message message={mockMessage} isCurrentUser={true} />);
    const userMessageContainer = screen.getByText('Hello world').closest('div');
    const initialClasses = userMessageContainer?.className;

    rerender(<Message message={mockOtherMessage} isCurrentUser={false} />);
    const otherMessageContainer = screen.getByText('Hello! How can I help you today?').closest('div');
    const otherClasses = otherMessageContainer?.className;

    expect(initialClasses).not.toBe(otherClasses);
  });

  it('handles message with markdown content', () => {
    const markdownMessage = {
      ...mockMessage,
      content: '**Bold text** and *italic text*',
    };
    render(<Message message={markdownMessage} isCurrentUser={true} />);
    expect(screen.getByText('Bold text')).toBeInTheDocument();
    expect(screen.getByText('italic text')).toBeInTheDocument();
  });

  it('handles message with code blocks', () => {
    const codeMessage = {
      ...mockMessage,
      content: '```javascript\nconsole.log("Hello");\n```',
    };
    render(<Message message={codeMessage} isCurrentUser={true} />);
    expect(screen.getByText('console.log("Hello");')).toBeInTheDocument();
  });

  it('handles message with reactions', () => {
    const messageWithReactions = {
      ...mockMessage,
      reactions: [
        { emoji: '👍', count: 3, users: ['user1', 'user2', 'user3'] },
        { emoji: '❤️', count: 1, users: ['user1'] },
      ],
    };
    render(<Message message={messageWithReactions} isCurrentUser={true} />);
    expect(screen.getByText('👍')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('❤️')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('handles empty message content', () => {
    const emptyMessage = { ...mockMessage, content: '' };
    render(<Message message={emptyMessage} isCurrentUser={true} />);
    const messageContainer = screen.getByText('You').closest('div');
    expect(messageContainer).toBeInTheDocument();
  });

  it('handles message with only whitespace', () => {
    const whitespaceMessage = { ...mockMessage, content: '   ' };
    render(<Message message={whitespaceMessage} isCurrentUser={true} />);
    const messageContainer = screen.getByText('You').closest('div');
    expect(messageContainer).toBeInTheDocument();
  });

  it('handles very long messages', () => {
    const longMessage = {
      ...mockMessage,
      content: 'This is a very long message that should wrap properly and not break the layout. '.repeat(20),
    };
    render(<Message message={longMessage} isCurrentUser={true} />);
    expect(screen.getByText(/This is a very long message/)).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<Message message={mockMessage} isCurrentUser={true} className="custom-message" />);
    const messageContainer = screen.getByText('Hello world').closest('div');
    expect(messageContainer).toHaveClass('custom-message');
  });

  it('calls onMessageClick when message is clicked', () => {
    const mockOnMessageClick = jest.fn();
    render(
      <Message
        message={mockMessage}
        isCurrentUser={true}
        onMessageClick={mockOnMessageClick}
      />
    );
    const messageContent = screen.getByText('Hello world');
    fireEvent.click(messageContent);
    expect(mockOnMessageClick).toHaveBeenCalledWith(mockMessage);
  });

  it('calls onReactionClick when reaction is clicked', () => {
    const mockOnReactionClick = jest.fn();
    const messageWithReactions = {
      ...mockMessage,
      reactions: [{ emoji: '👍', count: 1, users: ['user1'] }],
    };
    render(
      <Message
        message={messageWithReactions}
        isCurrentUser={true}
        onReactionClick={mockOnReactionClick}
      />
    );
    const reactionButton = screen.getByText('👍');
    fireEvent.click(reactionButton);
    expect(mockOnReactionClick).toHaveBeenCalledWith('👍', mockMessage.id);
  });

  it('shows message status indicators', () => {
    const sentMessage = { ...mockMessage, status: 'sent' as const };
    const deliveredMessage = { ...mockMessage, status: 'delivered' as const };
    const readMessage = { ...mockMessage, status: 'read' as const };

    const { rerender } = render(<Message message={sentMessage} isCurrentUser={true} />);
    expect(screen.getByTestId('message-status')).toHaveAttribute('data-status', 'sent');

    rerender(<Message message={deliveredMessage} isCurrentUser={true} />);
    expect(screen.getByTestId('message-status')).toHaveAttribute('data-status', 'delivered');

    rerender(<Message message={readMessage} isCurrentUser={true} />);
    expect(screen.getByTestId('message-status')).toHaveAttribute('data-status', 'read');
  });
});
