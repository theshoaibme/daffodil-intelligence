import type { UiBlock } from "@lib/uiBlocks/types";
import { normalizeUiBlocks } from "@lib/uiBlocks/normalize";
import { ErrorAlert } from "./ErrorAlert";
import { KeyValueBlock } from "./KeyValueBlock";
import { StatusCard } from "./StatusCard";
import { UiDataTable } from "./UiDataTable";
import { UiPanel } from "./UiPanel";
import { UiTabs } from "./UiTabs";

interface StructuredBlockRendererProps {
  blocks: UiBlock[];
}

function renderBlock(block: UiBlock) {
  const schema = block.schema;
  const data = block.data ?? {};

  switch (schema) {
    case "data_table": {
      const columns = (data.columns as { key: string; label: string }[]) ?? [];
      const rows = (data.rows as Record<string, unknown>[]) ?? [];
      return (
        <UiPanel title={block.title}>
          <UiDataTable columns={columns} rows={rows} />
        </UiPanel>
      );
    }
    case "key_value":
      return (
        <KeyValueBlock
          title={block.title ?? undefined}
          rows={(data.rows as Array<{ key: string; value: string }>) ?? []}
        />
      );
    case "tabs": {
      const tabs = (data.tabs as Array<{ id: string; label: string; block: UiBlock }>) ?? [];
      return (
        <UiPanel title={block.title}>
          <UiTabs
            tabs={tabs.map((tab) => ({
              id: tab.id,
              label: tab.label,
              content: renderBlock(tab.block),
            }))}
          />
        </UiPanel>
      );
    }
    case "status_card":
      return (
        <StatusCard
          title={block.title ?? undefined}
          tone={String(data.tone ?? "info")}
          message={String(data.message ?? "")}
        />
      );
    case "error_alert":
      return <ErrorAlert title={block.title ?? undefined} message={String(data.message ?? "Error")} />;
    default:
      return (
        <UiPanel title={block.title ?? String(schema)}>
          <p className="text-sm text-on-surface-variant">Unable to display this block.</p>
        </UiPanel>
      );
  }
}

export function StructuredBlockRenderer({ blocks }: StructuredBlockRendererProps) {
  const normalized = normalizeUiBlocks(blocks);
  if (!normalized.length) return null;

  return (
    <div className="flex flex-col gap-3 w-full">
      {normalized.map((block) => (
        <div key={block.id}>{renderBlock(block)}</div>
      ))}
    </div>
  );
}
