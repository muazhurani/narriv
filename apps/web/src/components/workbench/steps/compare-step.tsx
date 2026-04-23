"use client";

import { ArrowLeft, MoveRight } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

import { scoreRows } from "../constants";
import type { UseWorkbenchReturn } from "../use-workbench";
import {
  chartData,
  compareChartData,
  formatPlatform,
  leadSummary,
  railTone,
  scorePercent,
  sentenceTone,
  sentenceWindowLabel,
  weaknessSummary,
} from "../utils";
import {
  CompareInsight,
  MiniMetric,
  ScorePill,
  ScoreRow,
  StepperTab,
} from "../shared/score-components";
import { WorkflowInfo } from "../layout/workflow-info";

export function CompareStep({ state }: { state: UseWorkbenchReturn }) {
  const {
    result,
    selectedCandidate,
    compareCandidate,
    compareCandidateId,
    setCompareCandidateId,
    setSelectedCandidateId,
    runnerUp,
    compareView,
    setCompareView,
    resultMode,
    setScreenStep,
  } = state;

  if (!result || !selectedCandidate) {
    return null;
  }

  return (
    <section className="mx-auto w-full max-w-[1320px] space-y-6">
      <div className="grid gap-6 xl:grid-cols-[280px_minmax(0,1fr)_320px]">
        <aside className="xl:sticky xl:top-4 xl:self-start">
          <Card className="border-[#e5e5e5] bg-white shadow-[0_8px_24px_rgba(0,0,0,0.05)]">
            <CardHeader className="gap-2 pb-3">
              <CardTitle className="text-lg text-foreground">Candidate rail</CardTitle>
              <CardDescription className="text-xs leading-5">
                Select the draft you want to inspect.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {result.candidates.map((candidate, index) => {
                const isActive = candidate.id === selectedCandidate.id;
                const isWinner = candidate.id === result.recommended_candidate_id;
                const isCompare = candidate.id === compareCandidateId;

                return (
                  <div
                    key={candidate.id}
                    className={cn("rounded-[16px] border p-3 transition", railTone(isActive))}
                  >
                    <button
                      type="button"
                      className="w-full text-left"
                      onClick={() => setSelectedCandidateId(candidate.id)}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex flex-wrap items-center gap-1.5">
                            <Badge className="rounded-full border-foreground/10 bg-stone-100 text-foreground text-[10px]">
                              #{index + 1}
                            </Badge>
                            {isWinner ? (
                              <Badge className="rounded-full border-black/15 bg-black text-white text-[10px]">
                                Winner
                              </Badge>
                            ) : null}
                            {isCompare ? (
                              <Badge className="rounded-full border-stone-300 bg-stone-100 text-stone-700 text-[10px]">
                                Compare
                              </Badge>
                            ) : null}
                          </div>
                          <p className="mt-2 text-[13px] font-medium text-foreground">
                            {candidate.strategy}
                          </p>
                          <p className="mt-1 text-[11px] leading-5 text-muted-foreground">
                            {weaknessSummary(candidate)}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                            Score
                          </p>
                          <p className="mt-1 text-lg font-semibold text-foreground">
                            {scorePercent(candidate.scores.final_score)}
                          </p>
                        </div>
                      </div>
                    </button>

                    <div className="mt-3 h-10 rounded-xl border border-[#e5e5e5] bg-[#fafafa] px-2 py-1">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData(candidate)}>
                          <Line
                            type="monotone"
                            dataKey="energy"
                            stroke={isWinner ? "#111111" : "#7a7a7a"}
                            strokeWidth={2}
                            dot={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>

                    <Button
                      variant="outline"
                      size="sm"
                      className="mt-3 w-full rounded-full bg-white/76 text-xs"
                      onClick={() =>
                        setCompareCandidateId(
                          candidate.id === compareCandidateId ? null : candidate.id,
                        )
                      }
                    >
                      {candidate.id === compareCandidateId ? "Remove compare" : "Compare"}
                    </Button>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </aside>

        <div className="flex min-w-0 flex-col gap-6">
          <Card className="border-[#e5e5e5] bg-white shadow-[0_8px_24px_rgba(0,0,0,0.05)]">
            <CardHeader className="gap-4 border-b border-[#ececec] pb-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge className="rounded-full border-foreground/10 bg-white/70 text-foreground/70">
                      {selectedCandidate.id === result.recommended_candidate_id
                        ? "Recommended"
                        : "Alternative"}
                    </Badge>
                    <Badge className="rounded-full border-foreground/10 bg-white/70 text-foreground/70">
                      {formatPlatform(result.platform)}
                    </Badge>
                  </div>
                  <CardTitle className="text-2xl text-foreground">
                    {selectedCandidate.strategy}
                  </CardTitle>
                  <CardDescription className="max-w-2xl leading-6">
                    {selectedCandidate.reason}
                  </CardDescription>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <ScorePill label="Overall" value={selectedCandidate.scores.final_score} />
                  <ScorePill label="Brain" value={selectedCandidate.scores.brainscore} />
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6 pt-6">
              <div className="flex flex-wrap gap-2">
                <StepperTab
                  active={compareView === "summary"}
                  label="Summary"
                  onClick={() => setCompareView("summary")}
                />
                <StepperTab
                  active={compareView === "momentum"}
                  label="Momentum"
                  onClick={() => setCompareView("momentum")}
                />
                <StepperTab
                  active={compareView === "sentences"}
                  label="Sentences"
                  onClick={() => setCompareView("sentences")}
                />
              </div>

              {compareView === "summary" ? (
                <div className="space-y-6">
                  <div className="rounded-[24px] border border-[#e5e5e5] bg-[#fafafa] p-6">
                    <p className="text-[11px] uppercase tracking-[0.24em] text-muted-foreground">
                      Draft text
                    </p>
                    <p className="mt-4 max-w-4xl text-[17px] leading-8 text-[#111111]">
                      {selectedCandidate.id === result.recommended_candidate_id
                        ? result.winner_text
                        : selectedCandidate.text}
                    </p>
                  </div>

                  <div className="grid gap-4 lg:grid-cols-2">
                    <div className="space-y-4">
                      {scoreRows.map((row) => (
                        <ScoreRow
                          key={row.key}
                          label={row.label}
                          helper={row.helper}
                          value={selectedCandidate.scores[row.key]}
                          compareValue={compareCandidate?.scores[row.key] ?? null}
                        />
                      ))}
                    </div>
                    <div className="space-y-4">
                      <CompareInsight
                        title="Why this candidate works"
                        copy={leadSummary(selectedCandidate)}
                      />
                      <CompareInsight
                        title="Weakening factor"
                        copy={weaknessSummary(selectedCandidate)}
                      />
                      <CompareInsight
                        title="Runner-up risk"
                        copy={
                          runnerUp
                            ? `${runnerUp.strategy}: ${weaknessSummary(runnerUp)}`
                            : "No runner-up is available in this run."
                        }
                      />
                    </div>
                  </div>
                </div>
              ) : null}

              {compareView === "momentum" ? (
                <div className="space-y-4">
                      <div className="h-[320px] rounded-[24px] border border-[#e5e5e5] bg-[#fafafa] p-3">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={compareChartData(selectedCandidate, compareCandidate)}>
                            <defs>
                              <linearGradient id="primaryMomentum" x1="0" x2="0" y1="0" y2="1">
                                <stop offset="5%" stopColor="#111111" stopOpacity={0.22} />
                                <stop offset="95%" stopColor="#111111" stopOpacity={0.02} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e2e2" />
                            <XAxis dataKey="step" tickLine={false} axisLine={false} stroke="#666666" />
                            <YAxis tickLine={false} axisLine={false} width={42} stroke="#666666" />
                            <Tooltip
                              contentStyle={{
                                borderRadius: 16,
                                border: "1px solid #e2e2e2",
                                backgroundColor: "rgba(255,255,255,0.98)",
                              }}
                            />
                            <Area
                              type="monotone"
                              dataKey="primary"
                              stroke="#111111"
                              strokeWidth={2.5}
                              fill="url(#primaryMomentum)"
                            />
                            {compareCandidate ? (
                              <Line
                                type="monotone"
                                dataKey="compare"
                                stroke="#7a7a7a"
                                strokeWidth={2}
                                dot={false}
                              />
                        ) : null}
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <MiniMetric
                      label="Peak time"
                      value={`Step ${selectedCandidate.raw_features.peak_time + 1}`}
                    />
                    <MiniMetric
                      label="Sustainability"
                      value={selectedCandidate.raw_features.sustainability.toFixed(3)}
                    />
                  </div>
                </div>
              ) : null}

              {compareView === "sentences" ? (
                <div className="space-y-4">
                  {selectedCandidate.sentence_features.map((sentence) => {
                    const tone = sentenceTone(sentence, selectedCandidate);
                    return (
                      <div
                        key={`${selectedCandidate.id}-${sentence.sentence_index}`}
                        className="rounded-[24px] border border-[#e5e5e5] bg-[#fafafa] p-4"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge className="rounded-full border-foreground/10 bg-stone-100 text-foreground">
                              Sentence {sentence.sentence_index + 1}
                            </Badge>
                            <Badge className={cn("rounded-full border", tone.className)}>
                              {tone.label}
                            </Badge>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Window {sentenceWindowLabel(sentence)}
                          </div>
                        </div>
                        <p className="mt-3 text-sm leading-7 text-[#111111]/84">{sentence.text}</p>
                        <div className="mt-4 space-y-2">
                          <div className="h-2 overflow-hidden rounded-full bg-stone-200">
                            <div
                              className="h-full rounded-full bg-black"
                              style={{
                                width: `${Math.max(8, Math.round(sentence.relative_contribution * 100))}%`,
                              }}
                            />
                          </div>
                          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
                            <span>
                              Contribution {scorePercent(sentence.relative_contribution)}
                            </span>
                            <span>
                              Mean {scorePercent(sentence.mean_energy)} / Peak {scorePercent(sentence.peak_energy)}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : null}
            </CardContent>
          </Card>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <Button
              variant="outline"
              className="rounded-full bg-white/76"
              onClick={() => setScreenStep("results")}
            >
              <ArrowLeft />
              Back to results
            </Button>
            {resultMode === "generate" ? (
              <Button className="rounded-full px-5" onClick={() => setScreenStep("refine")}>
                Refine this winner
                <MoveRight />
              </Button>
            ) : null}
          </div>
        </div>

        <WorkflowInfo currentStep="compare" />
      </div>
    </section>
  );
}
