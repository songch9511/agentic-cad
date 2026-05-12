import { StrictMode, useEffect, useSyncExternalStore } from "react";
import { createRoot } from "react-dom/client";
import CadWorkspace from "./components/CadWorkspace";
import BenchmarkCarouselViewer from "./components/demo/BenchmarkCarouselViewer";
import DimensionLaunchDemo from "./components/demo/DimensionLaunchDemo";
import DimensionProductApp from "./components/product/DimensionProductApp";
import faviconUrl from "./app/favicon.png";
import "./app/globals.css";
import { getCadManifestSnapshot, subscribeCadManifest } from "./lib/cadManifestStore";
import { consumeCadWorkspacePersistenceResetRequest } from "./lib/workbench/persistence";

const ROOT_ID = "root";
const PRODUCT_PATH = "/";
const LAUNCH_DEMO_PATH = "/dimension";
const LAUNCH_DEMO_ALIAS_PATH = "/dimension-demo";
const BENCHMARK_CAROUSEL_PATH = "/benchmarks";
const WORKBENCH_PATH = "/workbench";

function ensureFavicon() {
  if (typeof document === "undefined") {
    return;
  }

  let icon = document.querySelector('link[rel="icon"]');
  if (!icon) {
    icon = document.createElement("link");
    icon.rel = "icon";
    document.head.appendChild(icon);
  }
  icon.type = "image/png";
  icon.href = faviconUrl;
}

function bootstrap() {
  const rootElement = document.getElementById(ROOT_ID);
  if (!rootElement) {
    throw new Error(`Missing #${ROOT_ID} mount point.`);
  }
  ensureFavicon();
  consumeCadWorkspacePersistenceResetRequest();
  document.title = "Agentic CAD";
  const root = rootElement.__agenticCadRoot || createRoot(rootElement);
  rootElement.__agenticCadRoot = root;
  root.render(
    <StrictMode>
      <AppRoot />
    </StrictMode>,
  );
}

function normalizePathname(pathname) {
  return pathname.endsWith("/") && pathname.length > 1
    ? pathname.slice(0, -1)
    : pathname;
}

function routeSnapshot() {
  if (typeof window === "undefined") {
    return {
      pathname: "/",
      searchParams: new URLSearchParams(),
    };
  }
  return {
    pathname: window.location.pathname,
    searchParams: new URLSearchParams(window.location.search),
  };
}

function isLaunchDemoRoute(pathname, searchParams) {
  const normalizedPath = normalizePathname(pathname);
  return normalizedPath === LAUNCH_DEMO_PATH || normalizedPath === LAUNCH_DEMO_ALIAS_PATH || searchParams.get("demo") === "launch";
}

function isBenchmarkCarouselRoute(pathname, searchParams) {
  const normalizedPath = normalizePathname(pathname);
  return normalizedPath === BENCHMARK_CAROUSEL_PATH || searchParams.get("demo") === "benchmarks";
}

function isWorkbenchRoute(pathname, searchParams) {
  const normalizedPath = normalizePathname(pathname);
  return normalizedPath === WORKBENCH_PATH || searchParams.get("app") === "workbench";
}

function AppRoot() {
  const { pathname, searchParams } = routeSnapshot();
  if (normalizePathname(pathname) === PRODUCT_PATH && !searchParams.get("demo") && !searchParams.get("app")) {
    return <ProductRoute />;
  }
  if (isLaunchDemoRoute(pathname, searchParams)) {
    return <LaunchDemoRoute canonicalize={normalizePathname(pathname) !== LAUNCH_DEMO_ALIAS_PATH} />;
  }
  if (isBenchmarkCarouselRoute(pathname, searchParams)) {
    return <BenchmarkCarouselRoute />;
  }
  if (isWorkbenchRoute(pathname, searchParams)) {
    return <CadWorkspaceRoute />;
  }

  return <ProductRoute />;
}

function LaunchDemoRoute({ canonicalize = true }) {
  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    if (!canonicalize) {
      return;
    }
    if (window.location.pathname === LAUNCH_DEMO_PATH && !window.location.search) {
      return;
    }
    window.history.replaceState(window.history.state, "", `${LAUNCH_DEMO_PATH}${window.location.hash}`);
  }, [canonicalize]);

  return <DimensionLaunchDemo />;
}

function ProductRoute() {
  const { manifest } = useSyncExternalStore(
    subscribeCadManifest,
    getCadManifestSnapshot,
    getCadManifestSnapshot,
  );

  return (
    <DimensionProductApp
      manifestEntries={manifest.entries}
    />
  );
}

function BenchmarkCarouselRoute() {
  const { manifest } = useSyncExternalStore(
    subscribeCadManifest,
    getCadManifestSnapshot,
    getCadManifestSnapshot,
  );

  return (
    <BenchmarkCarouselViewer
      manifestEntries={manifest.entries}
    />
  );
}

function CadWorkspaceRoute() {
  const { manifest, revision } = useSyncExternalStore(
    subscribeCadManifest,
    getCadManifestSnapshot,
    getCadManifestSnapshot,
  );

  return (
    <CadWorkspace
      manifestRevision={revision}
      manifestEntries={manifest.entries}
      catalogRootName={manifest.root?.name}
    />
  );
}

bootstrap();
