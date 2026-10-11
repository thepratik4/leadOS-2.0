"use client";

import * as React from "react";
import {
  Search,
  SlidersHorizontal,
  Download,
  RotateCcw,
  Star,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  AlertCircle,
  Sparkles,
  CheckCircle2,
  HelpCircle,
  Building2,
  MapPin,
  TrendingUp,
} from "lucide-react";
import {
  api,
  type DiscoveryCandidateItem,
  type DiscoverySearchResponse,
} from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export interface RerunQueryItem {
  query: string;
  id: number;
}

interface DiscoveryViewProps {
  onSelectCompany: (companyId: string) => void;
  onLeadSavedChange: () => void;
  rerunQuery?: RerunQueryItem | null;
}

const PRESET_QUERIES = [
  "B2B SaaS hiring engineering in United States",
  "Fintech infrastructure and payment platforms",
  "Cybersecurity cloud compliance automation",
  "AI developer tooling and observability",
];

const INDUSTRIES = [
  "All Industries",
  "SaaS",
  "Fintech",
  "Cybersecurity",
  "Healthcare / HealthTech",
  "Artificial Intelligence",
  "E-Commerce & Retail",
  "Developer Tools",
];

const GEOGRAPHIES = [
  "All Locations",
  "United States",
  "United Kingdom",
  "Canada",
  "Germany",
  "San Francisco, CA",
  "New York, NY",
  "Austin, TX",
];

const COMPANY_SIZES = [
  "All Sizes",
  "1-10",
  "11-50",
  "51-200",
  "201-500",
  "500+",
];

const SIGNALS = [
  "All Signals",
  "Hiring Expansion",
  "Tech Stack Adoption",
  "Funding & Growth",
  "Product Launch",
];

function sanitizeCsv(val: string | number | null | undefined): string {
  if (val === null || val === undefined) return "";
  const s = String(val).trim();
  if (s && ["=", "+", "-", "@", "\t", "\r"].includes(s[0])) {
    return `"'${s.replace(/"/g, '""')}"`;
  }
  return `"${s.replace(/"/g, '""')}"`;
}

export function DiscoveryView({
  onSelectCompany,
  onLeadSavedChange,
  rerunQuery,
}: DiscoveryViewProps) {
  // Query & Filter states
  const [query, setQuery] = React.useState("B2B SaaS hiring engineering in United States");
  const [industry, setIndustry] = React.useState("All Industries");
  const [geography, setGeography] = React.useState("All Locations");
  const [companySize, setCompanySize] = React.useState("All Sizes");
  const [buyingSignal, setBuyingSignal] = React.useState("All Signals");
  const [limit, setLimit] = React.useState(10);
  const [verifySources, setVerifySources] = React.useState(true);
  const [sortBy, setSortBy] = React.useState<"score" | "evidence" | "name">("score");

  // Search Results & UI states
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [searchResponse, setSearchResponse] = React.useState<DiscoverySearchResponse | null>(null);
  const [savingCompanyId, setSavingCompanyId] = React.useState<string | null>(null);

  // Track last executed rerun object to allow repeated reruns of the same query
  const lastExecutedRerunRef = React.useRef<RerunQueryItem | null>(null);

  // Execute discovery search
  const performSearch = React.useCallback(
    async (searchQuery?: string) => {
      const q = (searchQuery !== undefined ? searchQuery : query).trim();
      if (!q || q.length < 2) return;

      setIsLoading(true);
      setError(null);

      try {
        const resp = await api.searchCompanies({
          query: q,
          industry: industry === "All Industries" ? undefined : industry,
          geography: geography === "All Locations" ? undefined : geography,
          employee_range: companySize === "All Sizes" ? undefined : companySize,
          buying_signal: buyingSignal === "All Signals" ? undefined : buyingSignal,
          limit,
          verify_sources: verifySources,
        });
        setSearchResponse(resp);
      } catch (err: unknown) {
        const message =
          typeof err === "object" && err !== null && "message" in err
            ? (err as { message: string }).message
            : "Discovery search failed. Please verify provider connectivity.";
        setError(message);
      } finally {
        setIsLoading(false);
      }
    },
    [query, industry, geography, companySize, buyingSignal, limit, verifySources]
  );

  const handleSearch = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    performSearch();
  };

  // Trigger search whenever the rerun value changes, including repeated reruns of the same query
  React.useEffect(() => {
    if (rerunQuery && rerunQuery !== lastExecutedRerunRef.current) {
      lastExecutedRerunRef.current = rerunQuery;
      setQuery(rerunQuery.query);
      performSearch(rerunQuery.query);
    }
  }, [rerunQuery, performSearch]);

  // Toggle Save Lead
  const handleToggleSave = async (candidate: DiscoveryCandidateItem) => {
    const comp = candidate.company;
    setSavingCompanyId(comp.id);
    try {
      if (comp.is_saved) {
        // Find saved lead id by listing saved leads
        const allSaved = await api.listSavedLeads();
        const existing = allSaved.find((s) => s.company_id === comp.id);
        if (existing) {
          await api.deleteSavedLead(existing.id);
        }
        comp.is_saved = false;
      } else {
        await api.saveLead({
          company_id: comp.id,
          status: "new",
          notes: `Discovered from query: "${query}"`,
        });
        comp.is_saved = true;
      }
      onLeadSavedChange();
    } catch (saveErr) {
      console.error("Save lead error", saveErr);
    } finally {
      setSavingCompanyId(null);
    }
  };

  // Clear filters
  const handleClearFilters = () => {
    setIndustry("All Industries");
    setGeography("All Locations");
    setCompanySize("All Sizes");
    setBuyingSignal("All Signals");
    setLimit(10);
  };

  // Export search results to CSV safely
  const handleExportSearchResultsCsv = () => {
    if (!searchResponse || searchResponse.candidates.length === 0) return;

    const headers = [
      "Company Name",
      "Domain",
      "Industry",
      "Location",
      "Size Range",
      "Lead Score",
      "Score Tier",
      "Data Quality Score",
      "Verified Signal",
      "Verified Evidence Count",
      "Total Evidence Count",
      "Website URL",
    ];

    const rows = sortedCandidates.map((c) => [
      sanitizeCsv(c.company.name),
      sanitizeCsv(c.company.domain),
      sanitizeCsv(c.company.industry),
      sanitizeCsv(c.company.city || c.company.country),
      sanitizeCsv(c.company.employee_range),
      sanitizeCsv(c.score.total_score),
      sanitizeCsv(c.score.score_tier),
      sanitizeCsv(c.score.data_quality_score),
      sanitizeCsv(c.primary_signal || ""),
      sanitizeCsv(c.verification_summary.verified),
      sanitizeCsv(c.evidence.length),
      sanitizeCsv(c.company.website_url),
    ]);

    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `leados_search_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Sorted candidates
  const sortedCandidates = React.useMemo(() => {
    if (!searchResponse) return [];
    const list = [...searchResponse.candidates];
    if (sortBy === "score") {
      list.sort((a, b) => b.score.total_score - a.score.total_score);
    } else if (sortBy === "evidence") {
      list.sort(
        (a, b) => b.verification_summary.verified - a.verification_summary.verified
      );
    } else if (sortBy === "name") {
      list.sort((a, b) => a.company.name.localeCompare(b.company.name));
    }
    return list;
  }, [searchResponse, sortBy]);

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Prospect Discovery
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Discover real companies, extract buying signals from primary sources, and inspect deterministic scores.
          </p>
        </div>
        {searchResponse && searchResponse.candidates.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportSearchResultsCsv}
            className="self-start md:self-auto gap-1.5"
          >
            <Download className="size-3.5" />
            Export Results (CSV)
          </Button>
        )}
      </div>

      {/* Search Bar & Filters Card */}
      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-xs space-y-3.5">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 size-4 text-slate-400" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter discovery query (e.g., 'B2B SaaS with engineering hiring', 'Fintech API platforms')..."
              className="pl-9 h-9 text-xs"
              required
            />
          </div>
          <Button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="h-9 px-4 shrink-0 gap-1.5 font-semibold"
          >
            {isLoading ? (
              <>
                <span className="size-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Discovering...
              </>
            ) : (
              <>
                <Sparkles className="size-3.5" />
                Run Discovery
              </>
            )}
          </Button>
        </form>

        {/* Quick query suggestion chips */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[11px] text-slate-400 font-medium mr-1">Presets:</span>
          {PRESET_QUERIES.map((preset) => (
            <button
              key={preset}
              type="button"
              onClick={() => {
                setQuery(preset);
              }}
              className="rounded-md bg-slate-50 border border-slate-200/80 px-2 py-0.5 text-[11px] text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors cursor-pointer"
            >
              {preset}
            </button>
          ))}
        </div>

        {/* Filter Toolbar */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2.5 pt-2 border-t border-slate-100">
          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1 block">
              Industry
            </label>
            <Select value={industry} onChange={(e) => setIndustry(e.target.value)}>
              {INDUSTRIES.map((ind) => (
                <option key={ind} value={ind}>
                  {ind}
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1 block">
              Geography
            </label>
            <Select value={geography} onChange={(e) => setGeography(e.target.value)}>
              {GEOGRAPHIES.map((geo) => (
                <option key={geo} value={geo}>
                  {geo}
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1 block">
              Company Size
            </label>
            <Select value={companySize} onChange={(e) => setCompanySize(e.target.value)}>
              {COMPANY_SIZES.map((sz) => (
                <option key={sz} value={sz}>
                  {sz}
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1 block">
              Buying Signal
            </label>
            <Select value={buyingSignal} onChange={(e) => setBuyingSignal(e.target.value)}>
              {SIGNALS.map((sig) => (
                <option key={sig} value={sig}>
                  {sig}
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1 block">
              Result Limit
            </label>
            <Select value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
              <option value={5}>5 candidates</option>
              <option value={10}>10 candidates</option>
              <option value={15}>15 candidates</option>
              <option value={20}>20 candidates</option>
            </Select>
          </div>
        </div>

        {/* Verification Toggle & Filter Reset */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
          <label className="flex items-center gap-2 cursor-pointer select-none text-slate-700">
            <input
              type="checkbox"
              checked={verifySources}
              onChange={(e) => setVerifySources(e.target.checked)}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-600 size-3.5 cursor-pointer"
            />
            <span className="font-medium text-[11px]">
              Verify Primary Sources & Extract Excerpts (live website crawling)
            </span>
          </label>

          <button
            type="button"
            onClick={handleClearFilters}
            className="flex items-center gap-1 text-[11px] text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
          >
            <RotateCcw className="size-3" />
            Reset filters
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="size-4" />
          <AlertTitle>Discovery Search Notice</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Summary metadata bar */}
      {searchResponse && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-1 text-xs text-slate-600">
          <div className="flex items-center gap-3">
            <span className="font-medium text-slate-900">
              Found {searchResponse.total_candidates} candidate{searchResponse.total_candidates === 1 ? "" : "s"}
            </span>
            <span className="text-slate-300">•</span>
            <span className="text-emerald-700 font-semibold flex items-center gap-1">
              <ShieldCheck className="size-3.5" />
              {searchResponse.verified_candidates} verified by source evidence
            </span>
            <span className="text-slate-300">•</span>
            <span className="text-slate-400 font-mono text-[11px]">
              {searchResponse.duration_ms}ms
            </span>
            <span className="text-slate-300">•</span>
            <span className="text-slate-500 text-[11px]">
              Provider: {searchResponse.provider}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-400">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as "score" | "evidence" | "name")}
              className="bg-transparent font-medium text-slate-700 border-none outline-none text-xs cursor-pointer"
            >
              <option value="score">Lead Score (Highest)</option>
              <option value="evidence">Verified Evidence (Most)</option>
              <option value="name">Company Name (A-Z)</option>
            </select>
          </div>
        </div>
      )}

      {/* Loading state skeleton */}
      {isLoading && (
        <div className="rounded-lg border border-slate-200 bg-white overflow-hidden shadow-xs">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-4 w-24" />
          </div>
          <div className="p-4 space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-slate-50 last:border-0">
                <div className="space-y-1.5">
                  <Skeleton className="h-4 w-36" />
                  <Skeleton className="h-3 w-56" />
                </div>
                <Skeleton className="h-6 w-20" />
                <Skeleton className="h-6 w-16" />
                <Skeleton className="h-7 w-24" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty initial state */}
      {!isLoading && !searchResponse && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-200 bg-white p-12 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-blue-50 text-blue-600 mb-3">
            <Search className="size-6" />
          </div>
          <h3 className="text-sm font-semibold text-slate-800">
            Ready to Discover B2B Prospects
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mt-1 mb-4 leading-relaxed">
            Enter a query above or click a preset to search real companies. LeadOS will crawl public sources, verify buying signals, and calculate transparent scores.
          </p>
          <Button onClick={() => handleSearch()} size="sm" className="gap-1.5 font-medium">
            <Sparkles className="size-3.5" />
            Run Sample Discovery
          </Button>
        </div>
      )}

      {/* Results table */}
      {!isLoading && searchResponse && (
        <div className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
          {sortedCandidates.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs">
              No companies matched your specific filter criteria. Try broadening your industry or location filters.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[280px]">Company</TableHead>
                  <TableHead className="w-[180px]">Industry & Location</TableHead>
                  <TableHead>Primary Buying Signal</TableHead>
                  <TableHead className="w-[110px] text-center">Lead Score</TableHead>
                  <TableHead className="w-[120px] text-center">Evidence Status</TableHead>
                  <TableHead className="w-[130px] text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedCandidates.map((candidate) => {
                  const comp = candidate.company;
                  const score = candidate.score;
                  const vCount = candidate.verification_summary.verified;
                  const pCount = candidate.verification_summary.partially_verified;
                  const isSaved = comp.is_saved;

                  return (
                    <TableRow key={comp.id} className="hover:bg-slate-50/70 transition-colors">
                      {/* Company Info */}
                      <TableCell>
                        <div className="flex items-start gap-2.5">
                          <button
                            type="button"
                            onClick={() => handleToggleSave(candidate)}
                            disabled={savingCompanyId === comp.id}
                            className="mt-0.5 text-slate-400 hover:text-amber-500 transition-colors cursor-pointer"
                            title={isSaved ? "Remove from saved leads" : "Save this lead"}
                          >
                            <Star
                              className={`size-4 ${
                                isSaved ? "fill-amber-400 text-amber-500" : ""
                              }`}
                            />
                          </button>
                          <div className="min-w-0">
                            <div className="flex items-center gap-1.5">
                              <span className="font-semibold text-slate-900 truncate">
                                {comp.name}
                              </span>
                              {comp.website_url && (
                                <a
                                  href={comp.website_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-slate-400 hover:text-blue-600 transition-colors inline-flex"
                                  title={`Open ${comp.domain}`}
                                >
                                  <ExternalLink className="size-3" />
                                </a>
                              )}
                            </div>
                            <span className="text-[11px] text-slate-500 font-mono block truncate">
                              {comp.domain}
                            </span>
                            {comp.description && (
                              <p className="text-[11px] text-slate-600 line-clamp-1 mt-0.5 leading-snug">
                                {comp.description}
                              </p>
                            )}
                          </div>
                        </div>
                      </TableCell>

                      {/* Industry & Location */}
                      <TableCell>
                        <div className="space-y-1 text-slate-700">
                          <div className="flex items-center gap-1.5 truncate">
                            <Building2 className="size-3 text-slate-400 shrink-0" />
                            <span className="truncate">{comp.industry || "General / Tech"}</span>
                          </div>
                          {(comp.city || comp.country) && (
                            <div className="flex items-center gap-1.5 text-slate-500 text-[11px] truncate">
                              <MapPin className="size-3 text-slate-400 shrink-0" />
                              <span className="truncate">{comp.city || comp.country}</span>
                            </div>
                          )}
                        </div>
                      </TableCell>

                      {/* Primary Signal */}
                      <TableCell>
                        {candidate.primary_signal ? (
                          <div className="space-y-1">
                            <div className="flex items-center gap-1.5">
                              <Badge variant="outline" className="text-[10px] bg-blue-50 text-blue-700 border-blue-200">
                                {candidate.signals[0]?.signal_type.replace("_", " ") || "Signal"}
                              </Badge>
                              <span className="text-[10px] text-slate-400 font-mono">
                                {Math.round((candidate.signals[0]?.confidence_score || 0.8) * 100)}% conf
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-700 line-clamp-1">
                              {candidate.primary_signal}
                            </p>
                          </div>
                        ) : (
                          <span className="text-slate-400 italic text-[11px]">
                            Candidate indexed (crawling for verified trigger)
                          </span>
                        )}
                      </TableCell>

                      {/* Lead Score */}
                      <TableCell className="text-center">
                        <div className="inline-flex flex-col items-center">
                          <Badge variant={score.score_tier} className="text-xs font-mono px-2 py-0.5">
                            {score.total_score}
                            <span className="text-[10px] font-normal opacity-70">/100</span>
                          </Badge>
                          <span className="text-[10px] text-slate-400 mt-0.5 uppercase tracking-wider font-semibold">
                            {score.score_tier} fit
                          </span>
                        </div>
                      </TableCell>

                      {/* Evidence Summary */}
                      <TableCell className="text-center">
                        <div className="inline-flex flex-col items-center gap-1">
                          {vCount > 0 ? (
                            <Badge variant="verified" className="text-[10px]">
                              <ShieldCheck className="size-3" />
                              {vCount} Verified
                            </Badge>
                          ) : pCount > 0 ? (
                            <Badge variant="partially_verified" className="text-[10px]">
                              {pCount} Partial
                            </Badge>
                          ) : (
                            <Badge variant="unknown" className="text-[10px]">
                              0 Verified
                            </Badge>
                          )}
                          <span className="text-[10px] text-slate-400 font-mono">
                            {candidate.evidence.length} claims checked
                          </span>
                        </div>
                      </TableCell>

                      {/* Actions */}
                      <TableCell className="text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onSelectCompany(comp.id)}
                          className="gap-1 font-medium text-slate-700 hover:text-blue-600 hover:border-blue-300"
                        >
                          Inspect
                          <ChevronRight className="size-3.5" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </div>
      )}
    </div>
  );
}
