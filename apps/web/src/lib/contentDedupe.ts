/** Remove a repeated second copy when the model echoes the same section twice. */
export function dedupeRepeatedSections(content: string): string {
  const text = content.trim();
  if (!text || text.length < 200) return text;

  const markers = [
    /📅\s*Upcoming Exam Schedule/i,
    /🤖\s*Automated Telegram Reminder Agent/i,
    /##\s*Architecture Overview/i,
    /##\s*Step\s*1:/i,
    /#\s*🤖\s*Automated Telegram Reminder Agent/i,
  ];

  for (const marker of markers) {
    const matches = [...text.matchAll(new RegExp(marker.source, marker.flags + "g"))];
    if (matches.length >= 2 && matches[1]?.index != null) {
      return text.slice(0, matches[1].index).trim();
    }
  }

  const half = Math.floor(text.length / 2);
  const first = text.slice(0, half).trim();
  const second = text.slice(half).trim();
  if (first.length > 100 && second.startsWith(first.slice(0, Math.min(80, first.length)))) {
    return first;
  }

  return text;
}
