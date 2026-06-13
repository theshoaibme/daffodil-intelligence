import type { ComponentType } from "react";
import { SearchResultsWidget } from "../../components/cards/search/SearchResultsWidget";
import { BrowserSessionWidget } from "../../components/cards/browser/BrowserSessionWidget";
import { TerminalWidget } from "../../components/cards/terminal/TerminalWidget";
import { FilePreviewWidget } from "../../components/cards/file/FilePreviewWidget";
import { ImageGalleryWidget } from "../../components/cards/image/ImageGalleryWidget";
import { CodeViewerWidget } from "../../components/cards/code/CodeViewerWidget";
import { TableViewerWidget } from "../../components/cards/database/TableViewerWidget";
import { GenericResultWidget } from "../../components/cards/result/GenericResultWidget";

export type WidgetProps = { payload: Record<string, unknown> };
export type WidgetComponent = ComponentType<WidgetProps>;

const registry = new Map<string, WidgetComponent>([
  ["search_results", SearchResultsWidget],
  ["browser_session", BrowserSessionWidget],
  ["terminal_output", TerminalWidget],
  ["file_preview", FilePreviewWidget],
  ["image_gallery", ImageGalleryWidget],
  ["code_viewer", CodeViewerWidget],
  ["table_viewer", TableViewerWidget],
  ["generic_result", GenericResultWidget],
]);

export function registerWidget(type: string, component: WidgetComponent) {
  registry.set(type, component);
}

export function resolveWidget(widgetType: string): WidgetComponent {
  return registry.get(widgetType) ?? GenericResultWidget;
}
