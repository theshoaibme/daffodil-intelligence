import React from 'react';

// Clean component imports utilizing the @components path alias
import Header from '@components/Header';
import ColorPalette from '@components/ColorPalette';
import TypographyShowcase from '@components/TypographyShowcase';
import ComponentGallery from '@components/ComponentGallery';
import Footer from '@components/Footer';

const App: React.FC = () => {
  return (
    <div className="min-h-screen py-16 bg-background text-on-surface border-0 shadow-none">
      <div className="max-w-6xl mx-auto px-6 border-0 shadow-none">
        {/* Header */}
        <Header />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 border-0 shadow-none">
          {/* Colors Section */}
          <div className="col-span-1 border-0 shadow-none">
            <ColorPalette />
          </div>

          {/* Typography Section */}
          <div className="col-span-1 border-0 shadow-none">
            <TypographyShowcase />
          </div>

          {/* Components Section */}
          <div className="col-span-1 md:col-span-2 border-0 shadow-none">
            <ComponentGallery />
          </div>
        </div>

        {/* Footer */}
        <Footer />
      </div>
    </div>
  );
};

export default App;