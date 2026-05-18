import React from 'react';
import { Tooltip } from './Tooltip';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'contained' | 'outlined' | 'text';
  tooltipTitle?: string;
}

export const Button: React.FC<ButtonProps> = ({ 
  variant = 'contained', 
  tooltipTitle, 
  className = '', 
  children, 
  ...props 
}) => {
  const baseStyles = 'px-6 py-2.5 rounded-full font-semibold outline-none border-0 shadow-none transform-none transition-none text-[14px] flex items-center justify-center';
  
  let variantStyles = '';
  if (variant === 'contained') {
    variantStyles = 'bg-primary text-on-primary hover:opacity-90 active:opacity-80';
  } else if (variant === 'outlined') {
    variantStyles = 'bg-surface-low dark:bg-surface-lowest text-primary hover:bg-primary/10';
  } else {
    variantStyles = 'bg-transparent text-primary hover:bg-primary/10';
  }

  const buttonElement = (
    <button 
      className={`${baseStyles} ${variantStyles} ${className}`} 
      {...props}
    >
      {children}
    </button>
  );

  if (tooltipTitle) {
    return <Tooltip title={tooltipTitle}>{buttonElement}</Tooltip>;
  }

  return buttonElement;
};
