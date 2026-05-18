

export function SuggestionChip({ text }: { text: string }) {
  return (
    <button className="px-4 py-2 rounded-full border border-outline-variant/30 bg-surface-container-low hover:bg-surface-container-high text-sm text-on-surface-variant transition-all hover:border-outline">
      {text}
    </button>
  );
}
