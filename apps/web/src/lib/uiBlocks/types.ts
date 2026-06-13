export type UiBlockSchema =
  | "data_table"
  | "key_value"
  | "tabs"
  | "status_card"
  | "error_alert";

export interface UiBlock {
  id: string;
  schema: UiBlockSchema | string;
  title?: string | null;
  data: Record<string, unknown>;
  source?: string | null;
}

export interface UiTableColumn {
  key: string;
  label: string;
}
