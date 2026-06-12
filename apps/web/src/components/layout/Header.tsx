import { FileText, MessageSquare, Gift, Menu } from "lucide-react";
import { Logo } from "../logo";
import { HeaderIcon } from "../ui";
import { UserMenu } from "./UserMenu";
import { useIsLgUp } from "@hooks";

interface HeaderProps {
  onOpenSidebar?: () => void;
}

export function Header({ onOpenSidebar }: HeaderProps = {} as HeaderProps) {
  const isLgUp = useIsLgUp();

  return (
    <header className="sticky top-0 z-[60] shrink-0 flex justify-between items-center h-14 sm:h-16 w-full bg-background/95 backdrop-blur-md max-lg:px-3 sm:px-4 lg:pr-6 isolate pt-[env(safe-area-inset-top)]">
      <div className="flex items-center gap-1.5 sm:gap-2.5 min-w-0 flex-1">
        {!isLgUp && onOpenSidebar ? (
          <button
            type="button"
            onClick={onOpenSidebar}
            aria-label="Open menu"
            className="shrink-0 flex items-center justify-center size-10 rounded-full text-on-surface bg-surface-container-high/80 hover:bg-surface-container-high border-0 cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
          >
            <Menu size={22} strokeWidth={2} />
          </button>
        ) : null}
        <Logo size="sm" className="min-w-0 flex-1" />
      </div>

      <div className="flex items-center gap-2 sm:gap-4 shrink-0 pl-2">
        <div className="hidden sm:flex items-center gap-1.5">
          <HeaderIcon title="Documentation" icon={<FileText size={22} />} />
          <HeaderIcon title="Feedback" icon={<MessageSquare size={22} />} />
          <HeaderIcon title="What's new" icon={<Gift size={22} />} />
        </div>

        <UserMenu />
      </div>
    </header>
  );
}
