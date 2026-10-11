"use client";

import * as React from "react";
import {
  ExternalLink,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Mail,
  Copy,
  Check,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Sparkles,
  Send,
  Building2,
  MapPin,
  Users,
  Calendar,
  Lock,
  ArrowRight,
} from "lucide-react";
import {
  api,
  type CompanyDetailResponse,
  type CompanyDossierResponse,
  type EvidenceResponse,
  type OutreachDraftResponse,
} from "@/lib/api";
import { Sheet, SheetHeader, SheetContent, SheetFooter } from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";

interface CompanyDetailSheetProps {
  companyId: string | null;
  onClose: () => void;
  onLeadSavedChange: () => void;
}

export function CompanyDetailSheet({
  companyId,
  onClose,
  onLeadSavedChange,
}: CompanyDetailSheetProps) {
  const [activeTab, setActiveTab] = React.useState("score");
  const [isLoading, setIsLoading] = React.useState(false);
  const [company, setCompany] = React.useState<CompanyDetailResponse | null>(null);
  const [dossier, setDossier] = React.useState<CompanyDossierResponse | null>(null);
  const [outreach, setOutreach] = React.useState<OutreachDraftResponse | null>(null);
  const [isGeneratingOutreach, setIsGeneratingOutreach] = React.useState(false);
  const [copied, setCopied] = React.useState(false);

  // Live Claim Verification sub-form states
  const [customClaimType, setCustomClaimType] = React.useState("hiring");
  const [customClaimValue, setCustomClaimValue] = React.useState("");
  const [customSourceUrl, setCustomSourceUrl] = React.useState("");
  const [isVerifyingClaim, setIsVerifyingClaim] = React.useState(false);
  const [verifyNotice, setVerifyNotice] = React.useState<string | null>(null);

  // Fetch company details & dossier when opened
  React.useEffect(() => {
    if (!companyId) {
      setCompany(null);
      setDossier(null);
      setOutreach(null);
      return;
    }

    let isMounted = true;
    setIsLoading(true);

    const loadData = async () => {
      try {
        const [compData, dosData] = await Promise.all([
          api.getCompanyDetails(companyId),
          api.getCompanyDossier(companyId).catch(() => null),
        ]);
        if (isMounted) {
          setCompany(compData);
          setDossier(dosData);
          setCustomSourceUrl(compData.website_url || `https://${compData.domain}`);
        }
      } catch (err) {
        console.error("Failed to load company details", err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    loadData();
    return () => {
      isMounted = false;
    };
  }, [companyId]);

  // Handle live claim verification
  const handleVerifyNewClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!company || !customClaimValue.trim() || !customSourceUrl.trim()) return;

    setIsVerifyingClaim(true);
    setVerifyNotice(null);

    try {
      const newEv = await api.verifyClaim(company.id, {
        claim_type: customClaimType,
        claim_value: customClaimValue.trim(),
        source_url: customSourceUrl.trim(),
      });

      // Refresh company details to reflect new evidence and recalculate score
      const updated = await api.getCompanyDetails(company.id);
      setCompany(updated);

      const dosData = await api.getCompanyDossier(company.id).catch(() => null);
      setDossier(dosData);

      setVerifyNotice(
        `Claim evaluated: Status is ${newEv.verification_status.toUpperCase()}. ${
          newEv.validation_notes || ""
        }`
      );
      setCustomClaimValue("");
    } catch (err: unknown) {
      const msg =
        typeof err === "object" && err !== null && "message" in err
          ? (err as { message: string }).message
          : "Verification failed. Check that URL is public and safe.";
      setVerifyNotice(`Error: ${msg}`);
    } finally {
      setIsVerifyingClaim(false);
    }
  };

  // Generate Grounded Outreach
  const handleGenerateOutreach = async () => {
    if (!company) return;
    setIsGeneratingOutreach(true);
    try {
      const resp = await api.draftOutreach(company.id);
      setOutreach(resp);
    } catch (err) {
      console.error("Failed to draft outreach", err);
    } finally {
      setIsGeneratingOutreach(false);
    }
  };

  const handleCopyOutreach = () => {
    if (!outreach || !outreach.body_text) return;
    const text = `Subject: ${outreach.subject_line}\n\n${outreach.body_text}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!companyId) return null;

  return (
    <Sheet open={Boolean(companyId)} onOpenChange={(open) => !open && onClose()}>
      {isLoading || !company ? (
        <div className="p-6 space-y-4">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-32" />
          <div className="pt-6 space-y-3">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        </div>
      ) : (
        <>
          {/* Header */}
          <SheetHeader onClose={onClose}>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-900 tracking-tight">
                  {company.name}
                </h2>
                {company.lead_score !== null && (
                  <Badge variant={company.score_tier || "default"} className="font-mono text-xs">
                    {company.lead_score}/100
                  </Badge>
                )}
                {company.verified_evidence_count > 0 && (
                  <Badge variant="verified" className="text-[10px]">
                    <ShieldCheck className="size-3" />
                    Verified
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-500 font-mono">
                <a
                  href={company.website_url || `https://${company.domain}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-blue-600 transition-colors inline-flex items-center gap-1"
                >
                  {company.domain}
                  <ExternalLink className="size-3" />
                </a>
                <span>•</span>
                <span>{company.industry || "General Industry"}</span>
                {company.country && (
                  <>
                    <span>•</span>
                    <span>{company.country}</span>
                  </>
                )}
              </div>
            </div>
          </SheetHeader>

          {/* Navigation Tabs */}
          <div className="px-5 pt-3 border-b border-slate-100 bg-white">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="w-full justify-start space-x-1">
                <TabsTrigger value="score">Lead Score</TabsTrigger>
                <TabsTrigger value="evidence">
                  Evidence Explorer ({company.evidence.length})
                </TabsTrigger>
                <TabsTrigger value="dossier">Company Dossier</TabsTrigger>
                <TabsTrigger value="outreach">Grounded Outreach</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          {/* Main Content Area */}
          <SheetContent>
            {/* 1. SCORE BREAKDOWN TAB */}
            {activeTab === "score" && (
              <div className="space-y-4">
                {company.score_result && (
                  <>
                    {/* Score summary banner */}
                    <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-4 flex items-center justify-between">
                      <div>
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 block">
                          Deterministic Lead Score
                        </span>
                        <div className="flex items-baseline gap-2 mt-0.5">
                          <span className="text-3xl font-extrabold text-slate-900 font-mono">
                            {company.score_result.total_score}
                          </span>
                          <span className="text-xs text-slate-500">/ 100 possible</span>
                          <Badge variant={company.score_result.score_tier} className="ml-1 uppercase text-[10px]">
                            {company.score_result.score_tier} Tier
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-600 mt-1 max-w-md">
                          {company.score_result.scoring_notes}
                        </p>
                      </div>

                      <div className="text-right">
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 block">
                          Data Quality Rating
                        </span>
                        <span className="text-2xl font-bold font-mono text-emerald-700">
                          {company.score_result.data_quality_score}%
                        </span>
                        <span className="text-[10px] text-slate-400 block mt-0.5">
                          Primary source substantiated
                        </span>
                      </div>
                    </div>

                    {/* Dimensions Breakdown Cards */}
                    <div className="space-y-2.5">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                        Scoring Dimensions (5-Factor Formula)
                      </h4>

                      {company.score_result.breakdown.map((item) => (
                        <div
                          key={item.category}
                          className="rounded-lg border border-slate-200 bg-white p-3 space-y-1.5 shadow-2xs"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-slate-800 capitalize">
                              {item.category.replace("_", " ")}
                            </span>
                            <span className="text-xs font-mono font-bold text-slate-900">
                              {item.awarded_points}{" "}
                              <span className="font-normal text-slate-400">/ {item.max_points} pts</span>
                            </span>
                          </div>
                          <p className="text-xs text-slate-600 leading-snug">
                            {item.explanation}
                          </p>
                        </div>
                      ))}
                    </div>

                    {/* Matched vs Missing Criteria */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                      <div className="rounded-lg border border-emerald-100 bg-emerald-50/40 p-3 space-y-2">
                        <span className="text-xs font-semibold text-emerald-800 flex items-center gap-1.5">
                          <CheckCircle2 className="size-3.5 text-emerald-600" />
                          Matched Criteria ({company.score_result.matched_criteria.length})
                        </span>
                        <ul className="text-xs text-emerald-900 space-y-1">
                          {company.score_result.matched_criteria.map((mc, idx) => (
                            <li key={idx} className="flex items-start gap-1.5">
                              <span className="text-emerald-500 font-bold">•</span>
                              <span>{mc}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="rounded-lg border border-slate-200 bg-slate-50/50 p-3 space-y-2">
                        <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                          <AlertTriangle className="size-3.5 text-amber-500" />
                          Missing Evidence ({company.score_result.missing_evidence.length})
                        </span>
                        <ul className="text-xs text-slate-600 space-y-1">
                          {company.score_result.missing_evidence.length === 0 ? (
                            <li className="italic text-slate-400">All required signals substantiated.</li>
                          ) : (
                            company.score_result.missing_evidence.map((me, idx) => (
                              <li key={idx} className="flex items-start gap-1.5">
                                <span className="text-amber-500 font-bold">•</span>
                                <span>{me}</span>
                              </li>
                            ))
                          )}
                        </ul>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* 2. EVIDENCE EXPLORER TAB */}
            {activeTab === "evidence" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">
                    Inspecting {company.evidence.length} claims tracked against primary source content.
                  </span>
                </div>

                {/* Evidence List */}
                <div className="space-y-3">
                  {company.evidence.map((ev) => (
                    <div
                      key={ev.id}
                      className="rounded-lg border border-slate-200 bg-white p-3.5 space-y-2.5 shadow-2xs hover:border-slate-300 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-2">
                            <Badge variant={ev.verification_status} className="capitalize text-[10px]">
                              {ev.verification_status.replace("_", " ")}
                            </Badge>
                            <span className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                              {ev.claim_type.replace("_", " ")}
                            </span>
                          </div>
                          <p className="text-xs text-slate-800 font-medium mt-1">
                            {ev.claim_value}
                          </p>
                        </div>

                        <a
                          href={ev.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="shrink-0 text-slate-400 hover:text-blue-600 transition-colors inline-flex p-1"
                          title="Open primary source"
                        >
                          <ExternalLink className="size-3.5" />
                        </a>
                      </div>

                      {/* Excerpt callout */}
                      {ev.source_excerpt && (
                        <div className="rounded-md border-l-2 border-emerald-500 bg-slate-50 p-2.5 text-xs text-slate-700 italic font-serif leading-relaxed">
                          "{ev.source_excerpt}"
                        </div>
                      )}

                      {/* Source metadata footer */}
                      <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-400 border-t border-slate-100 pt-2 gap-2">
                        <span className="font-medium text-slate-600">
                          Source: {ev.source_name} ({ev.source_category})
                        </span>
                        <span className="font-mono">
                          Crawled: {new Date(ev.retrieval_timestamp).toLocaleDateString()}
                        </span>
                      </div>

                      {ev.validation_notes && (
                        <p className="text-[11px] text-slate-500 bg-slate-50/50 p-1.5 rounded text-left">
                          <span className="font-semibold text-slate-600">Validator Note:</span>{" "}
                          {ev.validation_notes}
                        </p>
                      )}
                    </div>
                  ))}
                </div>

                {/* Live Claim Verification Sub-Form */}
                <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50/60 p-4 space-y-3 mt-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="size-4 text-blue-600" />
                    <h4 className="text-xs font-bold text-slate-800">
                      Live Claim Verification Engine
                    </h4>
                  </div>
                  <p className="text-xs text-slate-500">
                    Test the real-time SSRF-safe scraper and factual validator against any live URL.
                  </p>

                  <form onSubmit={handleVerifyNewClaim} className="space-y-2.5">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      <div>
                        <label className="text-[10px] font-semibold text-slate-500 uppercase block mb-1">
                          Claim Type
                        </label>
                        <select
                          value={customClaimType}
                          onChange={(e) => setCustomClaimType(e.target.value)}
                          className="w-full text-xs rounded-md border border-slate-200 bg-white p-1.5"
                        >
                          <option value="hiring">Hiring / Team</option>
                          <option value="offering">Core Offering</option>
                          <option value="tech_stack">Tech Infrastructure</option>
                          <option value="headquarters">Headquarters</option>
                          <option value="funding">Funding / Metrics</option>
                        </select>
                      </div>

                      <div className="sm:col-span-2">
                        <label className="text-[10px] font-semibold text-slate-500 uppercase block mb-1">
                          Target URL (Must be HTTP/HTTPS)
                        </label>
                        <Input
                          value={customSourceUrl}
                          onChange={(e) => setCustomSourceUrl(e.target.value)}
                          placeholder="https://company.com/careers"
                          required
                          className="h-8 text-xs"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-[10px] font-semibold text-slate-500 uppercase block mb-1">
                        Specific Claim to Verify
                      </label>
                      <Input
                        value={customClaimValue}
                        onChange={(e) => setCustomClaimValue(e.target.value)}
                        placeholder="e.g. 'Hiring 5 backend engineers' or 'Built on Python & AWS'"
                        required
                        className="h-8 text-xs"
                      />
                    </div>

                    <Button
                      type="submit"
                      size="sm"
                      disabled={isVerifyingClaim || !customClaimValue.trim()}
                      className="gap-1.5 w-full font-semibold"
                    >
                      {isVerifyingClaim ? "Scraping & Verifying..." : "Evaluate Claim Against Source"}
                    </Button>
                  </form>

                  {verifyNotice && (
                    <div className="rounded-md p-2.5 text-xs bg-white border border-slate-200 text-slate-700">
                      {verifyNotice}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 3. COMPANY DOSSIER TAB */}
            {activeTab === "dossier" && (
              <div className="space-y-4">
                {dossier ? (
                  <>
                    <div className="rounded-lg border border-slate-200 bg-white p-3.5 space-y-1">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
                        Dossier Integrity Summary
                      </span>
                      <p className="text-xs text-slate-800 font-medium">
                        {dossier.data_quality_summary}
                      </p>
                    </div>

                    {/* Verified Facts */}
                    <div className="space-y-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1.5">
                        <ShieldCheck className="size-3.5 text-emerald-600" />
                        Verified Facts ({dossier.verified_facts.length})
                      </span>
                      {dossier.verified_facts.length === 0 ? (
                        <p className="text-xs text-slate-400 italic">No verified facts recorded yet.</p>
                      ) : (
                        <div className="space-y-1.5">
                          {dossier.verified_facts.map((fact, idx) => (
                            <div
                              key={idx}
                              className="rounded-md border border-slate-200 bg-white p-2.5 text-xs space-y-1"
                            >
                              <p className="font-semibold text-slate-900">{fact.statement}</p>
                              {fact.source_url && (
                                <a
                                  href={fact.source_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-[11px] text-blue-600 hover:underline flex items-center gap-1"
                                >
                                  {fact.source_name || "Primary Source"} <ExternalLink className="size-2.5" />
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Grounded Inferences */}
                    <div className="space-y-2 pt-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-blue-800 flex items-center gap-1.5">
                        <Sparkles className="size-3.5 text-blue-600" />
                        Grounded Inferences ({dossier.inferences.length})
                      </span>
                      <p className="text-[11px] text-slate-500">
                        Derived solely from primary source-verified facts; never hallucinated.
                      </p>
                      {dossier.inferences.length === 0 ? (
                        <p className="text-xs text-slate-400 italic">No inferences generated.</p>
                      ) : (
                        <div className="space-y-1.5">
                          {dossier.inferences.map((inf, idx) => (
                            <div
                              key={idx}
                              className="rounded-md border border-blue-100 bg-blue-50/30 p-2.5 text-xs space-y-1"
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-bold text-slate-900">{inf.inference}</span>
                                <Badge variant="outline" className="text-[10px] uppercase">
                                  {inf.confidence} conf
                                </Badge>
                              </div>
                              <p className="text-[11px] text-slate-600">{inf.reasoning}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Recommendations */}
                    <div className="space-y-2 pt-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                        Recommended Next Steps
                      </span>
                      <ul className="space-y-1 text-xs text-slate-700">
                        {dossier.recommendations.map((rec, idx) => (
                          <li key={idx} className="flex items-start gap-2 bg-slate-50 p-2 rounded">
                            <ArrowRight className="size-3 text-slate-400 shrink-0 mt-0.5" />
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </>
                ) : (
                  <p className="text-xs text-slate-400">Loading dossier report...</p>
                )}
              </div>
            )}

            {/* 4. GROUNDED OUTREACH TAB */}
            {activeTab === "outreach" && (
              <div className="space-y-4">
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3.5 space-y-1.5">
                  <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                    <Mail className="size-4 text-blue-600" />
                    Evidence-Grounded Outreach Drafting
                  </span>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    LeadOS only crafts outreach when substantiated by an active, primary source-verified trigger (e.g. engineering hiring or platform tech stack). If sufficient evidence is lacking, outreach is blocked to protect sender credibility.
                  </p>
                </div>

                {!outreach && (
                  <div className="text-center py-6">
                    <Button
                      onClick={handleGenerateOutreach}
                      disabled={isGeneratingOutreach}
                      className="gap-2 font-semibold"
                    >
                      {isGeneratingOutreach ? "Evaluating Triggers..." : "Draft Evidence-Grounded Outreach"}
                    </Button>
                  </div>
                )}

                {outreach && (
                  <div className="space-y-3">
                    {outreach.has_sufficient_evidence ? (
                      <div className="space-y-3">
                        <Alert variant="success">
                          <CheckCircle2 className="size-4" />
                          <AlertTitle>Verified Trigger Found</AlertTitle>
                          <AlertDescription>
                            Draft grounded in: "{outreach.trigger_summary}"
                          </AlertDescription>
                        </Alert>

                        {/* Subject */}
                        <div className="space-y-1">
                          <span className="text-[10px] font-semibold text-slate-400 uppercase">
                            Subject Line
                          </span>
                          <div className="p-2.5 rounded-md border border-slate-200 bg-white text-xs font-semibold text-slate-900 font-mono">
                            {outreach.subject_line}
                          </div>
                        </div>

                        {/* Body */}
                        <div className="space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-semibold text-slate-400 uppercase">
                              Email Body (Verifiable Excerpt Citing)
                            </span>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={handleCopyOutreach}
                              className="h-6 text-[11px] gap-1"
                            >
                              {copied ? (
                                <>
                                  <Check className="size-3 text-emerald-600" />
                                  Copied
                                </>
                              ) : (
                                <>
                                  <Copy className="size-3" />
                                  Copy
                                </>
                              )}
                            </Button>
                          </div>
                          <div className="p-3.5 rounded-md border border-slate-200 bg-white text-xs text-slate-800 whitespace-pre-wrap leading-relaxed">
                            {outreach.body_text}
                          </div>
                        </div>

                        {/* Cited Facts */}
                        <div className="rounded-md border border-slate-200 bg-slate-50 p-2.5 space-y-1">
                          <span className="text-[10px] font-semibold text-slate-500 uppercase block">
                            Substantiated Facts Referenced
                          </span>
                          <ul className="text-[11px] text-slate-600 space-y-0.5">
                            {outreach.facts_referenced.map((f, i) => (
                              <li key={i}>• {f}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ) : (
                      <Alert variant="warning">
                        <AlertTriangle className="size-4" />
                        <AlertTitle>Outreach Generation Guard Triggered</AlertTitle>
                        <AlertDescription>{outreach.status_reason}</AlertDescription>
                      </Alert>
                    )}
                  </div>
                )}
              </div>
            )}
          </SheetContent>

          {/* Footer */}
          <SheetFooter>
            <Button variant="outline" size="sm" onClick={onClose}>
              Close Inspector
            </Button>
          </SheetFooter>
        </>
      )}
    </Sheet>
  );
}
