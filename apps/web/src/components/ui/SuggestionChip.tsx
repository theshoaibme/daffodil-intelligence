

export function SuggestionChip({ text, onClick }: { text: string; onClick?: () => void }) {
  return (
    <button 
      onClick={onClick}
      className="px-4 py-2 rounded-full border border-outline-variant/30 bg-surface-container-low hover:bg-surface-container-high text-sm text-on-surface-variant transition-all hover:border-outline cursor-pointer"
    >
      {text}
    </button>
  );
}
