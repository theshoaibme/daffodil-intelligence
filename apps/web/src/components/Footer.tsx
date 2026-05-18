import React from 'react';
import { Github, Twitter, Linkedin } from 'lucide-react';

const Footer: React.FC = () => {
  return (
    <div className="mt-20 pt-8 border-t border-surface-highest/20 opacity-60 border-0 shadow-none">
      <div className="flex flex-row justify-between items-center border-0 shadow-none">
        <p className="text-[14px]">
          © 2026 Daffodil Intelligence. All rights reserved.
        </p>
        <div className="flex flex-row space-x-3 border-0 shadow-none">
          <button className="p-2 hover:bg-surface-highest/20 text-on-surface hover:text-primary rounded-full outline-none border-0 shadow-none transform-none transition-none flex items-center justify-center">
            <Github size={18} />
          </button>
          <button className="p-2 hover:bg-surface-highest/20 text-on-surface hover:text-primary rounded-full outline-none border-0 shadow-none transform-none transition-none flex items-center justify-center">
            <Twitter size={18} />
          </button>
          <button className="p-2 hover:bg-surface-highest/20 text-on-surface hover:text-primary rounded-full outline-none border-0 shadow-none transform-none transition-none flex items-center justify-center">
            <Linkedin size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Footer;
