import type { Platform } from "@/lib/brainopt";

export type BriefFormState = {
  topic: string;
  sourceMaterial: string;
  platform: Platform;
  audience: string;
  goal: string;
  tone: string;
  maxChars: string;
  candidateCount: string;
  includeCta: boolean;
  refineWinner: boolean;
};

export type WorkflowPhase = "idle" | "generating" | "scoring" | "ranking" | "ready";
export type ScreenStep = "brief" | "results" | "compare" | "refine";
export type CompareView = "summary" | "momentum" | "sentences";
export type ComposerMode = "generate" | "test";

export type RefineFocus = {
  id: string;
  label: string;
  prompt: string;
};

export type CopiedKind = "winner" | "log" | null;
