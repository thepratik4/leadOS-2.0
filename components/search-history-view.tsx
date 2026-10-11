"use client";

import * as React from "react";
import {
  History,
  RotateCcw,
  Clock,
  Search,
  CheckCircle2,
  AlertCircle,
  Database,
} from "lucide-react";
import { api, type SearchRunResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
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

interface SearchHistoryViewProps {
  onRerunQuery: (query: string) => void;
}

export function SearchHistoryView({ onRerunQuery }: SearchHistoryViewProps) {
  const [runs, setRuns] = React.useState<SearchRunResponse[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);

  const loadHistory = React.useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.getSearchHistory(25);
      setRuns(data);
    } catch (err) {
      console.error("Failed to load search history", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Search History
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Audit log of all discovery runs persisted in the database.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={loadHistory}
          disabled={isLoading}
          className="gap-1.5"
        >
          <RotateCcw className="size-3.5" />
          Refresh History
        </Button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && runs.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-200 bg-white p-12 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-slate-100 text-slate-500 mb-3">
            <History className="size-6" />
          </div>
          <h3 className="text-sm font-semibold text-slate-800">
            No search runs logged yet
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mt-1 leading-relaxed">
            Execute a discovery search from the Discover tab to see audit runs and latency metrics logged here.
          </p>
        </div>
      )}

      {/* Runs Table */}
      {!isLoading && runs.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[300px]">Search Query</TableHead>
                <TableHead>Filters Applied</TableHead>
                <TableHead className="w-[120px] text-center">Candidates</TableHead>
                <TableHead className="w-[130px]">Provider</TableHead>
                <TableHead className="w-[110px] text-center">Latency</TableHead>
                <TableHead className="w-[160px]">Executed At</TableHead>
                <TableHead className="w-[100px] text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {runs.map((run) => {
                let parsedFilters: Record<string, string | null> = {};
                try {
                  parsedFilters = JSON.parse(run.filters_json);
                } catch {
                  // ignore
                }

                const activeFilters = Object.entries(parsedFilters)
                  .filter(([, v]) => Boolean(v))
                  .map(([k, v]) => `${k}: ${v}`);

                return (
                  <TableRow key={run.id} className="hover:bg-slate-50/70 transition-colors">
                    {/* Query */}
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Search className="size-3.5 text-slate-400 shrink-0" />
                        <span className="font-semibold text-slate-900 text-xs truncate max-w-xs">
                          {run.query}
                        </span>
                      </div>
                    </TableCell>

                    {/* Filters */}
                    <TableCell>
                      {activeFilters.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {activeFilters.map((f, i) => (
                            <Badge
                              key={i}
                              variant="outline"
                              className="text-[10px] px-1.5 py-0 bg-slate-50 text-slate-600"
                            >
                              {f}
                            </Badge>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-400 italic text-[11px]">No extra filters</span>
                      )}
                    </TableCell>

                    {/* Candidates Count */}
                    <TableCell className="text-center font-mono font-medium text-xs">
                      {run.candidate_count}
                    </TableCell>

                    {/* Provider */}
                    <TableCell>
                      <span className="text-xs text-slate-700 font-medium">
                        {run.provider}
                      </span>
                    </TableCell>

                    {/* Latency */}
                    <TableCell className="text-center font-mono text-[11px] text-slate-500">
                      {run.duration_ms}ms
                    </TableCell>

                    {/* Timestamp */}
                    <TableCell className="text-slate-500 text-[11px] font-mono">
                      {new Date(run.created_at).toLocaleString()}
                    </TableCell>

                    {/* Actions */}
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onRerunQuery(run.query)}
                        className="h-7 text-xs gap-1 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                      >
                        <RotateCcw className="size-3" />
                        Rerun
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
