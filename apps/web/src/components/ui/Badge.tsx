import React from 'react';
import { Tooltip } from './Tooltip';

interface BadgeProps {
  label: string;
  variant?: 'filled' | 'outlined';
  tooltipTitle?: string;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ 
  label, 
  variant = 'filled', 
  tooltipTitle, 
  className = '' 
}) => {
  const baseStyles = 'px-3 py-1 rounded-full text-[12px] font-semibold inline-flex items-center justify-center outline-none border-0 shadow-none transform-none transition-none';
  
  let variantStyles = '';
  if (variant === 'filled') {
    variantStyles = 'bg-surface-highest text-on-surface';
  } else {
    variantStyles = 'bg-transparent text-primary border border-primary/30';
  }

  const badgeElement = (
    <span className={`${baseStyles} ${variantStyles} ${className}`}>
      {label}
    </span>
  );

  if (tooltipTitle) {
    return <Tooltip title={tooltipTitle}>{badgeElement}</Tooltip>;
  }

  return badgeElement;
};
