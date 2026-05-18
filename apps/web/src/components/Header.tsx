import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useThemeMode } from './ThemeProvider';
import { Tooltip } from '@ui';

const Header: React.FC = () => {
  const { mode, toggleTheme } = useThemeMode();

  return (
    <div className="flex flex-row justify-between items-center mb-16 border-0 shadow-none">
      <div className="border-0 shadow-none">
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-2">
          Daffodil Design System
        </h1>
        <p className="text-[15px] text-on-surface-variant font-medium">
          A high-fidelity, dynamic setup aligned strictly with Google default rules.
        </p>
      </div>
      <Tooltip title={mode === 'dark' ? "Switch to Light Theme" : "Switch to Dark Theme"}>
        <button 
          onClick={toggleTheme} 
          className="p-3 rounded-full bg-surface-lowest hover:bg-surface-highest/30 text-on-surface flex items-center justify-center outline-none border-0 shadow-none transform-none transition-none"
        >
          {mode === 'dark' ? <Sun size={22} /> : <Moon size={22} />}
        </button>
      </Tooltip>
    </div>
  );
};

export default Header;
