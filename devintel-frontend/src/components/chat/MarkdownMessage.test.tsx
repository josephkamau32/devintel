import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MarkdownMessage } from './MarkdownMessage';

describe('MarkdownMessage', () => {
  it('renders "### Title", inline code, and renders HTML tags like <script> as plain text without executing or creating DOM elements', () => {
    const content = '### Title\n\nHere is `code` and <script>alert("xss")</script>';
    const { container } = render(<MarkdownMessage content={content} />);

    // 1. Heading level 3 is rendered as a heading element with text "Title"
    const heading = screen.getByRole('heading', { level: 3, name: 'Title' });
    expect(heading).toBeInTheDocument();
    expect(heading.tagName).toBe('H3');

    // 2. Inline `code` is rendered in a <code> element with styling and wrap classes
    const codeElement = container.querySelector('code');
    expect(codeElement).not.toBeNull();
    expect(codeElement?.textContent).toBe('code');
    expect(codeElement?.className).toContain('break-words');
    expect(codeElement?.className).toContain('break-all');

    // 3. HTML tag <script> is NOT rendered as an HTML script element
    const scriptElement = container.querySelector('script');
    expect(scriptElement).toBeNull();

    // 4. The raw tag text is shown safely as plain text in the output
    expect(container.textContent).toContain('<script>alert("xss")</script>');
  });

  it('renders fenced code blocks and handles unclosed code fence mid-stream gracefully without errors', () => {
    // Complete fenced code block
    const fullBlock = '```python\ndef hello():\n    return "world"\n```';
    const { container: fullContainer } = render(<MarkdownMessage content={fullBlock} />);
    const preElement = fullContainer.querySelector('pre');
    expect(preElement).not.toBeNull();
    expect(preElement?.textContent).toContain('def hello():');

    // Partial / unclosed code fence mid-stream (e.g. streaming LLM output)
    const partialStream = 'Here is the function:\n\n```python\ndef calculate_score(x):\n    # streaming in progress';
    const { container: partialContainer } = render(<MarkdownMessage content={partialStream} />);
    const partialPre = partialContainer.querySelector('pre');
    expect(partialPre).not.toBeNull();
    expect(partialPre?.textContent).toContain('def calculate_score(x):');
    expect(partialContainer.textContent).toContain('Here is the function:');
  });

  it('renders lists, blockquotes, and links properly', () => {
    const markdown = '- item 1\n- item 2\n\n> Important quote\n\n[Devintel](https://devintel.dev)';
    const { container } = render(<MarkdownMessage content={markdown} />);

    expect(screen.getByText('item 1')).toBeInTheDocument();
    expect(screen.getByText('item 2')).toBeInTheDocument();
    expect(container.querySelector('blockquote')).not.toBeNull();
    expect(container.querySelector('blockquote')?.textContent).toContain('Important quote');

    const link = screen.getByRole('link', { name: 'Devintel' });
    expect(link).toHaveAttribute('href', 'https://devintel.dev');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });
});
