import React from 'react';
import { Loader } from './Loader';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'contained' | 'outlined' | 'text' | 'tonal';
  color?: 'primary' | 'secondary' | 'error';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean; // Add the premium loading state prop!
}

export const Button: React.FC<ButtonProps> = ({ 
  variant = 'contained', 
  color = 'primary',
  size = 'md',
  loading = false,
  disabled,
  className = '', 
  children, 
  ...props 
}) => {
  // Add 'relative' to support absolute centering of the spinner loader
  const baseStyles = 'relative rounded-full font-semibold outline-none border-0 shadow-none transform-none transition-none flex items-center justify-center';
  
  let sizeStyles = '';
  if (size === 'sm') {
    sizeStyles = 'px-4 py-1.5 text-[12px]';
  } else if (size === 'lg') {
    sizeStyles = 'px-8 py-3.5 text-[16px]';
  } else {
    sizeStyles = 'px-6 py-2.5 text-[14px]';
  }

  let variantStyles = '';
  if (variant === 'contained') {
    if (color === 'secondary') {
      variantStyles = 'bg-secondary text-white hover:opacity-90 active:opacity-80 disabled:opacity-50';
    } else if (color === 'error') {
      variantStyles = 'bg-error text-white hover:opacity-90 active:opacity-80 disabled:opacity-50';
    } else {
      variantStyles = 'bg-primary text-on-primary hover:opacity-90 active:opacity-80 disabled:opacity-50';
    }
  } else if (variant === 'outlined') {
    if (color === 'secondary') {
      variantStyles = 'bg-transparent text-secondary border border-secondary/30 hover:bg-secondary/10 disabled:opacity-50';
    } else if (color === 'error') {
      variantStyles = 'bg-transparent text-error border border-error/30 hover:bg-error/10 disabled:opacity-50';
    } else {
      variantStyles = 'bg-transparent text-primary border border-primary/30 hover:bg-primary/10 disabled:opacity-50';
    }
  } else if (variant === 'tonal') {
    if (color === 'secondary') {
      variantStyles = 'bg-secondary/15 text-secondary hover:bg-secondary/25 disabled:opacity-50';
    } else if (color === 'error') {
      variantStyles = 'bg-error/15 text-error hover:bg-error/25 disabled:opacity-50';
    } else {
      variantStyles = 'bg-primary/15 text-primary hover:bg-primary/25 disabled:opacity-50';
    }
  } else {
    if (color === 'secondary') {
      variantStyles = 'bg-transparent text-secondary hover:bg-secondary/10 disabled:opacity-50';
    } else if (color === 'error') {
      variantStyles = 'bg-transparent text-error hover:bg-error/10 disabled:opacity-50';
    } else {
      variantStyles = 'bg-transparent text-primary hover:bg-primary/10 disabled:opacity-50';
    }
  }

  // Calculate spinner size dynamically based on the button size
  const loaderDiameter = size === 'sm' ? 24 : size === 'lg' ? 36 : 30;
  const strokeWidth = size === 'sm' ? 2.5 : size === 'lg' ? 3.5 : 3;

  return (
    <button 
      className={`${baseStyles} ${sizeStyles} ${variantStyles} ${className}`} 
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <Loader 
            variant="spinner" 
            diameter={loaderDiameter} 
            strokeWidth={strokeWidth} 
            color="inherit" 
          />
        </div>
      )}
      {/* Hide text while loading, but keep it in the DOM to preserve dimensions */}
      <span className={loading ? 'invisible' : 'flex items-center justify-center'}>
        {children}
      </span>
    </button>
  );
};
