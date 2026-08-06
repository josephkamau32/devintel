import { forwardRef, InputHTMLAttributes } from 'react';
import { clsx } from 'clsx';
import { AlertCircle } from 'lucide-react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, className, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-body-sm font-medium text-text-secondary"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={
            error
              ? `${inputId}-error`
              : helperText
              ? `${inputId}-helper`
              : undefined
          }
          className={clsx(
            'rounded-lg border bg-surface-3 px-3.5 py-2.5 text-sm text-text-primary placeholder-text-quaternary',
            'outline-none transition-all duration-150',
            'focus:border-brand-500 focus:shadow-focus-ring',
            error
              ? 'border-status-error focus:border-status-error focus:shadow-focus-ring-error'
              : 'border-border-medium hover:border-border-strong',
            className,
          )}
          {...props}
        />
        {error && (
          <p
            id={`${inputId}-error`}
            role="alert"
            className="flex items-center gap-1.5 text-xs text-status-error"
          >
            <AlertCircle className="h-3 w-3 shrink-0" />
            {error}
          </p>
        )}
        {!error && helperText && (
          <p
            id={`${inputId}-helper`}
            className="text-xs text-text-tertiary"
          >
            {helperText}
          </p>
        )}
      </div>
    );
  },
);
Input.displayName = 'Input';
