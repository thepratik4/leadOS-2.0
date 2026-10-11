"use client";

import * as React from "react";
import {
  Search,
  BookmarkCheck,
  History,
  Sliders,
  ShieldCheck,
  PanelLeftClose,
  PanelLeft,
  Activity,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

export type NavTab = "discover" | "saved" | "history" | "settings";

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  savedLeadsCount: number;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export function Sidebar({
  currentTab,
  onSelectTab,
  savedLeadsCount,
  collapsed,
  onToggleCollapse,
}: SidebarProps) {
  const navItems = [
    {
      id: "discover" as NavTab,
      label: "Discover",
      icon: Search,
      badge: null,
      description: "Company discovery & signals",
    },
    {
      id: "saved" as NavTab,
      label: "Saved Leads",
      icon: BookmarkCheck,
      badge: savedLeadsCount > 0 ? savedLeadsCount : null,
      description: "Prioritized prospects",
    },
    {
      id: "history" as NavTab,
      label: "Search History",
      icon: History,
      badge: null,
      description: "Persisted search runs",
    },
    {
      id: "settings" as NavTab,
      label: "Settings & Health",
      icon: Sliders,
      badge: null,
      description: "Diagnostics & providers",
    },
  ];

  return (
    <aside
      className={cn(
        "flex flex-col border-r border-slate-200 bg-white transition-[width] duration-200 ease-in-out shrink-0 select-none z-30",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className="flex h-14 items-center justify-between border-b border-slate-200 px-3.5">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-blue-600 text-white shadow-xs">
            <ShieldCheck className="size-5" />
          </div>
          {!collapsed && (
            <div className="flex flex-col min-w-0">
              <span className="text-sm font-bold tracking-tight text-slate-900 leading-none">
                LeadOS
              </span>
              <span className="text-[10px] text-slate-500 font-medium tracking-tight truncate mt-0.5">
                Evidence-First Prospecting
              </span>
            </div>
          )}
        </div>
        <button
          onClick={onToggleCollapse}
          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors cursor-pointer"
          title={collapsed ? "Expand sidebar (Ctrl+B)" : "Collapse sidebar (Ctrl+B)"}
        >
          {collapsed ? <PanelLeft className="size-4" /> : <PanelLeftClose className="size-4" />}
          <span className="sr-only">Toggle Sidebar</span>
        </button>
      </div>

      {/* Navigation Group */}
      <div className="flex-1 overflow-y-auto px-2.5 py-4 space-y-1">
        {!collapsed && (
          <div className="px-2 pb-2 text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
            Workspace
          </div>
        )}
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={cn(
                "group flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-xs font-medium transition-colors cursor-pointer text-left relative",
                isActive
                  ? "bg-blue-50 text-blue-700 font-semibold"
                  : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
              )}
              title={collapsed ? item.label : undefined}
            >
              <Icon
                className={cn(
                  "size-4 shrink-0 transition-colors",
                  isActive ? "text-blue-600" : "text-slate-500 group-hover:text-slate-700"
                )}
              />
              {!collapsed && (
                <div className="flex flex-1 items-center justify-between min-w-0">
                  <span className="truncate">{item.label}</span>
                  {item.badge !== null && (
                    <Badge variant="secondary" className="ml-auto px-1.5 py-0 text-[10px]">
                      {item.badge}
                    </Badge>
                  )}
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Footer System Status */}
      <div className="border-t border-slate-200 p-3">
        {collapsed ? (
          <div className="flex justify-center" title="System Operational (Zero-Config DDGS)">
            <span className="relative flex size-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full size-2.5 bg-emerald-500"></span>
            </span>
          </div>
        ) : (
          <div className="rounded-md bg-slate-50 border border-slate-200/80 p-2.5 text-[11px] space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 font-medium text-slate-700">
                <span className="size-2 rounded-full bg-emerald-500 inline-block" />
                Live Verification
              </span>
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 font-mono">
                v1.0
              </Badge>
            </div>
            <p className="text-[10px] text-slate-500 leading-tight">
              Deterministic scoring & SSRF guard active.
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}
