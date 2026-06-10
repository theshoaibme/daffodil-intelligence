import { CardCanvas } from "../components/canvas/CardCanvas";
import { filterThreadCards } from "./cardFilters";

interface RenderEngineProps {
  sessionId: string;
  /** Render only inline cards (excludes dock-only types) */
  inlineOnly?: boolean;
  /** Card types to hide (e.g. block/result already shown in message thread) */
  excludeCardTypes?: string[];
  /** Limit cards to the active turn */
  turnId?: string | null;
  className?: string;
}

export function RenderEngine({
  sessionId,
  inlineOnly = true,
  excludeCardTypes = [],
  turnId,
  className,
}: RenderEngineProps) {
  return (
    <CardCanvas
      sessionId={sessionId}
      className={className}
      filter={(card) =>
        filterThreadCards(card, {
          excludeTypes: excludeCardTypes,
          inlineOnly,
          turnId,
        })
      }
    />
  );
}
