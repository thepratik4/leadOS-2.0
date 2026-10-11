"use client";

import * as React from "react";
import { Sidebar, type NavTab } from "@/components/sidebar";
import { DiscoveryView, type RerunQueryItem } from "@/components/discovery-view";
import { CompanyDetailSheet } from "@/components/company-detail-sheet";
import { SavedLeadsView } from "@/components/saved-leads-view";
import { SearchHistoryView } from "@/components/search-history-view";
import { SettingsView } from "@/components/settings-view";
import { api } from "@/lib/api";

export default function LeadOSDashboard() {
  const [currentTab, setCurrentTab] = React.useState<NavTab>("discover");
  const [selectedCompanyId, setSelectedCompanyId] = React.useState<string | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);
  const [savedLeadsCount, setSavedLeadsCount] = React.useState(0);
  const [rerunQuery, setRerunQuery] = React.useState<RerunQueryItem | null>(null);

  // Load saved leads count for the sidebar badge
  const refreshSavedCount = React.useCallback(async () => {
    try {
      const data = await api.listSavedLeads();
      setSavedLeadsCount(data.length);
    } catch {
      // ignore
    }
  }, []);

  React.useEffect(() => {
    refreshSavedCount();
  }, [refreshSavedCount]);

  // Global Ctrl+B shortcut to toggle sidebar
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "b") {
        e.preventDefault();
        setSidebarCollapsed((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Handle rerun query from history
  const handleRerunQuery = (query: string) => {
    setRerunQuery({ query, id: Date.now() });
    setCurrentTab("discover");
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans text-slate-900">
      {/* Base UI Sidebar */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        savedLeadsCount={savedLeadsCount}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((prev) => !prev)}
      />

      {/* Main Workspace Canvas */}
      <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden bg-[#f8fafc]">
        <div
          className={`h-full flex-col min-w-0 flex-1 ${
            currentTab === "discover" ? "flex" : "hidden"
          }`}
        >
          <DiscoveryView
            onSelectCompany={(id) => setSelectedCompanyId(id)}
            onLeadSavedChange={refreshSavedCount}
            rerunQuery={rerunQuery}
          />
        </div>

        {currentTab === "saved" && (
          <SavedLeadsView
            onSelectCompany={(id) => setSelectedCompanyId(id)}
            onLeadChange={refreshSavedCount}
          />
        )}

        {currentTab === "history" && (
          <SearchHistoryView onRerunQuery={handleRerunQuery} />
        )}

        {currentTab === "settings" && <SettingsView />}
      </main>

      {/* Company Evidence & Dossier Sheet */}
      <CompanyDetailSheet
        companyId={selectedCompanyId}
        onClose={() => setSelectedCompanyId(null)}
        onLeadSavedChange={refreshSavedCount}
      />
    </div>
  );
}
