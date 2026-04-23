"use client";

import { startTransition } from "react";
import {
  ArrowLeft,
  Check,
  Copy,
  FileText,
  LoaderCircle,
  MoveRight,
  RefreshCcw,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

import { refineFocusOptions } from "../constants";
import type { UseWorkbenchReturn } from "../use-workbench";
import { DraftPanel } from "../shared/score-components";
import { WorkflowInfo } from "../layout/workflow-info";

export function RefineStep({ state }: { state: UseWorkbenchReturn }) {
  const {
    result,
    winnerCandidate,
    resultMode,
    refineFocusId,
    setRefineFocusId,
    activeRefineFocus,
    isRefining,
    executeRefineWinner,
    copyText,
    copiedState,
    setScreenStep,
    executeOptimization,
  } = state;

  if (!result || !winnerCandidate || resultMode !== "generate") {
    return null;
  }

  return (
    <section className="mx-auto w-full max-w-[1240px]">
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-6">
          <Card className="border-[#e5e5e5] bg-white shadow-[0_8px_24px_rgba(0,0,0,0.05)]">
            <CardHeader className="gap-3">
              <CardTitle className="text-2xl text-foreground">Refine the winner</CardTitle>
              <CardDescription className="leading-6">
                Once you are here, the job is no longer ranking. It is improving the chosen draft.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="flex flex-wrap gap-2">
                {refineFocusOptions.map((focus) => (
                  <button
                    key={focus.id}
                    type="button"
                    className={cn(
                      "rounded-full border px-4 py-2 text-sm transition",
                      focus.id === refineFocusId
                        ? "border-foreground/15 bg-foreground text-background"
                        : "border-border bg-white/76 text-foreground hover:bg-white",
                    )}
                    onClick={() => setRefineFocusId(focus.id)}
                  >
                    {focus.label}
                  </button>
                ))}
              </div>

              <div className="grid gap-4 xl:grid-cols-2">
                <DraftPanel
                  title="Current recommendation"
                  copy={result.winner_text}
                  footer="This is the strongest current draft."
                />
                <DraftPanel
                  title="Next-pass instruction"
                  copy={activeRefineFocus.prompt}
                  footer="Use a directed refinement instead of rerunning without a clear target."
                />
              </div>

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm leading-6 text-muted-foreground">
                  Use another pass when the winner is directionally right but still has one clear weakness.
                </p>
                <Button
                  className="rounded-full px-5"
                  disabled={isRefining}
                  onClick={() =>
                    startTransition(() => {
                      void executeRefineWinner();
                    })
                  }
                >
                  {isRefining ? (
                    <>
                      <LoaderCircle className="animate-spin" />
                      Refining winner
                    </>
                  ) : (
                    <>
                      Apply refinement
                      <MoveRight />
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="border-[#e5e5e5] bg-white shadow-[0_8px_24px_rgba(0,0,0,0.05)]">
            <CardHeader className="gap-3">
              <CardTitle className="text-2xl text-foreground">Export and trust</CardTitle>
              <CardDescription className="leading-6">
                Final actions live here, not scattered across the whole app.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <Button className="rounded-full" onClick={() => copyText("winner", result.winner_text)}>
                  {copiedState === "winner" ? (
                    <>
                      <Check />
                      Copied final post
                    </>
                  ) : (
                    <>
                      <Copy />
                      Copy final post
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
              </div>

              <div className="rounded-[22px] border border-[#e5e5e5] bg-[#fafafa] p-4">
                <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">Log file</p>
                <p className="mt-2 break-all font-mono text-xs leading-6 text-[#111111]/82">
                  {result.log_file_path ?? "No log file was returned for this run."}
                </p>
              </div>

              <Separator />

              <div className="space-y-2 text-sm leading-7 text-[#111111]/82">
                <p>
                  This is a brain-inspired ranking signal. It is useful for comparing narrative shape and pacing, not for promising reach or conversions.
                </p>
                <p>
                  The winner should be treated as the strongest current option, not as an unquestionable output.
                </p>
              </div>

              <div className="flex flex-wrap gap-3">
                <Button
                  variant="outline"
                  className="rounded-full bg-white/76"
                  onClick={() => setScreenStep("compare")}
                >
                  <ArrowLeft />
                  Back to compare
                </Button>
                <Button
                  variant="outline"
                  className="rounded-full bg-white/76"
                  onClick={() =>
                    startTransition(() => {
                      void executeOptimization();
                    })
                  }
                >
                  <RefreshCcw />
                  Run again from this brief
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <WorkflowInfo currentStep="refine" />
      </div>
    </section>
  );
}
