import { useState, useRef, useLayoutEffect, useEffect } from "react";
import { ChevronDown } from "lucide-react";
import { motion } from "framer-motion";

interface UserMessageBadgeProps {
  prompt?: string;
}

export function UserMessageBadge({ prompt }: UserMessageBadgeProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [hasOverflow, setHasOverflow] = useState(false);
  const textRef = useRef<HTMLSpanElement>(null);

  const cleanPrompt = prompt?.trim() || "";
  const hasNewline = cleanPrompt.includes("\n");
  const showDropdown = hasNewline || hasOverflow;
  const displayPrompt = cleanPrompt || "Custom template";

  // Collapse prompt by default whenever a new message is sent
  useEffect(() => {
    setIsExpanded(false);
  }, [cleanPrompt]);

  useLayoutEffect(() => {
    const el = textRef.current;
    if (!el) return;

    const checkOverflow = () => {
      if (!isExpanded) {
        const isOverflowing = el.scrollWidth > el.clientWidth;
        setHasOverflow(isOverflowing);
      }
    };

    checkOverflow();

    // Use ResizeObserver for highly responsive detection across all screen transitions/shifts
    const observer = new ResizeObserver(checkOverflow);
    observer.observe(el);

    window.addEventListener("resize", checkOverflow);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", checkOverflow);
    };
  }, [cleanPrompt, isExpanded]);

  const handleToggle = () => {
    if (showDropdown) {
      setIsExpanded(!isExpanded);
    }
  };

  return (
    <div className="w-full">
      <motion.button
        layout
        onClick={handleToggle}
        disabled={!showDropdown}
        animate={{
          borderRadius: isExpanded ? "16px" : "9999px",
          paddingTop: isExpanded ? "10px" : "8px",
          paddingBottom: isExpanded ? "10px" : "8px",
        }}
        transition={{ duration: 0.25, ease: "easeInOut" }}
        className={`flex items-start gap-2.5 bg-surface-container-high/65 border border-outline-variant/30 w-full text-left outline-none shadow-sm ${
          showDropdown ? "hover:bg-surface-container-highest cursor-pointer" : "cursor-default"
        } pl-2 pr-4`}
      >
        <img
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuDJf7XQASA0jBSOSKY-mKuNg5uw2i3AajRzSSWjX1ajaWZJzkiCeEjMgJ4udRILP4lYH6l5zxiOu3rWYG_My9e_MPXCbsW-rYClgRi_7iUV0plEb0mHpsovRqixVDiRcUYbn76TQexaIosqkZ5qrEPT9jPooVZG9GqD6o79nHOB8Yz8Y2gGOVukTFHag1h-5qrw5j_nThhOXY_idm_7H0KFf2GWg5vHyzTJNR_cmSmPSFfFT3LCBbMTGMHiL8hM7kmBV-5YnufJZQ"
          alt="User Profile"
          className="w-6 h-6 rounded-full object-cover border border-outline-variant/30 flex-shrink-0 mt-0.5"
        />
        <motion.span
          ref={textRef}
          layout="position"
          className={`text-xs font-semibold text-on-surface-variant flex-1 pr-2 custom-scrollbar break-words ${
            isExpanded ? "whitespace-pre-wrap overflow-y-auto" : "truncate overflow-hidden"
          } leading-relaxed`}
          style={{
            maxHeight: isExpanded ? "80px" : "18px",
            alignSelf: isExpanded ? "flex-start" : "center",
          }}
          animate={{
            height: isExpanded ? "auto" : "18px",
          }}
          transition={{ duration: 0.25, ease: "easeInOut" }}
          title={prompt}
        >
          {displayPrompt}
        </motion.span>
        {showDropdown && (
          <motion.div
            animate={{
              rotate: isExpanded ? 180 : 0,
              y: isExpanded ? 2 : 0,
            }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className={`flex-shrink-0 ${isExpanded ? "mt-0.5" : "self-center"}`}
          >
            <ChevronDown size={14} className="text-on-surface-variant/80 animate-pulse" />
          </motion.div>
        )}
      </motion.button>
    </div>
  );
}
