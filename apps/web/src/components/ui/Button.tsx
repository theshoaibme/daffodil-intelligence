import React from 'react';
import { Loader } from './Loader';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'contained' | 'outlined' | 'text' | 'tonal';
  color?: 'primary' | 'secondary' | 'error';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  loadingDiameter?: number;
  loadingStrokeWidth?: number;
}

export const Button: React.FC<ButtonProps> = ({ 
  variant = 'contained', 
  color = 'primary',
  size = 'md',
  loading = false,
  loadingDiameter,
  loadingStrokeWidth,
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
      variantStyles = 'bg-secondary text-white hover:opacity-90 active:opacity-80';
    } else if (color === 'error') {
      variantStyles = 'bg-error text-white hover:opacity-90 active:opacity-80';
    } else {
      variantStyles =
        'bg-gradient-to-b from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700 border-none active:from-blue-700 active:to-blue-800';
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
    if (color === 'secondary') {
      variantStyles = 'bg-secondary/15 text-secondary hover:bg-secondary/25';
    } else if (color === 'error') {
      variantStyles = 'bg-error/15 text-error hover:bg-error/25';
    } else {
      variantStyles = 'bg-primary/15 text-primary hover:bg-primary/25';
    }
  } else {
    if (color === 'secondary') {
      variantStyles = 'bg-transparent text-secondary hover:bg-secondary/10';
    } else if (color === 'error') {
      variantStyles = 'bg-transparent text-error hover:bg-error/10';
    } else {
      variantStyles = 'bg-transparent text-primary hover:bg-primary/10';
    }
  }

  const disabledStyles = (disabled && !loading) ? 'opacity-50 pointer-events-none' : '';

  // Calculate spinner size dynamically based on the button size
  const loaderDiameter = loadingDiameter ?? (size === 'sm' ? 24 : size === 'lg' ? 36 : 30);
  const strokeWidth = loadingStrokeWidth ?? (size === 'sm' ? 2.5 : size === 'lg' ? 3.5 : 3);

  const showLoader = loading && (variant === 'contained' || variant === 'outlined' || variant === 'tonal');

  return (
    <button 
      className={`${baseStyles} ${sizeStyles} ${variantStyles} ${disabledStyles} ${className}`} 
      disabled={disabled || loading}
      {...props}
    >
      {showLoader && (
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
      <span className={showLoader ? 'invisible' : 'flex items-center justify-center'}>
        {children}
      </span>
    </button>
  );
};
