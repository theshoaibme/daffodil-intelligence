import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { motion } from "framer-motion";

interface UserMessageBadgeProps {
  prompt?: string;
}

export function UserMessageBadge({ prompt }: UserMessageBadgeProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const cleanPrompt = prompt?.trim() || "";
  const lines = cleanPrompt.split("\n");
  const isMultiline = lines.length > 1;
  const displayPrompt = cleanPrompt || "Custom template";

  const handleToggle = () => {
    if (isMultiline) {
      setIsExpanded(!isExpanded);
    }
  };

  return (
    <div className="w-full">
      {isMultiline ? (
        <button
          onClick={handleToggle}
          className={`flex items-start gap-2.5 bg-surface-container-high/65 hover:bg-surface-container-highest border border-outline-variant/30 ${
            isExpanded ? "rounded-[16px] py-2.5" : "rounded-full py-2"
          } pl-2 pr-4 cursor-pointer transition-all duration-200 w-full text-left outline-none shadow-sm`}
        >
          <img
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuDJf7XQASA0jBSOSKY-mKuNg5uw2i3AajRzSSWjX1ajaWZJzkiCeEjMgJ4udRILP4lYH6l5zxiOu3rWYG_My9e_MPXCbsW-rYClgRi_7iUV0plEb0mHpsovRqixVDiRcUYbn76TQexaIosqkZ5qrEPT9jPooVZG9GqD6o79nHOB8Yz8Y2gGOVukTFHag1h-5qrw5j_nThhOXY_idm_7H0KFf2GWg5vHyzTJNR_cmSmPSFfFT3LCBbMTGMHiL8hM7kmBV-5YnufJZQ"
            alt="User Profile"
            className="w-6 h-6 rounded-full object-cover border border-outline-variant/30 flex-shrink-0 mt-0.5"
          />
          <span
            className={`text-xs font-semibold text-on-surface-variant flex-1 pr-2 custom-scrollbar ${
              isExpanded
                ? "whitespace-pre-wrap max-h-[80px] overflow-y-auto leading-relaxed"
                : "truncate self-center"
            }`}
            title={prompt}
          >
            {displayPrompt}
          </span>
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
            className="flex-shrink-0 self-center"
          >
            <ChevronDown size={14} className="text-on-surface-variant/80 animate-pulse" />
          </motion.div>
        </button>
      ) : (
        <div
          className="flex items-center gap-2.5 bg-surface-container-high/65 border border-outline-variant/30 rounded-full pl-2 pr-4 py-2 w-full text-left shadow-sm"
        >
          <img
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuDJf7XQASA0jBSOSKY-mKuNg5uw2i3AajRzSSWjX1ajaWZJzkiCeEjMgJ4udRILP4lYH6l5zxiOu3rWYG_My9e_MPXCbsW-rYClgRi_7iUV0plEb0mHpsovRqixVDiRcUYbn76TQexaIosqkZ5qrEPT9jPooVZG9GqD6o79nHOB8Yz8Y2gGOVukTFHag1h-5qrw5j_nThhOXY_idm_7H0KFf2GWg5vHyzTJNR_cmSmPSFfFT3LCBbMTGMHiL8hM7kmBV-5YnufJZQ"
            alt="User Profile"
            className="w-6 h-6 rounded-full object-cover border border-outline-variant/30 flex-shrink-0"
          />
          <span
            className="text-xs font-semibold text-on-surface-variant truncate flex-1 pr-2"
            title={prompt}
          >
            {displayPrompt}
          </span>
        </div>
      )}
    </div>
  );
}
