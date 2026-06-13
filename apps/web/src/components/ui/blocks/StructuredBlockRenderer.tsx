import type { ReactNode } from "react";
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

type BlockRenderer = (block: UiBlock) => ReactNode;

const blockRegistry = new Map<string, BlockRenderer>();

function registerBlockSchema(schema: string, renderer: BlockRenderer) {
  blockRegistry.set(schema, renderer);
}

registerBlockSchema("data_table", (block) => {
  const data = block.data ?? {};
  const columns = (data.columns as { key: string; label: string }[]) ?? [];
  const rows = (data.rows as Record<string, unknown>[]) ?? [];
  return (
    <UiPanel title={block.title}>
      <UiDataTable columns={columns} rows={rows} />
    </UiPanel>
  );
});

registerBlockSchema("key_value", (block) => (
  <KeyValueBlock
    title={block.title ?? undefined}
    rows={(block.data?.rows as Array<{ key: string; value: string }>) ?? []}
  />
));

registerBlockSchema("tabs", (block) => {
  const tabs = (block.data?.tabs as Array<{ id: string; label: string; block: UiBlock }>) ?? [];
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
});

registerBlockSchema("status_card", (block) => (
  <StatusCard
    title={block.title ?? undefined}
    tone={String(block.data?.tone ?? "info")}
    message={String(block.data?.message ?? "")}
  />
));

registerBlockSchema("error_alert", (block) => (
  <ErrorAlert title={block.title ?? undefined} message={String(block.data?.message ?? "Error")} />
));

export function registerUiBlockRenderer(schema: string, renderer: BlockRenderer) {
  registerBlockSchema(schema, renderer);
}

function renderBlock(block: UiBlock) {
  const renderer = blockRegistry.get(block.schema);
  if (renderer) return renderer(block);
  return (
    <UiPanel title={block.title ?? String(block.schema)}>
      <p className="text-sm text-on-surface-variant">Unable to display this block.</p>
    </UiPanel>
  );
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
