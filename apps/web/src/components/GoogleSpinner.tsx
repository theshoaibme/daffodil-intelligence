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
  // Translate legacy color codes to clean primative equivalents for compilation
  const loaderColor = React.useMemo(() => {
    if (color === 'warn') return 'error';
    if (color === 'accent') return 'secondary';
    return 'primary';
  }, [color]);

  // Leverage our 100% pure Tailwind Loader primitive to enforce identical premium visuals
  return (
    <Loader
      variant="spinner"
      diameter={diameter}
      strokeWidth={strokeWidth}
      color={loaderColor}
      message={message}
      fullPage={fullPage}
      overlay={overlay}
    />
  );
};

export default GoogleSpinner;
