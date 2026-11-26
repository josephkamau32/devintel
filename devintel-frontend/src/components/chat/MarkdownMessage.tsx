import { memo } from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import { clsx } from 'clsx';

interface MarkdownMessageProps {
  content: string;
  className?: string;
}

const markdownComponents: Components = {
  // Headings
  h1: ({ children }) => (
    <h1 className="text-base font-bold text-text-primary mt-3 mb-1.5 first:mt-0">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-sm font-bold text-text-primary mt-3 mb-1.5 first:mt-0">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-sm font-semibold text-text-primary mt-2.5 mb-1 first:mt-0">
      {children}
    </h3>
  ),
  h4: ({ children }) => (
    <h4 className="text-xs font-semibold text-text-secondary mt-2 mb-1 first:mt-0">
      {children}
    </h4>
  ),
  h5: ({ children }) => (
    <h5 className="text-xs font-semibold text-text-secondary mt-1.5 mb-0.5 first:mt-0">
      {children}
    </h5>
  ),
  h6: ({ children }) => (
    <h6 className="text-xs font-medium text-text-tertiary mt-1 mb-0.5 first:mt-0">
      {children}
    </h6>
  ),

  // Paragraphs
  p: ({ children }) => (
    <p className="text-sm leading-relaxed mb-2.5 last:mb-0 break-words">
      {children}
    </p>
  ),

  // Lists
  ul: ({ children }) => (
    <ul className="list-disc list-outside pl-5 mb-2.5 space-y-1 text-sm">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal list-outside pl-5 mb-2.5 space-y-1 text-sm">
      {children}
    </ol>
  ),
  li: ({ children }) => (
    <li className="leading-relaxed break-words">{children}</li>
  ),

  // Blockquotes
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-brand-500/60 pl-3.5 my-2.5 text-text-secondary italic text-sm">
      {children}
    </blockquote>
  ),

  // Links
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-brand-400 hover:text-brand-300 underline underline-offset-2 break-all"
    >
      {children}
    </a>
  ),

  // Tables
  table: ({ children }) => (
    <div className="overflow-x-auto my-3 max-w-full rounded-lg border border-border/60">
      <table className="min-w-full divide-y divide-border text-xs text-left">
        {children}
      </table>
    </div>
  ),
  th: ({ children }) => (
    <th className="px-3 py-2 font-semibold text-text-secondary bg-surface-4">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="px-3 py-2 border-t border-border/40 text-text-primary">
      {children}
    </td>
  ),

  // Horizontal Rule
  hr: () => <hr className="border-border/60 my-3.5" />,

  // Code & Pre
  pre: ({ children, ...props }) => (
    <pre
      className="bg-surface-2 border border-border/70 rounded-lg p-3.5 my-3 overflow-x-auto text-xs font-mono text-text-primary max-w-full leading-relaxed"
      {...props}
    >
      {children}
    </pre>
  ),
  code: ({ node, className, children, ...props }) => {
    const isBlock =
      Boolean(className) ||
      (node?.position ? node.position.start.line !== node.position.end.line : false) ||
      String(children).includes('\n');

    if (isBlock) {
      return (
        <code className={clsx('font-mono text-xs text-text-primary', className)} {...props}>
          {children}
        </code>
      );
    }

    return (
      <code
        className="px-1.5 py-0.5 mx-0.5 rounded bg-surface-2 border border-border/60 font-mono text-xs text-brand-300 break-words break-all"
        {...props}
      >
        {children}
      </code>
    );
  },

  // Strong & Emphasis
  strong: ({ children }) => (
    <strong className="font-semibold text-text-primary">{children}</strong>
  ),
  em: ({ children }) => (
    <em className="italic text-text-secondary">{children}</em>
  ),
};

export const MarkdownMessage = memo(function MarkdownMessage({
  content,
  className,
}: MarkdownMessageProps) {
  return (
    <div className={clsx('markdown-content text-sm leading-relaxed text-text-primary break-words', className)}>
      <ReactMarkdown components={markdownComponents}>
        {content}
      </ReactMarkdown>
    </div>
  );
});
