import React from 'react';
import { Tooltip } from './Tooltip';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  tooltipTitle?: string;
  startIcon?: React.ReactNode;
  containerClassName?: string;
}

export const Input: React.FC<InputProps> = ({ 
  label, 
  tooltipTitle, 
  startIcon,
  className = '', 
  containerClassName = '', 
  ...props 
}) => {
  const inputElement = (
    <div className={`flex flex-col w-full ${containerClassName}`}>
      {label && (
        <label className="text-[14px] font-medium mb-1.5 text-on-surface">
          {label}
        </label>
      )}
      <div className="relative flex items-center w-full">
        {startIcon && (
          <div className="absolute left-4 text-on-surface-variant/70 pointer-events-none flex items-center justify-center">
            {startIcon}
          </div>
        )}
        <input 
          className={`h-10 w-full rounded-full bg-surface-low dark:bg-surface-lowest text-on-surface placeholder:text-on-surface-variant/40 outline-none border-0 shadow-none selection:bg-primary selection:text-on-primary autofill-light dark:autofill-dark text-[14px] ${
            startIcon ? 'pl-11 pr-4' : 'px-4'
          } ${className}`} 
          {...props}
        />
      </div>
    </div>
  );

  if (tooltipTitle) {
    return <Tooltip title={tooltipTitle}>{inputElement}</Tooltip>;
  }

  return inputElement;
};
