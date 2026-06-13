import { PublicLayout } from "@layout";
import { PUBLIC_LAYOUT_WIDTH } from "@lib";
import { ConnectionsNetwork } from "./components/ConnectionsNetwork";

export function ConnectionsPage() {
  return (
    <PublicLayout>
      <main className={`${PUBLIC_LAYOUT_WIDTH} flex-1 py-8 sm:py-12 animate-fadeIn`}>
        <ConnectionsNetwork />
      </main>
    </PublicLayout>
  );
}
