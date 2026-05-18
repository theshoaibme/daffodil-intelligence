import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  variant?: 'outlined' | 'standard'; // Outlined pill or standard underlined input only
  startIcon?: React.ReactNode;
  containerClassName?: string;
}

export const Input: React.FC<InputProps> = ({ 
  label, 
  variant = 'outlined',
  startIcon,
  className = '', 
  containerClassName = '', 
  ...props 
}) => {
  // Variant styling mapping
  let inputStyles = '';
  if (variant === 'outlined') {
    // Google standard fully pill-shaped search input
    inputStyles = 'h-10 rounded-full bg-surface-low dark:bg-surface-lowest text-on-surface placeholder:text-on-surface-variant/40 outline-none border-0 shadow-none focus:bg-surface-low dark:focus:bg-surface-lowest';
  } else {
    // Standard underlined input: no background, simple bottom line, highly compact
    inputStyles = 'h-10 rounded-none bg-transparent text-on-surface placeholder:text-on-surface-variant/40 outline-none border-0 border-b-2 border-surface-highest/40 focus:border-primary transition-colors duration-150 shadow-none px-0';
  }

  // Padding adjustment for startIcon
  const paddingStyles = startIcon 
    ? (variant === 'standard' ? 'pl-8 pr-0' : 'pl-11 pr-4') 
    : (variant === 'standard' ? 'px-0' : 'px-4');

  // Adjust icon placement for standard underlined variants
  const iconLeftClass = variant === 'standard' ? 'left-0' : 'left-4';

  return (
    <div className={`flex flex-col w-full ${containerClassName} border-0 shadow-none`}>
      {label && (
        <label className="text-[14px] font-medium mb-1.5 text-on-surface">
          {label}
        </label>
      )}
      <div className="relative flex items-center w-full border-0 shadow-none">
        {startIcon && (
          <div className={`absolute ${iconLeftClass} text-on-surface-variant/70 pointer-events-none flex items-center justify-center`}>
            {startIcon}
          </div>
        )}
        <input 
          className={`w-full selection:bg-primary selection:text-on-primary autofill-light dark:autofill-dark text-[14px] ${inputStyles} ${paddingStyles} ${className}`} 
          {...props}
        />
      </div>
    </div>
  );
};
