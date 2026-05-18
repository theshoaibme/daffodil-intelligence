import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'contained' | 'outlined' | 'text' | 'tonal';
  color?: 'primary' | 'secondary' | 'error';
  size?: 'sm' | 'md' | 'lg';
}

export const Button: React.FC<ButtonProps> = ({ 
  variant = 'contained', 
  color = 'primary',
  size = 'md',
  className = '', 
  children, 
  ...props 
}) => {
  // Base pill-shaped modern layout
  const baseStyles = 'rounded-full font-semibold outline-none border-0 shadow-none transform-none transition-none flex items-center justify-center';
  
  // Size variants mapping
  let sizeStyles = '';
  if (size === 'sm') {
    sizeStyles = 'px-4 py-1.5 text-[12px]';
  } else if (size === 'lg') {
    sizeStyles = 'px-8 py-3.5 text-[16px]';
  } else {
    sizeStyles = 'px-6 py-2.5 text-[14px]'; // standard md size
  }

  // Variant & Color combinations
  let variantStyles = '';
  if (variant === 'contained') {
    if (color === 'secondary') {
      variantStyles = 'bg-secondary text-white hover:opacity-90 active:opacity-80';
    } else if (color === 'error') {
      variantStyles = 'bg-error text-white hover:opacity-90 active:opacity-80';
    } else {
      variantStyles = 'bg-primary text-on-primary hover:opacity-90 active:opacity-80';
    }
  } else if (variant === 'outlined') {
    if (color === 'secondary') {
      variantStyles = 'bg-transparent text-secondary border border-secondary/30 hover:bg-secondary/10';
    } else if (color === 'error') {
      variantStyles = 'bg-transparent text-error border border-error/30 hover:bg-error/10';
    } else {
      variantStyles = 'bg-transparent text-primary border border-primary/30 hover:bg-primary/10';
    }
  } else if (variant === 'tonal') {
    // Premium Google Material You Filled Tonal variant (soft background, deep colored text)
    if (color === 'secondary') {
      variantStyles = 'bg-secondary/15 text-secondary hover:bg-secondary/25';
    } else if (color === 'error') {
      variantStyles = 'bg-error/15 text-error hover:bg-error/25';
    } else {
      variantStyles = 'bg-primary/15 text-primary hover:bg-primary/25';
    }
  } else {
    // Text variant
    if (color === 'secondary') {
      variantStyles = 'bg-transparent text-secondary hover:bg-secondary/10';
    } else if (color === 'error') {
      variantStyles = 'bg-transparent text-error hover:bg-error/10';
    } else {
      variantStyles = 'bg-transparent text-primary hover:bg-primary/10';
    }
  }

  return (
    <button 
      className={`${baseStyles} ${sizeStyles} ${variantStyles} ${className}`} 
      {...props}
    >
      {children}
    </button>
  );
};
