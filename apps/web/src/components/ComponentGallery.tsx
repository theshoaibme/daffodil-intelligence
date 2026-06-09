import React, { useState } from 'react';
import { Layout, Box as BoxIcon, Search } from 'lucide-react';

// Centralized UI imports using the clean path alias
import { Button, Input, Badge, Loader } from '@ui';

const ComponentGallery: React.FC = () => {
  // Add state for the interactive loading button toggle control (No hardcoded mock timeouts)
  const [btnLoading, setBtnLoading] = useState(false);

  return (
    <div className="bg-surface-container rounded-lg p-8 border-0 shadow-none">
      <div className="flex flex-row items-center space-x-3 mb-8 border-0 shadow-none">
        <Layout size={24} className="text-primary" />
        <h2 className="text-xl font-bold tracking-tight">Interactive Components</h2>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-12 border-0 shadow-none">
        {/* Buttons section */}
        <div className="flex flex-col border-0 shadow-none">
          <div className="flex flex-row justify-between items-center mb-4 border-0 shadow-none">
            <h3 className="text-[12px] font-bold uppercase tracking-wider text-on-surface-variant/60">
              Button Variants & Colors
            </h3>
            
            {/* Real-time Toggle for testing dynamic Loading (No hardcoded mock timing) */}
            <label className="relative inline-flex items-center cursor-pointer select-none">
              <input 
                type="checkbox" 
                checked={btnLoading}
                onChange={(e) => setBtnLoading(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-surface-highest/80 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-on-surface-variant dark:after:bg-on-surface after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary peer-checked:after:bg-on-primary" />
              <span className="ms-2 text-[11px] font-semibold text-on-surface-variant/80">
                Mock Load
              </span>
            </label>
          </div>

          <div className="space-y-4 flex flex-col border-0 shadow-none">
            <Button variant="contained" loading={btnLoading}>
              Primary Contained
            </Button>

            <Button variant="tonal" loading={btnLoading}>
              Tonal Accent
            </Button>
            
            <Button variant="outlined" loading={btnLoading}>
              Outlined Border
            </Button>
            
            <Button variant="text" loading={btnLoading}>
              Text Standard
            </Button>
            
            <div className="pt-4 border-t border-surface-highest/20 flex flex-row space-x-2">
              <Button size="sm" color="error" loading={btnLoading}>
                Small Error
              </Button>
              <Button size="sm" variant="tonal" color="secondary" loading={btnLoading}>
                Small Secondary
              </Button>
            </div>
          </div>
        </div>

        {/* Inputs section */}
        <div className="flex flex-col border-0 shadow-none">
          <h3 className="text-[12px] font-bold uppercase tracking-wider text-on-surface-variant/60 mb-4">
            Input Variants
          </h3>
          <div className="space-y-6 flex flex-col border-0 shadow-none">
            <Input 
              variant="outlined"
              label="Outlined Variant" 
              placeholder="Search Google or type a URL"
              startIcon={<Search size={18} />}
            />
            <Input 
              variant="standard"
              label="Underlined Standard Variant" 
              placeholder="Type anything..."
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
          <h3 className="text-[12px] font-bold align-center uppercase tracking-wider text-on-surface-variant/60 mb-8 text-center">
            Google Loading States (Unified)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 justify-center items-center border-0 shadow-none">
            <div className="text-center border-0 shadow-none flex flex-col items-center">
              <span className="text-[11px] font-semibold text-on-surface-variant/60 block mb-4">Spinner Variant</span>
              <Loader variant="spinner" />
            </div>
            
            <div className="text-center border-0 shadow-none flex flex-col items-center">
              <span className="text-[11px] font-semibold text-on-surface-variant/60 block mb-4">Dots Variant</span>
              <Loader variant="dots" />
            </div>

            <div className="text-center border-0 shadow-none flex flex-col items-center">
              <span className="text-[11px] font-semibold text-on-surface-variant/60 block mb-4">Linear progress bar</span>
              <Loader variant="linear" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComponentGallery;
