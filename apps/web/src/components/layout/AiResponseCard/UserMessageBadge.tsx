import { useState, useRef, useLayoutEffect, useEffect } from "react";
import { ChevronDown } from "lucide-react";
import { motion } from "framer-motion";

interface UserMessageBadgeProps {
  prompt?: string;
  onEdit?: () => void;
}

export function UserMessageBadge({ prompt, onEdit }: UserMessageBadgeProps) {
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

  return (
    <div className="w-full">
      <div
        role="button"
        tabIndex={0}
        onClick={onEdit}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onEdit?.();
          }
        }}
        className={`flex items-start gap-2.5 bg-surface-container-high/65 border border-outline-variant/30 w-full text-left outline-none shadow-sm transition-[border-radius,padding,border-color,background-color] duration-200 ease-in-out cursor-pointer pl-2 pr-2.5 hover:bg-surface-container-highest/65 hover:border-outline-variant/60 ${
          isExpanded ? "rounded-[16px] py-2.5" : "rounded-[20px] py-2"
        }`}
      >
        <img
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuDJf7XQASA0jBSOSKY-mKuNg5uw2i3AajRzSSWjX1ajaWZJzkiCeEjMgJ4udRILP4lYH6l5zxiOu3rWYG_My9e_MPXCbsW-rYClgRi_7iUV0plEb0mHpsovRqixVDiRcUYbn76TQexaIosqkZ5qrEPT9jPooVZG9GqD6o79nHOB8Yz8Y2gGOVukTFHag1h-5qrw5j_nThhOXY_idm_7H0KFf2GWg5vHyzTJNR_cmSmPSFfFT3LCBbMTGMHiL8hM7kmBV-5YnufJZQ"
          alt="User Profile"
          className="w-6 h-6 rounded-full object-cover border border-outline-variant/30 flex-shrink-0 mt-0.5"
        />
        <motion.span
          ref={textRef}
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
          transition={{ duration: 0.2, ease: "easeInOut" }}
          title={prompt}
        >
          {displayPrompt}
        </motion.span>
        {showDropdown && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
            tabIndex={0}
            className={`flex-shrink-0 p-1 rounded-full hover:bg-surface-container-highest active:bg-surface-container-highest/80 transition-all duration-200 -mr-1.5 flex items-center justify-center cursor-pointer border-none bg-transparent outline-none ${
              isExpanded ? "mt-0" : "self-center"
            }`}
          >
            <motion.div
              animate={{
                rotate: isExpanded ? 180 : 0,
                y: isExpanded ? 2 : 0,
              }}
              transition={{ duration: 0.2, ease: "easeInOut" }}
              className="flex items-center justify-center"
            >
              <ChevronDown size={14} className="text-on-surface-variant/80" />
            </motion.div>
          </button>
        )}
      </div>
    </div>
  );
}
