"use client";

import * as React from "react";
import {
  Sliders,
  ShieldCheck,
  Database,
  Cpu,
  Globe,
  Lock,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Server,
  Terminal,
} from "lucide-react";
import { api, type HealthStatus } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function SettingsView() {
  const [health, setHealth] = React.useState<HealthStatus | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const loadHealth = React.useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch (err: unknown) {
      const msg =
        typeof err === "object" && err !== null && "message" in err
          ? (err as { message: string }).message
          : "Could not reach backend health endpoint.";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadHealth();
  }, [loadHealth]);

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            System Settings & Diagnostics
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time backend status, database persistence, search providers, and crawler guards.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={loadHealth}
          disabled={isLoading}
          className="gap-1.5"
        >
          <RefreshCw className="size-3.5" />
          Re-test Health
        </Button>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Skeleton className="h-44 w-full" />
          <Skeleton className="h-44 w-full" />
          <Skeleton className="h-44 w-full" />
          <Skeleton className="h-44 w-full" />
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-xs text-red-800">
          <span className="font-bold block mb-1">Backend Connectivity Notice:</span>
          {error}. Ensure FastAPI is running on port 8000 (`uvicorn app.main:app`).
        </div>
      )}

      {!isLoading && health && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Card 1: API & Server Status */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs flex items-center gap-2">
                  <Server className="size-4 text-blue-600" />
                  FastAPI Application Runtime
                </CardTitle>
                <Badge variant={health.status === "healthy" ? "verified" : "destructive"}>
                  {health.status.toUpperCase()}
                </Badge>
              </div>
              <CardDescription>
                Core REST API engine running on Python 3.13
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">App Name</span>
                <span className="font-semibold text-slate-900">{health.app_name}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">API Version</span>
                <span className="font-mono text-slate-700">{health.version}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Docs Path</span>
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline font-mono inline-flex items-center gap-1"
                >
                  /docs (Swagger UI)
                </a>
              </div>
            </CardContent>
          </Card>

          {/* Card 2: Database Storage */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs flex items-center gap-2">
                  <Database className="size-4 text-emerald-600" />
                  Persistence & Models
                </CardTitle>
                <Badge variant={health.database.status === "healthy" ? "verified" : "destructive"}>
                  {health.database.status.toUpperCase()}
                </Badge>
              </div>
              <CardDescription>
                SQLAlchemy 2.x async engine with Alembic migrations
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Storage Backend</span>
                <span className="font-mono text-slate-700">SQLite (aiosqlite) / PostgreSQL</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Schema Isolation</span>
                <span className="text-slate-900 font-medium">Automatic DDL Migration</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Duplicate Domain Constraint</span>
                <span className="text-emerald-700 font-semibold">Enforced (Unique Index)</span>
              </div>
            </CardContent>
          </Card>

          {/* Card 3: Discovery Provider */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs flex items-center gap-2">
                  <Globe className="size-4 text-indigo-600" />
                  Web Discovery Provider
                </CardTitle>
                <Badge variant={health.search_provider.available ? "verified" : "partially_verified"}>
                  {health.search_provider.available ? "ACTIVE" : "CONFIG REQUIRED"}
                </Badge>
              </div>
              <CardDescription>
                Live external company candidate discovery engine
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Active Provider</span>
                <span className="font-semibold text-slate-900">
                  {health.search_provider.name}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Key Requirement</span>
                <span className="text-slate-700">
                  {health.search_provider.requires_key ? "API Key Required" : "Zero-Config (Free Tier)"}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 pt-1">
                {health.search_provider.message}
              </p>
            </CardContent>
          </Card>

          {/* Card 4: AI Assisted Mode */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs flex items-center gap-2">
                  <Cpu className="size-4 text-violet-600" />
                  Factual Extraction Engine
                </CardTitle>
                <Badge variant="outline">
                  {health.ai_assisted_extraction.configured ? "HYBRID AI" : "DETERMINISTIC"}
                </Badge>
              </div>
              <CardDescription>
                Claim extraction operates fully without requiring an LLM API key
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Current Mode</span>
                <span className="font-mono text-slate-800">
                  {health.ai_assisted_extraction.mode}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Gemini Key Injected</span>
                <span className="font-medium text-slate-700">
                  {health.ai_assisted_extraction.configured ? "Configured" : "None (Deterministic Rule Fallback)"}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 pt-1">
                Notice: All extracted claims are strictly validated against raw source text by the Evidence Validator, regardless of AI presence.
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Security & Crawler Architecture card */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-xs flex items-center gap-2">
            <Lock className="size-4 text-slate-700" />
            Crawler Security Safeguards (SSRF Protection)
          </CardTitle>
          <CardDescription>
            Controlled retrieval prevents server-side request forgery and unauthorized host access
          </CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="rounded-md border border-slate-200 bg-slate-50 p-3 space-y-1">
            <span className="font-semibold text-slate-800 block">Restricted Destinations</span>
            <p className="text-slate-600 text-[11px] leading-relaxed">
              Blocks 127.0.0.1, RFC 1918 private ranges (10.x, 172.16.x, 192.168.x), AWS/GCP cloud metadata (169.254.169.254), and loopbacks.
            </p>
          </div>
          <div className="rounded-md border border-slate-200 bg-slate-50 p-3 space-y-1">
            <span className="font-semibold text-slate-800 block">Redirect Revalidation</span>
            <p className="text-slate-600 text-[11px] leading-relaxed">
              Manually resolves HTTP redirects (up to 3 hops) re-verifying safe destination IP addresses at every individual hop.
            </p>
          </div>
          <div className="rounded-md border border-slate-200 bg-slate-50 p-3 space-y-1">
            <span className="font-semibold text-slate-800 block">Bounded Resources</span>
            <p className="text-slate-600 text-[11px] leading-relaxed">
              Connection timeout: 8.0s. Max payload: 2MB. Concurrency semaphore: 5 simultaneous fetches.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
