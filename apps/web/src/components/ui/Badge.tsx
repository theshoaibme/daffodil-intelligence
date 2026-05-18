import React from 'react';

interface BadgeProps {
  label: string;
  variant?: 'filled' | 'outlined';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ 
  label, 
  variant = 'filled', 
  className = '' 
}) => {
  const baseStyles = 'px-3 py-1 rounded-full text-[12px] font-semibold inline-flex items-center justify-center outline-none border-0 shadow-none transform-none transition-none';
  
  let variantStyles = '';
  if (variant === 'filled') {
    variantStyles = 'bg-surface-highest text-on-surface';
  } else {
    variantStyles = 'bg-transparent text-primary border border-primary/30';
  }

  return (
    <span className={`${baseStyles} ${variantStyles} ${className}`}>
      {label}
    </span>
  );
};
