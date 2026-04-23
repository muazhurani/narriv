"use client";

import { startTransition } from "react";
import {
  ArrowRight,
  Check,
  ChevronDown,
  ChevronUp,
  FileText,
  LoaderCircle,
  Plus,
} from "lucide-react";
import type { IconType } from "react-icons";
import { FaLinkedinIn, FaXTwitter, FaThreads } from "react-icons/fa6";

import type { Platform } from "@/lib/brainopt";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

import {
  goalOptions,
  lengthOptions,
  toneOptions,
} from "../constants";
import type { UseWorkbenchReturn } from "../use-workbench";
import { formatPlatform, platformConsequence } from "../utils";
import {
  FormField,
  FormLabel,
  SelectField,
  ToggleField,
} from "../shared/form-fields";
import { WorkflowInfo } from "../layout/workflow-info";

const platformOptions: Array<{
  id: Platform;
  label: string;
  icon: IconType;
  iconClassName: string;
}> = [
  {
    id: "linkedin",
    label: "LinkedIn",
    icon: FaLinkedinIn,
    iconClassName: "text-[#111111]",
  },
  {
    id: "twitter",
    label: "X (Twitter)",
    icon: FaXTwitter,
    iconClassName: "text-[#111111]",
  },
  {
    id: "threads",
    label: "Threads",
    icon: FaThreads,
    iconClassName: "text-[#111111]",
  },
];

export function BriefStep({ state }: { state: UseWorkbenchReturn }) {
  const {
    form,
    setForm,
    composerMode,
    setComposerMode,
    testPostText,
    setTestPostText,
    comparePostText,
    setComparePostText,
    showAdvanced,
    setShowAdvanced,
    executeOptimization,
    executePostAnalysis,
    isPending,
    workflowPhase,
    error,
    canRun,
    comparePostPresent,
    applyTemplate,
    templateIndex,
    updatePlatform,
  } = state;

  const activePlatformConsequence = platformConsequence(form.platform);
  const topicLength = form.topic.length;
  const sourceMaterialLength = form.sourceMaterial.length;

  return (
    <section className="mx-auto grid w-full max-w-[1240px] gap-8 lg:grid-cols-[minmax(0,1fr)_340px]">
      <div className="space-y-6">
        <header className="space-y-4">
          <h1 className="max-w-[620px] text-[44px] leading-[1.04] tracking-[-0.035em] text-[#111111] sm:text-[52px]">
            Find the post with the strongest <span className="relative">narrative pull</span>
          </h1>
          <p className="max-w-[560px] text-[15px] leading-7 text-[#666666]">
            Define your brief, generate multiple directions, compare them, and refine the
            strongest version.
          </p>
        </header>

        <div className="rounded-[20px] border border-[#e5e5e5] bg-white p-6 shadow-[0_8px_24px_rgba(0,0,0,0.04)]">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-5">
            <div className="flex items-center gap-3">
              <div className="flex size-8 items-center justify-center rounded-lg border border-[#e0e0e0] text-[#444444]">
                <FileText className="size-4" />
              </div>
              <h2 className="text-[18px] font-semibold tracking-[-0.01em] text-[#111111]">
                Define your brief
              </h2>
            </div>
            <div className="flex items-center gap-3">
              <div className="inline-flex rounded-full border border-[#e3e3e3] bg-[#f5f5f5] p-1">
                <ModeToggle
                  label="Create"
                  active={composerMode === "generate"}
                  onClick={() => setComposerMode("generate")}
                />
                <ModeToggle
                  label="Analyze"
                  active={composerMode === "test"}
                  onClick={() => setComposerMode("test")}
                />
              </div>
              <span className="hidden items-center gap-1.5 text-[12px] text-[#666666] sm:inline-flex">
                Saved just now
                <Check className="size-3.5 text-[#111111]" />
              </span>
            </div>
          </div>

          {composerMode === "generate" ? (
            <div className="space-y-5">
              <FormField
                label="Angle or topic"
                helper={`${topicLength} / 140`}
                input={
                  <Input
                    id="topic"
                    value={form.topic}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, topic: event.target.value }))
                    }
                    maxLength={140}
                    className="h-11 rounded-[10px] border-[#e0e0e0] bg-white pr-20 text-[14px]"
                    placeholder="What is the post about, or what angle should it take?"
                  />
                }
              />

              <div className="space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <FormLabel>Source material</FormLabel>
                  <span className="text-[12px] text-[#888888]">{sourceMaterialLength} chars</span>
                </div>
                <Textarea
                  id="source-material"
                  value={form.sourceMaterial}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      sourceMaterial: event.target.value,
                    }))
                  }
                  className="min-h-44 rounded-[12px] border-[#e0e0e0] bg-white text-[14px] leading-7"
                  placeholder="Optional: paste a news article, transcript, product notes, customer feedback, or research. The system will extract the strongest posting angle from this material."
                />
                <p className="text-[12px] leading-5 text-[#666666]">
                  Use this when the input is larger than a simple topic. The generator will treat pasted material as source context, not as copy to repost verbatim.
                </p>
              </div>

              <FormField
                label="Audience"
                helper={`${form.audience.length} / 80`}
                input={
                  <Input
                    id="audience"
                    value={form.audience}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, audience: event.target.value }))
                    }
                    maxLength={80}
                    className="h-11 rounded-[10px] border-[#e0e0e0] bg-white pr-20 text-[14px]"
                  />
                }
              />

              <PlatformSelector
                value={form.platform}
                onChange={updatePlatform}
                onAdd={() => applyTemplate(templateIndex + 1)}
              />

              <SelectField
                id="tone"
                label="Tone"
                value={form.tone}
                helper="Direct, insightful, and actionable."
                onChange={(event) =>
                  setForm((current) => ({ ...current, tone: event.target.value }))
                }
                options={toneOptions}
              />

              <SelectField
                id="goal"
                label="Goal"
                value={form.goal}
                helper="Build authority and spark conversations."
                onChange={(event) =>
                  setForm((current) => ({ ...current, goal: event.target.value }))
                }
                options={goalOptions}
              />

              <div className="grid gap-4 sm:grid-cols-2">
                <SelectField
                  id="candidate-count"
                  label="Candidate count"
                  value={form.candidateCount}
                  helper="3-6 recommended"
                  onChange={(event) =>
                    setForm((current) => ({ ...current, candidateCount: event.target.value }))
                  }
                  options={["3", "4", "5", "6"]}
                />
                <SelectField
                  id="max-chars"
                  label="Max length"
                  value={form.maxChars}
                  helper={`Optimal for ${formatPlatform(form.platform)}`}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, maxChars: event.target.value }))
                  }
                  options={lengthOptions.map((item) => item.value)}
                  labels={Object.fromEntries(
                    lengthOptions.map((item) => [item.value, item.label]),
                  )}
                />
              </div>

              <div className="rounded-[14px] border border-[#e5e5e5] bg-[#fafafa]">
                <button
                  type="button"
                  className="flex w-full items-center justify-between px-4 py-3 text-left"
                  onClick={() => setShowAdvanced((current) => !current)}
                >
                  <div>
                    <p className="text-[13px] font-semibold text-[#111111]">Advanced controls</p>
                    <p className="mt-0.5 text-[12px] text-[#666666]">
                      Keep optional guidance out of the way until needed.
                    </p>
                  </div>
                  {showAdvanced ? (
                    <ChevronUp className="size-4 text-[#666666]" />
                  ) : (
                    <ChevronDown className="size-4 text-[#666666]" />
                  )}
                </button>
                {showAdvanced ? (
                  <div className="space-y-3 border-t border-[#e5e5e5] p-4">
                    <ToggleField
                      label="Include CTA"
                      helper="Ask the system to land with a clear next step."
                      checked={form.includeCta}
                      onClick={() =>
                        setForm((current) => ({
                          ...current,
                          includeCta: !current.includeCta,
                        }))
                      }
                    />
                    <ToggleField
                      label="Prepare refine flow"
                      helper="Keep the winner ready for the refine step after ranking."
                      checked={form.refineWinner}
                      onClick={() =>
                        setForm((current) => ({
                          ...current,
                          refineWinner: !current.refineWinner,
                        }))
                      }
                    />
                  </div>
                ) : null}
              </div>
            </div>
          ) : (
            <div className="space-y-5">
              <div className="space-y-2">
                <FormLabel>Draft</FormLabel>
                <Textarea
                  id="test-post"
                  value={testPostText}
                  onChange={(event) => setTestPostText(event.target.value)}
                  className="min-h-36 rounded-[12px] border-[#e0e0e0] bg-white text-[14px] leading-7"
                  placeholder="Paste the post you want to analyze."
                />
              </div>
              <div className="space-y-2">
                <FormLabel>Second draft</FormLabel>
                <Textarea
                  id="compare-post"
                  value={comparePostText}
                  onChange={(event) => setComparePostText(event.target.value)}
                  className="min-h-28 rounded-[12px] border-[#e0e0e0] bg-white text-[14px] leading-7"
                  placeholder="Optional: paste another version to compare."
                />
              </div>
              <PlatformSelector
                value={form.platform}
                onChange={updatePlatform}
                onAdd={() => applyTemplate(templateIndex + 1)}
                helper={activePlatformConsequence.headline}
              />
            </div>
          )}

          <div className="mt-6 flex flex-col gap-3 border-t border-[#ececec] pt-5 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-[12px] text-[#666666]">
              {composerMode === "generate"
                ? "AI will create multiple directions from your brief and any source material you provide."
                : "Scoring shows where momentum rises or weakens."}
            </p>
            <Button
              className="h-11 rounded-[10px] bg-black px-6 text-[14px] font-semibold text-white shadow-none hover:bg-black/85"
              disabled={isPending || !canRun}
              onClick={() =>
                startTransition(() => {
                  void (composerMode === "generate"
                    ? executeOptimization()
                    : executePostAnalysis());
                })
              }
            >
              {isPending ? (
                <>
                  <LoaderCircle className="size-4 animate-spin" />
                  {workflowPhase === "generating"
                    ? "Generating"
                    : workflowPhase === "scoring"
                      ? "Scoring"
                      : "Ranking"}
                </>
              ) : (
                <>
                  Continue to {composerMode === "generate" ? "Generate" : "Analyze"}
                  <ArrowRight className="size-4" />
                </>
              )}
            </Button>
          </div>

          {error ? (
            <div className="mt-4 rounded-[12px] border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-800">
              {error}
            </div>
          ) : null}
        </div>

        {comparePostPresent ? (
          <div className="text-[12px] text-[#666666]">
            <Badge className="mr-2 rounded-full border-[#dddddd] bg-[#f2f2f2] text-[#111111]">
              Compare ready
            </Badge>
            Second draft detected and will be scored alongside the primary post.
          </div>
        ) : null}
      </div>

      <WorkflowInfo currentStep="brief" />
    </section>
  );
}

function ModeToggle({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={cn(
        "rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] transition",
        active ? "bg-black text-white" : "text-[#666666] hover:text-[#111111]",
      )}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

function PlatformSelector({
  value,
  onChange,
  onAdd,
  helper,
}: {
  value: Platform;
  onChange: (platform: Platform) => void;
  onAdd?: () => void;
  helper?: string;
}) {
  return (
    <div className="space-y-2">
      <FormLabel>Platform</FormLabel>
      <div className="flex flex-wrap gap-2">
        {platformOptions.map((platform) => {
          const isSelected = value === platform.id;
          const Icon = platform.icon;
          return (
            <button
              key={platform.id}
              type="button"
              onClick={() => onChange(platform.id)}
              className={cn(
                "flex items-center gap-2 rounded-[10px] border px-3 py-2 text-[13px] font-medium transition",
                isSelected
                  ? "border-black bg-black text-white"
                  : "border-[#e0e0e0] bg-white text-[#222222] hover:bg-[#f5f5f5]",
              )}
            >
              <Icon
                className={cn(
                  "size-4",
                  platform.iconClassName,
                  isSelected ? "text-white" : ""
                )}
              />
              {platform.label}
            </button>
      
          );
        })}
        {onAdd ? (
          <button
            type="button"
            onClick={onAdd}
            className="flex items-center gap-2 rounded-[10px] border border-dashed border-[#d5d5d5] bg-white px-3 py-2 text-[13px] text-[#666666] hover:bg-[#f5f5f5]"
          >
            <Plus className="size-3.5" />
            Add
          </button>
        ) : null}
      </div>
      {helper ? <p className="text-[12px] leading-5 text-[#666666]">{helper}</p> : null}
    </div>
  );
}
