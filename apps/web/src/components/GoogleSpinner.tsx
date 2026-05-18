import React from 'react';
import { Loader } from '@ui';

interface GoogleSpinnerProps {
  diameter?: number;
  strokeWidth?: number;
  mode?: 'determinate' | 'indeterminate';
  color?: 'primary' | 'accent' | 'warn';
  message?: string;
  fullPage?: boolean;
  overlay?: boolean;
}

const GoogleSpinner: React.FC<GoogleSpinnerProps> = ({
  diameter = 40,
  strokeWidth = 4,
  color = 'primary',
  message,
  fullPage = false,
  overlay = false,
}) => {
  // Leverage our 100% pure Tailwind Loader primitive to enforce identical premium visuals
  return (
    <Loader
      variant="spinner"
      diameter={diameter}
      strokeWidth={strokeWidth}
      color={color}
      message={message}
      fullPage={fullPage}
      overlay={overlay}
    />
  );
};

export default GoogleSpinner;
