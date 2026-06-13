import type { IconType } from "react-icons";
import {
  RiBookOpenFill,
  RiBrainFill,
  RiBriefcaseFill,
  RiBuilding2Fill,
  RiBusFill,
  RiCameraFill,
  RiClipboardFill,
  RiCodeFill,
  RiComputerFill,
  RiErrorWarningFill,
  RiFileCopyFill,
  RiFlaskFill,
  RiGraduationCapFill,
  RiHeartFill,
  RiHomeFill,
  RiMicFill,
  RiMoneyDollarCircleFill,
  RiCalendarEventFill,
  RiRobotFill,
  RiTimerFill,
  RiWalletFill,
  RiFileTextFill,
  RiListCheck2,
  RiSettings4Fill,
  RiCalendarScheduleFill,
} from "react-icons/ri";

export interface AgentIconStyle {
  icon: IconType;
  iconColor: string;
}

export const AGENT_ICON_STYLES: Record<string, AgentIconStyle> = {
  academic: { icon: RiGraduationCapFill, iconColor: "text-blue-500" },
  library: { icon: RiBookOpenFill, iconColor: "text-amber-500" },
  campus: { icon: RiBuilding2Fill, iconColor: "text-teal-500" },
  career: { icon: RiBriefcaseFill, iconColor: "text-indigo-500" },
  coding: { icon: RiCodeFill, iconColor: "text-emerald-500" },
  research: { icon: RiFlaskFill, iconColor: "text-violet-500" },
  writing: { icon: RiFileTextFill, iconColor: "text-sky-600" },
  tasks: { icon: RiListCheck2, iconColor: "text-orange-500" },
  wellness: { icon: RiHeartFill, iconColor: "text-rose-500" },
  finance: { icon: RiMoneyDollarCircleFill, iconColor: "text-green-600" },
  vision: { icon: RiCameraFill, iconColor: "text-fuchsia-500" },
  voice: { icon: RiMicFill, iconColor: "text-sky-500" },
  exam: { icon: RiClipboardFill, iconColor: "text-orange-500" },
  hostel: { icon: RiHomeFill, iconColor: "text-cyan-600" },
  transport: { icon: RiBusFill, iconColor: "text-lime-600" },
  campus_events: { icon: RiCalendarEventFill, iconColor: "text-pink-500" },
  event: { icon: RiCalendarScheduleFill, iconColor: "text-yellow-500" },
  complaint: { icon: RiErrorWarningFill, iconColor: "text-red-500" },
  automation: { icon: RiSettings4Fill, iconColor: "text-amber-600" },
  fee: { icon: RiWalletFill, iconColor: "text-green-500" },
  general: { icon: RiRobotFill, iconColor: "text-slate-500" },
  computer_use: { icon: RiComputerFill, iconColor: "text-blue-600" },
  copycat: { icon: RiFileCopyFill, iconColor: "text-purple-500" },
  planning: { icon: RiBrainFill, iconColor: "text-violet-600" },
  routine: { icon: RiTimerFill, iconColor: "text-cyan-500" },
};

const CATEGORY_FALLBACK: Record<string, AgentIconStyle> = {
  university: { icon: RiBuilding2Fill, iconColor: "text-teal-500" },
  computer: { icon: RiComputerFill, iconColor: "text-blue-600" },
  orchestration: { icon: RiBrainFill, iconColor: "text-violet-600" },
  productivity: { icon: RiCodeFill, iconColor: "text-emerald-500" },
  ai: { icon: RiCameraFill, iconColor: "text-fuchsia-500" },
  general: { icon: RiRobotFill, iconColor: "text-slate-500" },
};

const DEFAULT_STYLE: AgentIconStyle = {
  icon: RiRobotFill,
  iconColor: "text-slate-500",
};

export function getAgentIconStyle(agentId: string, category = "general"): AgentIconStyle {
  return AGENT_ICON_STYLES[agentId] ?? CATEGORY_FALLBACK[category] ?? DEFAULT_STYLE;
}
