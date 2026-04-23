"use client";

import { useEffect, useMemo, useState } from "react";

import {
  type CandidateVariant,
  type OptimizeResponse,
  type Platform,
  type RefineRequest,
  optimizePosts,
  refinePost,
  scoreCandidates,
} from "@/lib/brainopt";

import { defaultForm, presets, refineFocusOptions } from "./constants";
import type {
  BriefFormState,
  ComposerMode,
  CompareView,
  CopiedKind,
  ScreenStep,
  WorkflowPhase,
} from "./types";
import { buildPayload } from "./utils";

export type UseWorkbenchReturn = ReturnType<typeof useWorkbench>;

export function useWorkbench() {
  const [form, setForm] = useState<BriefFormState>(defaultForm);
  const [composerMode, setComposerMode] = useState<ComposerMode>("generate");
  const [templateIndex, setTemplateIndex] = useState(0);
  const [resultMode, setResultMode] = useState<ComposerMode>("generate");
  const [testPostText, setTestPostText] = useState("");
  const [comparePostText, setComparePostText] = useState("");
  const [result, setResult] = useState<OptimizeResponse | null>(null);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [compareCandidateId, setCompareCandidateId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, setPending] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [workflowPhase, setWorkflowPhase] = useState<WorkflowPhase>("idle");
  const [screenStep, setScreenStep] = useState<ScreenStep>("brief");
  const [compareView, setCompareView] = useState<CompareView>("summary");
  const [copiedState, setCopiedState] = useState<CopiedKind>(null);
  const [refineFocusId, setRefineFocusId] = useState<string>(refineFocusOptions[0].id);
  const [isRefining, setIsRefining] = useState(false);

  const selectedCandidate =
    result?.candidates.find((candidate) => candidate.id === selectedCandidateId) ??
    result?.candidates[0] ??
    null;

  const winnerCandidate =
    result?.candidates.find(
      (candidate) => candidate.id === result.recommended_candidate_id,
    ) ?? result?.candidates[0] ?? null;

  const compareCandidate =
    result?.candidates.find((candidate) => candidate.id === compareCandidateId) ?? null;

  const runnerUp = useMemo(() => {
    if (!result) {
      return null;
    }

    return (
      result.candidates.find(
        (candidate) => candidate.id !== result.recommended_candidate_id,
      ) ?? null
    );
  }, [result]);

  const activeRefineFocus =
    refineFocusOptions.find((focus) => focus.id === refineFocusId) ??
    refineFocusOptions[0];

  useEffect(() => {
    if (!isPending) {
      return;
    }

    const timers = [
      window.setTimeout(() => setWorkflowPhase("scoring"), 900),
      window.setTimeout(() => setWorkflowPhase("ranking"), 1900),
    ];

    return () => timers.forEach((timer) => window.clearTimeout(timer));
  }, [isPending]);

  async function executeOptimization(refinementPrompt?: string) {
    setPending(true);
    setError(null);
    setWorkflowPhase("generating");

    try {
      const nextResult = await optimizePosts(buildPayload(form, refinementPrompt));
      setResult(nextResult);
      setSelectedCandidateId(nextResult.recommended_candidate_id);
      setCompareCandidateId(
        nextResult.candidates.find(
          (candidate) => candidate.id !== nextResult.recommended_candidate_id,
        )?.id ?? null,
      );
      setResultMode("generate");
      setScreenStep(refinementPrompt ? "refine" : "results");
      setCompareView("summary");
      setWorkflowPhase("ready");
    } catch (submissionError) {
      const message =
        submissionError instanceof Error
          ? submissionError.message
          : "The optimize request failed before results were returned.";
      setError(message);
      setWorkflowPhase(result ? "ready" : "idle");
    } finally {
      setPending(false);
    }
  }

  async function executePostAnalysis() {
    const primaryText = testPostText.trim();
    const secondaryText = comparePostText.trim();

    if (!primaryText) {
      setError("Paste a post to analyze before running direct analysis.");
      return;
    }

    setPending(true);
    setError(null);
    setWorkflowPhase("generating");

    try {
      const scoreResult = await scoreCandidates({
        platform: form.platform,
        tone: form.tone,
        constraints: {
          max_chars: Number(form.maxChars) || undefined,
          include_cta: form.includeCta,
        },
        candidates: [
          {
            id: "submitted-post-a",
            strategy: secondaryText ? "Submitted post A" : "Submitted post",
            tone: form.tone || "original",
            text: primaryText,
          },
          ...(secondaryText
            ? [
                {
                  id: "submitted-post-b",
                  strategy: "Submitted post B",
                  tone: form.tone || "original",
                  text: secondaryText,
                } satisfies CandidateVariant,
              ]
            : []),
        ],
      });

      setResult(scoreResult);
      setSelectedCandidateId(scoreResult.recommended_candidate_id);
      setCompareCandidateId(
        scoreResult.candidates.find(
          (candidate) => candidate.id !== scoreResult.recommended_candidate_id,
        )?.id ?? null,
      );
      setResultMode("test");
      setScreenStep("results");
      setCompareView("summary");
      setWorkflowPhase("ready");
    } catch (submissionError) {
      const message =
        submissionError instanceof Error
          ? submissionError.message
          : "The direct analysis request failed before results were returned.";
      setError(message);
      setWorkflowPhase(result ? "ready" : "idle");
    } finally {
      setPending(false);
    }
  }

  async function executeRefineWinner() {
    if (!result || resultMode !== "generate") {
      return;
    }

    setIsRefining(true);
    setError(null);

    try {
      const payload: RefineRequest = {
        platform: form.platform,
        tone: form.tone,
        constraints: {
          max_chars: Number(form.maxChars) || undefined,
          include_cta: form.includeCta,
        },
        text: result.winner_text,
        refinement_goal: activeRefineFocus.prompt,
      };

      const refined = await refinePost(payload);
      setResult((current) =>
        current
          ? {
              ...current,
              winner_text: refined.final_text,
              explanation: refined.explanation || current.explanation,
              llm_model: refined.llm_model,
              log_file_path: refined.log_file_path ?? current.log_file_path,
            }
          : current,
      );
    } catch (submissionError) {
      const message =
        submissionError instanceof Error
          ? submissionError.message
          : "The refinement request failed before results were returned.";
      setError(message);
    } finally {
      setIsRefining(false);
    }
  }

  function applyTemplate(index: number) {
    const nextTemplate = presets[index % presets.length];
    setTemplateIndex(index % presets.length);
    setComposerMode("generate");
    setScreenStep("brief");
    setForm((current) => ({
      ...current,
      topic: nextTemplate.topic,
      platform: nextTemplate.platform,
      audience: nextTemplate.audience,
      goal: nextTemplate.goal,
      tone: nextTemplate.tone,
    }));
  }

  function copyText(kind: Exclude<CopiedKind, null>, value: string | null) {
    if (!value) {
      return;
    }

    void navigator.clipboard.writeText(value).then(() => {
      setCopiedState(kind);
      window.setTimeout(() => setCopiedState(null), 1500);
    });
  }

  function updatePlatform(platform: Platform) {
    setForm((current) => ({ ...current, platform }));
  }

  const canRun =
    composerMode === "generate"
      ? Boolean(form.topic.trim() || form.sourceMaterial.trim())
      : Boolean(testPostText.trim());
  const comparePostPresent = Boolean(comparePostText.trim());

  return {
    form,
    setForm,
    composerMode,
    setComposerMode,
    templateIndex,
    resultMode,
    testPostText,
    setTestPostText,
    comparePostText,
    setComparePostText,
    result,
    selectedCandidate,
    selectedCandidateId,
    setSelectedCandidateId,
    compareCandidate,
    compareCandidateId,
    setCompareCandidateId,
    runnerUp,
    winnerCandidate,
    error,
    isPending,
    showAdvanced,
    setShowAdvanced,
    workflowPhase,
    screenStep,
    setScreenStep,
    compareView,
    setCompareView,
    copiedState,
    refineFocusId,
    setRefineFocusId,
    activeRefineFocus,
    isRefining,
    canRun,
    comparePostPresent,
    executeOptimization,
    executePostAnalysis,
    executeRefineWinner,
    applyTemplate,
    copyText,
    updatePlatform,
  };
}
