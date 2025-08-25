import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MainNav } from '../main-nav';

describe('MainNav Component', () => {
  const mockItems = [
    { title: 'Dashboard', href: '/dashboard' },
    { title: 'Chat', href: '/chat' },
    { title: 'Settings', href: '/settings' },
  ];

  it('renders navigation items', () => {
    render(<MainNav items={mockItems} />);

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Chat')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('renders navigation links with correct href', () => {
    render(<MainNav items={mockItems} />);

    const dashboardLink = screen.getByText('Dashboard').closest('a');
    const chatLink = screen.getByText('Chat').closest('a');
    const settingsLink = screen.getByText('Settings').closest('a');

    expect(dashboardLink).toHaveAttribute('href', '/dashboard');
    expect(chatLink).toHaveAttribute('href', '/chat');
    expect(settingsLink).toHaveAttribute('href', '/settings');
  });

  it('applies custom className', () => {
    render(<MainNav items={mockItems} className="custom-nav" />);
    const nav = screen.getByRole('navigation');
    expect(nav).toHaveClass('custom-nav');
  });

  it('handles empty items array', () => {
    render(<MainNav items={[]} />);
    const nav = screen.getByRole('navigation');
    expect(nav).toBeInTheDocument();
    expect(nav.children.length).toBe(0);
  });

  it('handles click events on navigation items', () => {
    const handleClick = jest.fn();
    render(<MainNav items={mockItems} onItemClick={handleClick} />);

    const chatLink = screen.getByText('Chat').closest('a');
    fireEvent.click(chatLink);

    expect(handleClick).toHaveBeenCalledWith(mockItems[1]);
  });

  it('applies active state styling', () => {
    render(<MainNav items={mockItems} activeItem="/chat" />);

    const dashboardLink = screen.getByText('Dashboard').closest('a');
    const chatLink = screen.getByText('Chat').closest('a');
    const settingsLink = screen.getByText('Settings').closest('a');

    expect(chatLink).toHaveClass('active');
    expect(dashboardLink).not.toHaveClass('active');
    expect(settingsLink).not.toHaveClass('active');
  });

  it('renders with logo when provided', () => {
    const logo = <div data-testid="logo">Logo</div>;
    render(<MainNav items={mockItems} logo={logo} />);

    expect(screen.getByTestId('logo')).toBeInTheDocument();
  });

  it('renders with user menu when provided', () => {
    const userMenu = <div data-testid="user-menu">User Menu</div>;
    render(<MainNav items={mockItems} userMenu={userMenu} />);

    expect(screen.getByTestId('user-menu')).toBeInTheDocument();
  });
});
