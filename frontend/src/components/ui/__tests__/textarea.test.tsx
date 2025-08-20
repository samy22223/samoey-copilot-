import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Textarea } from '../textarea';

describe('Textarea Component', () => {
  const mockOnChange = jest.fn();
  const mockOnValueChange = jest.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
    mockOnValueChange.mockClear();
  });

  it('renders textarea with default props', () => {
    render(<Textarea />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toBeInTheDocument();
    expect(textarea).toHaveClass('flex', 'min-h-[80px]', 'w-full', 'rounded-md', 'border', 'border-input', 'bg-background', 'px-3', 'py-2', 'text-sm', 'ring-offset-background', 'placeholder:text-muted-foreground', 'focus-visible:outline-none', 'focus-visible:ring-2', 'focus-visible:ring-ring', 'focus-visible:ring-offset-2', 'disabled:cursor-not-allowed', 'disabled:opacity-50');
  });

  it('handles value changes', () => {
    render(<Textarea onChange={mockOnChange} />);
    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: 'test content' } });
    expect(mockOnChange).toHaveBeenCalledTimes(1);
  });

  it('handles onValueChange callback', () => {
    render(<Textarea onValueChange={mockOnValueChange} />);
    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: 'test content' } });
    expect(mockOnValueChange).toHaveBeenCalledWith('test content');
  });

  it('applies custom className', () => {
    render(<Textarea className="custom-textarea" />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('custom-textarea');
  });

  it('is disabled when disabled prop is true', () => {
    render(<Textarea disabled />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toBeDisabled();
    expect(textarea).toHaveClass('disabled:cursor-not-allowed', 'disabled:opacity-50');
  });

  it('shows placeholder text', () => {
    render(<Textarea placeholder="Enter your text here" />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('placeholder', 'Enter your text here');
  });

  it('accepts default value', () => {
    render(<Textarea defaultValue="Default text" />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveValue('Default text');
  });

  it('accepts controlled value', () => {
    render(<Textarea value="Controlled text" onChange={mockOnChange} />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveValue('Controlled text');
  });

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLTextAreaElement>();
    render(<Textarea ref={ref} />);
    expect(ref.current).toBeInstanceOf(HTMLTextAreaElement);
  });

  it('applies custom attributes', () => {
    render(<Textarea maxLength={100} rows={4} />);
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('maxlength', '100');
    expect(textarea).toHaveAttribute('rows', '4');
  });

  it('does not trigger onChange when disabled', () => {
    render(<Textarea onChange={mockOnChange} disabled />);
    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: 'test content' } });
    expect(mockOnChange).not.toHaveBeenCalled();
  });
});
