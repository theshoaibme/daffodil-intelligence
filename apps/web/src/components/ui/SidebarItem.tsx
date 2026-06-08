interface SidebarItemProps {
  title: string;
  date: string;
  img: string;
  subtitle?: string;
  onClick?: () => void;
}

export function SidebarItem({ title, date, img, subtitle, onClick }: SidebarItemProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex items-center gap-3 p-2 rounded-xl hover:bg-surface-container-high cursor-pointer transition-all group/item text-left w-full border-0 bg-transparent"
    >
      <div className="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center overflow-hidden border border-outline-variant/10 flex-shrink-0">
        <img alt={title} className="object-cover w-full h-full opacity-80 group-hover/item:opacity-100 transition-opacity" src={img} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-on-surface truncate font-medium">{title}</p>
        <p className="text-[11px] text-on-surface-variant truncate">
          {subtitle ? `${subtitle} · ${date}` : date}
        </p>
      </div>
    </button>
  );
}
