import React from 'react';
import { Layout, Box as BoxIcon, Search } from 'lucide-react';

// Centralized UI imports using the clean path alias
import { Button, Input, Badge, Loader } from '@ui';

const ComponentGallery: React.FC = () => {
  return (
    <div className="bg-surface-container rounded-lg p-8 border-0 shadow-none">
      <div className="flex flex-row items-center space-x-3 mb-8 border-0 shadow-none">
        <Layout size={24} className="text-primary" />
        <h2 className="text-xl font-bold tracking-tight">Interactive Components</h2>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 border-0 shadow-none">
        {/* Buttons section */}
        <div className="flex flex-col border-0 shadow-none">
          <h3 className="text-[12px] font-bold uppercase tracking-wider text-on-surface-variant/60 mb-4">
            Buttons
          </h3>
          <div className="space-y-4 flex flex-col border-0 shadow-none">
            <Button variant="contained">
              Primary Action
            </Button>
            <Button variant="outlined">
              Secondary Action
            </Button>
            <Button variant="text">
              Tertiary Action
            </Button>
          </div>
        </div>

        {/* Inputs section */}
        <div className="flex flex-col border-0 shadow-none">
          <h3 className="text-[12px] font-bold uppercase tracking-wider text-on-surface-variant/60 mb-4">
            Inputs
          </h3>
          <div className="space-y-4 flex flex-col border-0 shadow-none">
            <Input 
              label="Google Search" 
              placeholder="Search Google or type a URL"
              startIcon={<Search size={18} />}
            />
            <Input 
              label="Password" 
              type="password" 
              placeholder="Enter password"
            />
          </div>
        </div>

        {/* Shapes and Rounding section */}
        <div className="flex flex-col border-0 shadow-none">
          <h3 className="text-[12px] font-bold uppercase tracking-wider text-on-surface-variant/60 mb-4">
            Rounding & Shapes
          </h3>
          <div className="flex flex-row flex-wrap gap-2 items-center border-0 shadow-none">
            <Badge label="Pill-shaped" />
            <Badge label="Category" variant="outlined" />
            <div className="w-12 h-12 rounded-md bg-surface-highest/40 flex items-center justify-center border-0 shadow-none transform-none transition-none">
              <BoxIcon size={20} className="text-primary" />
            </div>
          </div>
        </div>

        {/* Dynamic Loading States section */}
        <div className="col-span-1 md:col-span-3 border-0 shadow-none mt-4 pt-6 border-t border-surface-highest/20">
          <h3 className="text-[12px] font-bold align-center uppercase tracking-wider text-on-surface-variant/60 mb-6 text-center">
            Google Loading States (Unified)
          </h3>
          <div className="flex flex-row space-x-16 justify-center items-center border-0 shadow-none">
            <div className="text-center border-0 shadow-none">
              <span className="text-[11px] font-semibold text-on-surface-variant/60 block mb-3">Dots Variant</span>
              <Loader variant="dots" />
            </div>
            <div className="text-center border-0 shadow-none">
              <span className="text-[11px] font-semibold text-on-surface-variant/60 block mb-3">Spinner Variant</span>
              <Loader variant="spinner" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComponentGallery;
