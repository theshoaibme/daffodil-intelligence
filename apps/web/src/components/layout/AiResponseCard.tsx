import { useState } from "react";
import { ChevronDown, Check } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export function AiResponseCard() {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  return (
    <div className="w-full max-w-md bg-panel-bg border border-outline-variant/40 rounded-[28px] p-6 shadow-2xl text-left select-none relative overflow-hidden flex flex-col gap-5">
      {/* Top Capsule Indicator */}
      <div className="flex">
        <div className="bg-white rounded-full px-3 py-1 flex items-center justify-center gap-1.5 w-[52px] h-[26px]">
          <div className="w-2 h-2 rounded-full bg-black"></div>
          <div className="w-2 h-2 rounded-full bg-black"></div>
        </div>
      </div>

      {/* Interactive Dropdown Capsule */}
      <div className="relative">
        <button 
          onClick={() => setDropdownOpen(!dropdownOpen)}
          className="flex items-center gap-2 bg-[#252629] hover:bg-[#2d2e32] border border-neutral-800 rounded-full pl-2 pr-4 py-1.5 cursor-pointer transition-all duration-200 w-fit max-w-[260px] text-left outline-none"
        >
          <img 
            src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80" 
            alt="AI Avatar" 
            className="w-6 h-6 rounded-full object-cover border border-white/10"
          />
          <span className="text-xs font-medium text-neutral-300 truncate">
            {dropdownOpen ? "app background and mood" : "app background and mo..."}
          </span>
          <motion.div
            animate={{ rotate: dropdownOpen ? 180 : 0 }}
            transition={{ duration: 0.2 }}
            className="flex-shrink-0"
          >
            <ChevronDown size={14} className="text-neutral-400" />
          </motion.div>
        </button>

        {/* Dropdown Menu Details */}
        <AnimatePresence>
          {dropdownOpen && (
            <motion.div
              initial={{ opacity: 0, y: -8, scale: 0.95 }}
              animate={{ opacity: 1, y: 4, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full left-0 mt-1 w-72 bg-[#202124] border border-neutral-800 rounded-2xl shadow-xl z-20 p-3 flex flex-col gap-2"
            >
              <div className="text-xs font-semibold text-neutral-400 uppercase tracking-wider px-2 py-1">Steps Executed</div>
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2 p-2 rounded-lg bg-primary/10 text-primary">
                  <Check size={14} className="stroke-[3]" />
                  <span className="text-xs font-medium">Applied Stitch Light System</span>
                </div>
                <div className="flex items-center gap-2 p-2 rounded-lg text-neutral-300 hover:bg-neutral-800/50 transition-all">
                  <Check size={14} className="text-neutral-500" />
                  <span className="text-xs">Generated grid background layout</span>
                </div>
                <div className="flex items-center gap-2 p-2 rounded-lg text-neutral-300 hover:bg-neutral-800/50 transition-all">
                  <Check size={14} className="text-neutral-500" />
                  <span className="text-xs">Compiled styling design tokens</span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Main Response Content */}
      <div className="flex flex-col gap-4 text-neutral-200 text-[14px] leading-relaxed font-sans pr-1">
        <p>
          background grid. This adds a layer of depth and immersion to the workspace without being distracting.
        </p>

        <ul className="list-disc pl-5 flex flex-col gap-4">
          <li className="marker:text-neutral-500">
            <span className="font-semibold text-white">Dynamic Grid Background:</span>{" "}
            Maintained the clean, systematic grid aesthetic while integrating the new lighting layer.
          </li>
          <li className="marker:text-neutral-500">
            <span className="font-semibold text-white">Performance Optimized:</span>{" "}
            The effect is built using the HTML5 Canvas API to ensure smooth, low-latency movement that respects the clinical and professional tone of the design system.
          </li>
        </ul>

        <p className="mt-1">
          How does the interactive feel of the background work for you, or should we adjust the intensity of the light effect?
        </p>
      </div>
    </div>
  );
}
