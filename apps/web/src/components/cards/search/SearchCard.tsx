import type { Card } from "../../../engine/types";
import { CardShell } from "../CardShell";
import { SearchResultsWidget } from "./SearchResultsWidget";

export default function SearchCard({ card }: { card: Card }) {
  return (
    <CardShell card={card}>
      <SearchResultsWidget payload={card.payload} />
    </CardShell>
  );
}
