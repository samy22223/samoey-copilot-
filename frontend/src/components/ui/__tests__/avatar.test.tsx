import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Avatar, AvatarImage, AvatarFallback } from '../avatar';

describe('Avatar Components', () => {
  it('renders Avatar with correct classes', () => {
    render(<Avatar />);
    const avatar = screen.getByRole('img', { hidden: true });
    expect(avatar).toBeInTheDocument();
    expect(avatar).toHaveClass('relative', 'flex', 'h-10', 'w-10', 'shrink-0', 'overflow-hidden', 'rounded-full');
  });

  it('renders AvatarImage with correct attributes', () => {
    render(
      <Avatar>
        <AvatarImage src="https://example.com/avatar.jpg" alt="User avatar" />
      </Avatar>
    );
    const image = screen.getByAltText('User avatar');
    expect(image).toBeInTheDocument();
    expect(image).toHaveAttribute('src', 'https://example.com/avatar.jpg');
    expect(image).toHaveClass('aspect-square', 'h-full', 'w-full');
  });

  it('renders AvatarFallback with correct classes', () => {
    render(
      <Avatar>
        <AvatarFallback>JD</AvatarFallback>
      </Avatar>
    );
    const fallback = screen.getByText('JD');
    expect(fallback).toBeInTheDocument();
    expect(fallback).toHaveClass('flex', 'h-full', 'w-full', 'items-center', 'justify-center', 'rounded-full', 'bg-muted');
  });

  it('shows fallback when image fails to load', () => {
    const mockOnError = jest.fn();
    render(
      <Avatar>
        <AvatarImage
          src="invalid-image.jpg"
          alt="User avatar"
          onLoadingStatusChange={mockOnError}
        />
        <AvatarFallback>JD</AvatarFallback>
      </Avatar>
    );

    // Initially, image should be present
    const image = screen.getByAltText('User avatar');
    expect(image).toBeInTheDocument();

    // Simulate image error
    fireEvent.error(image);

    // Fallback should be visible
    const fallback = screen.getByText('JD');
    expect(fallback).toBeInTheDocument();
  });

  it('applies custom className to Avatar', () => {
    render(<Avatar className="custom-avatar" />);
    const avatar = screen.getByRole('img', { hidden: true });
    expect(avatar).toHaveClass('custom-avatar');
  });

  it('applies custom className to AvatarImage', () => {
    render(
      <Avatar>
        <AvatarImage
          src="https://example.com/avatar.jpg"
          className="custom-image"
        />
      </Avatar>
    );
    const image = screen.getByAltText('User avatar');
    expect(image).toHaveClass('custom-image');
  });

  it('applies custom className to AvatarFallback', () => {
    render(
      <Avatar>
        <AvatarFallback className="custom-fallback">JD</AvatarFallback>
      </Avatar>
    );
    const fallback = screen.getByText('JD');
    expect(fallback).toHaveClass('custom-fallback');
  });

  it('handles different Avatar sizes', () => {
    const { rerender } = render(<Avatar />);
    let avatar = screen.getByRole('img', { hidden: true });
    expect(avatar).toHaveClass('h-10', 'w-10');

    rerender(<Avatar size="sm" />);
    avatar = screen.getByRole('img', { hidden: true });
    expect(avatar).toHaveClass('h-8', 'w-8');

    rerender(<Avatar size="lg" />);
    avatar = screen.getByRole('img', { hidden: true });
    expect(avatar).toHaveClass('h-12', 'w-12');
  });

  it('handles shape prop', () => {
    const { rerender } = render(<Avatar />);
    let avatar = screen.getByRole('img', { hidden: true });
    expect(avatar).toHaveClass('rounded-full');

    rerender(<Avatar shape="square" />);
    avatar = screen.getByRole('img', { hidden: true });
    expect(avatar).toHaveClass('rounded-md');
  });

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLSpanElement>();
    render(<Avatar ref={ref} />);
    expect(ref.current).toBeInstanceOf(HTMLSpanElement);
  });

  it('composes Avatar components correctly with image', () => {
    render(
      <Avatar>
        <AvatarImage src="https://example.com/avatar.jpg" alt="User avatar" />
        <AvatarFallback>JD</AvatarFallback>
      </Avatar>
    );

    const image = screen.getByAltText('User avatar');
    expect(image).toBeInTheDocument();
  });

  it('composes Avatar components correctly with fallback only', () => {
    render(
      <Avatar>
        <AvatarFallback>JD</AvatarFallback>
      </Avatar>
    );

    const fallback = screen.getByText('JD');
    expect(fallback).toBeInTheDocument();
  });

  it('handles accessibility attributes', () => {
    render(
      <Avatar>
        <AvatarImage src="https://example.com/avatar.jpg" alt="User avatar" />
        <AvatarFallback>JD</AvatarFallback>
      </Avatar>
    );

    const avatar = screen.getByRole('img', { hidden: true });
    expect(avatar).toBeInTheDocument();
  });
});
