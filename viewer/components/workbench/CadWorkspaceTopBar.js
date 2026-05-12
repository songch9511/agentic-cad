import { Fragment } from "react";
import { BadgeCheck, Bot, Palette, PanelRightIcon } from "lucide-react";
import {
  Breadcrumb,
  BreadcrumbEllipsis,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator
} from "@/components/ui/breadcrumb";
import { Button } from "@/components/ui/button";
import { SidebarTrigger, useSidebar } from "@/components/ui/sidebar";

function pathSegmentsForEntry(entry, fallbackLabel) {
  if (!entry) {
    return [fallbackLabel];
  }

  const sourcePath = String(entry.source?.path || entry.step?.path || entry.id || "").trim();
  const segments = sourcePath
    ? sourcePath.replace(/\\/g, "/").split("/").filter(Boolean)
    : [];

  if (!segments.length) {
    return [fallbackLabel];
  }

  return [
    ...segments.slice(0, -1),
    fallbackLabel
  ];
}

function collapsedBreadcrumbSegments(segments) {
  if (segments.length <= 3) {
    return segments.map((segment) => ({ type: "segment", label: segment }));
  }

  return [
    { type: "segment", label: segments[0] },
    { type: "ellipsis", label: "..." },
    ...segments.slice(-2).map((segment) => ({ type: "segment", label: segment }))
  ];
}

function fileSheetLabel(fileSheetKind) {
  if (fileSheetKind === "dxf") {
    return "DXF sheet";
  }
  if (fileSheetKind === "urdf") {
    return "URDF sheet";
  }
  if (fileSheetKind === "stepAssembly") {
    return "assembly sheet";
  }
  return "file sheet";
}

export default function CadWorkspaceTopBar({
  previewMode,
  lookMenuOpen,
  sidebarLabelForEntry,
  selectedEntry,
  setLookMenuOpen,
  fileSheetKind = "",
  fileSheetOpen = false,
  onToggleFileSheet,
  agentRailOpen = false,
  showAgentRailToggle = false,
  onToggleAgentRail
}) {
  const { isMobile, state: sidebarState } = useSidebar();

  if (previewMode) {
    return null;
  }

  const selectedFileLabel = selectedEntry ? sidebarLabelForEntry(selectedEntry) : "Select a file";
  const selectedFileTitle = selectedEntry
    ? String(selectedEntry.source?.path || selectedEntry.step?.path || selectedEntry.id || selectedFileLabel)
    : selectedFileLabel;
  const breadcrumbSegments = pathSegmentsForEntry(selectedEntry, selectedFileLabel);
  const breadcrumbItems = collapsedBreadcrumbSegments(breadcrumbSegments);
  const activeIconButtonClasses = "bg-accent text-accent-foreground";
  const showFileSheetToggle = !!fileSheetKind && typeof onToggleFileSheet === "function";
  const lookSheetToggleLabel = lookMenuOpen
    ? "Collapse viewer settings"
    : "Expand viewer settings";
  const fileSheetToggleLabel = fileSheetOpen
    ? `Collapse ${fileSheetLabel(fileSheetKind)}`
    : `Expand ${fileSheetLabel(fileSheetKind)}`;
  const showTopBarSidebarTrigger = isMobile || sidebarState !== "expanded";

  return (
    <header
      className="cad-glass-surface pointer-events-auto flex h-11 shrink-0 items-center gap-2 border-b border-sidebar-border px-2 text-sidebar-foreground"
    >
      {showTopBarSidebarTrigger ? (
        <SidebarTrigger
          title="Toggle Agentic CAD explorer"
          aria-label="Toggle Agentic CAD explorer"
        />
      ) : null}

      <div className="hidden shrink-0 items-center gap-2 rounded-md border border-sidebar-border/70 bg-sidebar-accent/35 px-2 py-1 md:flex">
        <BadgeCheck className="size-3.5 text-primary" strokeWidth={2} aria-hidden="true" />
        <span className="text-[11px] font-semibold text-sidebar-foreground">Agentic CAD</span>
        <span className="text-[10px] text-muted-foreground">Dimension Shell</span>
      </div>

      <Breadcrumb className="min-w-0 flex-1">
        <BreadcrumbList className="min-w-0 flex-nowrap gap-1.5 text-xs sm:gap-1.5">
          {breadcrumbItems.map((item, index) => (
            <Fragment key={`${item.type}:${item.label}:${index}`}>
              <BreadcrumbItem className="min-w-0">
                {item.type === "ellipsis" ? (
                  <BreadcrumbEllipsis className="h-auto w-auto px-0.5 text-muted-foreground [&>svg]:hidden">
                    <span aria-hidden="true">...</span>
                    <span className="sr-only">Collapsed path</span>
                  </BreadcrumbEllipsis>
                ) : index < breadcrumbItems.length - 1 ? (
                  <BreadcrumbLink asChild className="block max-w-32 truncate text-xs font-medium">
                    <span title={selectedFileTitle}>{item.label}</span>
                  </BreadcrumbLink>
                ) : (
                  <BreadcrumbPage
                    className="block max-w-[min(36rem,55vw)] truncate text-xs font-medium"
                    title={selectedFileTitle}
                  >
                    {item.label}
                  </BreadcrumbPage>
                )}
              </BreadcrumbItem>
              {index < breadcrumbItems.length - 1 ? (
                <BreadcrumbSeparator className="text-muted-foreground/60" />
              ) : null}
            </Fragment>
          ))}
        </BreadcrumbList>
      </Breadcrumb>

      <div className="flex shrink-0 items-center gap-1">
        {showAgentRailToggle ? (
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label={agentRailOpen ? "Close agent workbench" : "Open agent workbench"}
            title={agentRailOpen ? "Close agent workbench" : "Open agent workbench"}
            aria-pressed={agentRailOpen}
            onClick={onToggleAgentRail}
            className={`size-8 ${agentRailOpen ? activeIconButtonClasses : ""}`}
          >
            <Bot className="size-4" strokeWidth={2} aria-hidden="true" />
          </Button>
        ) : null}

        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          aria-label={lookSheetToggleLabel}
          title={lookSheetToggleLabel}
          aria-pressed={lookMenuOpen}
          onClick={() => {
            setLookMenuOpen((current) => !current);
          }}
          className={`size-8 ${lookMenuOpen ? activeIconButtonClasses : ""}`}
        >
          <Palette className="size-4" strokeWidth={2} aria-hidden="true" />
        </Button>

        {showFileSheetToggle ? (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label={fileSheetToggleLabel}
            title={fileSheetToggleLabel}
            aria-pressed={fileSheetOpen}
            onClick={onToggleFileSheet}
            className={`size-7 ${fileSheetOpen ? activeIconButtonClasses : ""}`}
          >
            <PanelRightIcon />
            <span className="sr-only">{fileSheetToggleLabel}</span>
          </Button>
        ) : null}
      </div>
    </header>
  );
}
