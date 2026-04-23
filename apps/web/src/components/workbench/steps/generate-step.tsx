"use client";

import { ArrowRight, Check, Copy, FileText, WandSparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import type { UseWorkbenchReturn } from "../use-workbench";
import {
  confidenceLabel,
  formatPlatform,
  leadSummary,
  scorePercent,
} from "../utils";
import { CandidateMiniCard } from "../shared/candidate-mini-card";
import { OverviewMetric, ScorePill } from "../shared/score-components";
import { WorkflowInfo } from "../layout/workflow-info";

export function GenerateStep({ state }: { state: UseWorkbenchReturn }) {
  const {
    result,
    winnerCandidate,
    resultMode,
    copyText,
    copiedState,
    setScreenStep,
    setSelectedCandidateId,
  } = state;

  if (!result || !winnerCandidate) {
    return null;
  }

  const overviewMetrics = [
    {
      label: "Overall score",
      value: `${scorePercent(winnerCandidate.scores.final_score)}`,
      copy: "Blended narrative and platform score",
    },
    {
      label: "Best opener",
      value:
        winnerCandidate.diagnostics.strongest_sentence !== null
          ? `S${winnerCandidate.diagnostics.strongest_sentence + 1}`
          : "N/A",
      copy: "Top-contributing sentence",
    },
    {
      label: "Momentum confidence",
      value: confidenceLabel(result),
      copy: "Lead over the next strongest candidate",
    },
  ];

  return (
    <section className="mx-auto grid w-full max-w-[1240px] gap-8 lg:grid-cols-[minmax(0,1fr)_340px]">
      <div className="space-y-6">
        <Card className="border-[#e5e5e5] bg-white shadow-[0_8px_24px_rgba(0,0,0,0.05)]">
          <CardHeader className="gap-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge className="rounded-full border-black/15 bg-black text-white">
                    {resultMode === "generate" ? "Recommended" : "Analyzed post"}
                  </Badge>
                  <Badge className="rounded-full border-foreground/10 bg-white/70 text-foreground/70">
                    {formatPlatform(result.platform)}
                  </Badge>
                </div>
                <CardTitle className="text-2xl text-foreground">
                  {resultMode === "generate" ? "Recommended post" : "Post analysis"}
                </CardTitle>
                <CardDescription className="max-w-2xl leading-6">
                  {leadSummary(winnerCandidate)}
                </CardDescription>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <ScorePill label="Overall" value={winnerCandidate.scores.final_score} />
                <ScorePill label="Brain" value={winnerCandidate.scores.brainscore} />
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="rounded-[24px] border border-[#e5e5e5] bg-[#fafafa] p-6">
              <p className="text-[11px] uppercase tracking-[0.24em] text-muted-foreground">
                Draft text
              </p>
              <p className="mt-4 max-w-4xl text-[17px] leading-8 text-[#111111]">
                {result.winner_text}
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              {overviewMetrics.map((metric) => (
                <OverviewMetric
                  key={metric.label}
                  label={metric.label}
                  value={metric.value}
                  copy={metric.copy}
                />
              ))}
            </div>

            <div className="rounded-[22px] border border-[#e5e5e5] bg-[#fafafa] p-4">
              <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
                Recommendation
              </p>
              <p className="mt-2 text-sm leading-7 text-[#111111]/82">{result.explanation}</p>
            </div>

            <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_320px]">
              <div className="rounded-[22px] border border-[#e5e5e5] bg-[#fafafa] p-4">
                <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
                  Run metadata
                </p>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                      Model
                    </p>
                    <p className="mt-1 text-sm text-[#111111]/82">{result.llm_model}</p>
                  </div>
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                      Run ID
                    </p>
                    <p className="mt-1 break-all font-mono text-xs leading-6 text-[#111111]/82">
                      {result.run_id}
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-[22px] border border-[#e5e5e5] bg-[#fafafa] p-4">
                <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
                  Log file
                </p>
                <p className="mt-2 break-all font-mono text-xs leading-6 text-[#111111]/82">
                  {result.log_file_path ?? "No log file was returned for this run."}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Button className="rounded-full px-5" onClick={() => copyText("winner", result.winner_text)}>
                {copiedState === "winner" ? (
                  <>
                    <Check />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy />
                    Copy post
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                className="rounded-full bg-white/76"
                onClick={() => copyText("log", result.log_file_path)}
              >
                {copiedState === "log" ? (
                  <>
                    <Check />
                    Copied log path
                  </>
                ) : (
                  <>
                    <FileText />
                    Copy log path
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                className="rounded-full bg-white/76"
                onClick={() => setScreenStep("compare")}
              >
                Open compare view
                <ArrowRight />
              </Button>
              {resultMode === "generate" ? (
                <Button
                  variant="outline"
                  className="rounded-full bg-white/76"
                  onClick={() => setScreenStep("refine")}
                >
                  Refine winner
                  <WandSparkles />
                </Button>
              ) : null}
            </div>
          </CardContent>
        </Card>

        {result.candidates.length > 1 ? (
          <Card className="border-[#e5e5e5] bg-white shadow-[0_8px_24px_rgba(0,0,0,0.05)]">
            <CardHeader className="gap-3">
              <CardTitle className="text-xl text-foreground">
                {resultMode === "generate" ? "Alternatives at a glance" : "Submitted versions"}
              </CardTitle>
              <CardDescription className="leading-6">
                Full diagnostics belong in the compare step.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 lg:grid-cols-2">
              {result.candidates.map((candidate, index) => (
                <CandidateMiniCard
                  key={candidate.id}
                  candidate={candidate}
                  rank={index + 1}
                  isWinner={candidate.id === result.recommended_candidate_id}
                  onOpen={() => {
                    setSelectedCandidateId(candidate.id);
                    setScreenStep("compare");
                  }}
                />
              ))}
            </CardContent>
          </Card>
        ) : null}
      </div>

      <WorkflowInfo currentStep="results" />
    </section>
  );
}
