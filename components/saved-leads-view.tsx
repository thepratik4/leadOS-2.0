"use client";

import * as React from "react";
import {
  BookmarkCheck,
  Download,
  Trash2,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Edit2,
  Check,
  Building2,
  MapPin,
  Calendar,
} from "lucide-react";
import { api, type SavedLeadResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

interface SavedLeadsViewProps {
  onSelectCompany: (companyId: string) => void;
  onLeadChange: () => void;
}

const STATUS_OPTIONS = [
  { value: "all", label: "All Statuses" },
  { value: "new", label: "New Lead" },
  { value: "in_review", label: "In Review" },
  { value: "contacted", label: "Contacted" },
  { value: "qualified", label: "Qualified" },
  { value: "disqualified", label: "Disqualified" },
];

export function SavedLeadsView({
  onSelectCompany,
  onLeadChange,
}: SavedLeadsViewProps) {
  const [leads, setLeads] = React.useState<SavedLeadResponse[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [filterStatus, setFilterStatus] = React.useState("all");
  const [editingLeadId, setEditingLeadId] = React.useState<string | null>(null);
  const [editingNotes, setEditingNotes] = React.useState("");

  const loadSavedLeads = React.useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.listSavedLeads();
      setLeads(data);
    } catch (err) {
      console.error("Failed to load saved leads", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadSavedLeads();
  }, [loadSavedLeads]);

  const handleUpdateStatus = async (leadId: string, newStatus: string) => {
    try {
      await api.updateSavedLead(leadId, { status: newStatus });
      setLeads((prev) =>
        prev.map((l) =>
          l.id === leadId
            ? { ...l, status: newStatus as SavedLeadResponse["status"] }
            : l
        )
      );
      onLeadChange();
    } catch (err) {
      console.error("Failed to update status", err);
    }
  };

  const handleSaveNotes = async (leadId: string) => {
    try {
      await api.updateSavedLead(leadId, { notes: editingNotes });
      setLeads((prev) =>
        prev.map((l) => (l.id === leadId ? { ...l, notes: editingNotes } : l))
      );
      setEditingLeadId(null);
      onLeadChange();
    } catch (err) {
      console.error("Failed to save notes", err);
    }
  };

  const handleDeleteLead = async (leadId: string) => {
    if (!window.confirm("Remove this lead from saved list?")) return;
    try {
      await api.deleteSavedLead(leadId);
      setLeads((prev) => prev.filter((l) => l.id !== leadId));
      onLeadChange();
    } catch (err) {
      console.error("Failed to delete lead", err);
    }
  };

  const filteredLeads = React.useMemo(() => {
    if (filterStatus === "all") return leads;
    return leads.filter((l) => l.status === filterStatus);
  }, [leads, filterStatus]);

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Saved Prospects ({leads.length})
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage your prioritized prospect list, track contact statuses, and export to CSV.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="w-36 h-8 text-xs"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </Select>

          {leads.length > 0 && (
            <a
              href={api.getExportSavedLeadsUrl()}
              download="leados_saved_leads.csv"
              className="inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-md text-xs font-medium border border-slate-200 bg-white text-slate-800 shadow-xs hover:bg-slate-50 h-8 px-3 transition-colors"
            >
              <Download className="size-3.5" />
              Download CSV
            </a>
          )}
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && leads.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-200 bg-white p-12 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-slate-100 text-slate-500 mb-3">
            <BookmarkCheck className="size-6" />
          </div>
          <h3 className="text-sm font-semibold text-slate-800">
            No saved leads yet
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mt-1 leading-relaxed">
            When you discover promising prospects, click the star icon to save them here for prioritization and outreach.
          </p>
        </div>
      )}

      {/* Leads Table */}
      {!isLoading && leads.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white shadow-xs overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[280px]">Company</TableHead>
                <TableHead className="w-[160px]">Status</TableHead>
                <TableHead>User Notes</TableHead>
                <TableHead className="w-[120px] text-center">Verified Evidence</TableHead>
                <TableHead className="w-[130px] text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLeads.map((lead) => {
                const comp = lead.company;
                const isEditing = editingLeadId === lead.id;

                return (
                  <TableRow key={lead.id} className="hover:bg-slate-50/70 transition-colors">
                    {/* Company */}
                    <TableCell>
                      {comp ? (
                        <div className="space-y-0.5">
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
                              >
                                <ExternalLink className="size-3" />
                              </a>
                            )}
                          </div>
                          <span className="text-[11px] text-slate-500 font-mono block">
                            {comp.domain}
                          </span>
                          <span className="text-[11px] text-slate-400 block">
                            {comp.industry || "General Industry"}
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-400 italic">Company details archived</span>
                      )}
                    </TableCell>

                    {/* Status Dropdown */}
                    <TableCell>
                      <select
                        value={lead.status}
                        onChange={(e) => handleUpdateStatus(lead.id, e.target.value)}
                        className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700 shadow-2xs cursor-pointer capitalize"
                      >
                        <option value="new">New</option>
                        <option value="in_review">In Review</option>
                        <option value="contacted">Contacted</option>
                        <option value="qualified">Qualified</option>
                        <option value="disqualified">Disqualified</option>
                      </select>
                    </TableCell>

                    {/* User Notes */}
                    <TableCell>
                      {isEditing ? (
                        <div className="flex items-center gap-1.5">
                          <Input
                            value={editingNotes}
                            onChange={(e) => setEditingNotes(e.target.value)}
                            placeholder="Add lead notes..."
                            className="h-7 text-xs"
                            autoFocus
                          />
                          <Button
                            size="sm"
                            onClick={() => handleSaveNotes(lead.id)}
                            className="h-7 px-2"
                          >
                            <Check className="size-3" />
                          </Button>
                        </div>
                      ) : (
                        <div className="flex items-center justify-between group/note max-w-sm">
                          <p className="text-xs text-slate-600 truncate">
                            {lead.notes || <span className="text-slate-400 italic">No notes</span>}
                          </p>
                          <button
                            type="button"
                            onClick={() => {
                              setEditingLeadId(lead.id);
                              setEditingNotes(lead.notes || "");
                            }}
                            className="opacity-0 group-hover/note:opacity-100 text-slate-400 hover:text-slate-700 p-1 cursor-pointer transition-opacity"
                            title="Edit notes"
                          >
                            <Edit2 className="size-3" />
                          </button>
                        </div>
                      )}
                    </TableCell>

                    {/* Evidence count */}
                    <TableCell className="text-center">
                      <Badge variant="verified" className="text-[10px]">
                        <ShieldCheck className="size-3" />
                        {comp ? comp.verified_evidence_count : 0} Verified
                      </Badge>
                    </TableCell>

                    {/* Actions */}
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {comp && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onSelectCompany(comp.id)}
                            className="h-7 text-xs gap-1"
                          >
                            Inspect
                            <ChevronRight className="size-3" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDeleteLead(lead.id)}
                          className="h-7 w-7 text-slate-400 hover:text-red-600 hover:bg-red-50"
                          title="Remove saved lead"
                        >
                          <Trash2 className="size-3.5" />
                        </Button>
                      </div>
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
