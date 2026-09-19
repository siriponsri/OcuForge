import { Box, Button, Flex, HStack, IconButton, Text, VStack } from "@chakra-ui/react";
import {
  Activity,
  Database,
  FileBox,
  FolderOpen,
  LayoutDashboard,
  Menu,
  RefreshCw,
  ScanLine,
  ShieldCheck,
  X,
} from "lucide-react";

const navItems = [
  { id: "sources", label: "Sources", caption: "Connect and ingest", icon: FolderOpen },
  { id: "queue", label: "Queue", caption: "Review worklist", icon: ScanLine },
  { id: "review", label: "Review & Label", caption: "Human decisions", icon: Activity },
  { id: "summary", label: "Summary", caption: "Throughput view", icon: LayoutDashboard },
  { id: "manifest", label: "Dataset / Manifest", caption: "Training index", icon: Database },
];

export function AppShell({ page, onNavigate, children, onReset, sourceReady, queueCount, mobileNavOpen, setMobileNavOpen }) {
  return (
    <Box className="app-root">
      <Box className={`mobile-scrim ${mobileNavOpen ? "is-open" : ""}`} onClick={() => setMobileNavOpen(false)} />
      <Box as="aside" className={`app-sidebar ${mobileNavOpen ? "is-open" : ""}`}>
        <Flex className="brand-lockup" align="center" justify="space-between">
          <HStack gap="3">
            <Box className="brand-mark"><ScanLine size={18} strokeWidth={2.4} /></Box>
            <Box>
              <Text className="brand-name">OcuForge</Text>
              <Text className="brand-caption">RETINAL MODEL FACTORY</Text>
            </Box>
          </HStack>
          <IconButton className="sidebar-close" aria-label="Close navigation" variant="ghost" size="sm" onClick={() => setMobileNavOpen(false)}>
            <X size={18} />
          </IconButton>
        </Flex>

        <VStack className="sidebar-nav" align="stretch" gap="1">
          <Text className="nav-kicker">Workspace</Text>
          {navItems.map(({ id, label, caption, icon: Icon }) => (
            <Button
              key={id}
              className={`nav-item ${page === id ? "is-active" : ""}`}
              variant="ghost"
              justifyContent="flex-start"
              onClick={() => { onNavigate(id); setMobileNavOpen(false); }}
            >
              <Icon size={18} />
              <Box textAlign="left">
                <Text className="nav-label">{label}</Text>
                <Text className="nav-caption">{caption}</Text>
              </Box>
              {id === "queue" && <span className="nav-count">{queueCount}</span>}
            </Button>
          ))}
        </VStack>

        <Box className="sidebar-footer">
          <Flex className="privacy-card" gap="3" align="flex-start">
            <ShieldCheck size={17} />
            <Box>
              <Text className="privacy-title">Local authority</Text>
              <Text className="privacy-copy">Synthetic demo data only. Private images stay on-prem.</Text>
            </Box>
          </Flex>
          <Button className="reset-button" variant="ghost" size="sm" onClick={onReset}>
            <RefreshCw size={15} />
            Reset demo state
          </Button>
        </Box>
      </Box>

      <Box className="app-main">
        <Flex as="header" className="topbar" align="center" justify="space-between">
          <HStack gap="3">
            <IconButton className="menu-button" aria-label="Open navigation" variant="ghost" size="sm" onClick={() => setMobileNavOpen(true)}>
              <Menu size={19} />
            </IconButton>
            <Box>
              <Text className="workspace-label">OcuForge workspace</Text>
              <Text className="workspace-context">Encoder head POC <span>/</span> Local review</Text>
            </Box>
          </HStack>
          <HStack className="topbar-status" gap="3">
            <span className={`connection-dot ${sourceReady ? "is-ready" : ""}`} />
            <Text>{sourceReady ? "Local adapters ready" : "Setup needed"}</Text>
            <Box className="demo-pill">POC / SYNTHETIC</Box>
          </HStack>
        </Flex>
        <Box as="main" className="page-content">{children}</Box>
      </Box>
    </Box>
  );
}
