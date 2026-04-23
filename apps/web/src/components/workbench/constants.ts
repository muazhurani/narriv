import type { Platform } from "@/lib/brainopt";
import type { BriefFormState, RefineFocus } from "./types";

export const defaultForm: BriefFormState = {
  topic: "Why design systems fail in startups",
  sourceMaterial: "",
  platform: "linkedin",
  audience: "Startup founders and early-stage product teams",
  goal: "thought leadership",
  tone: "Confident and clear",
  maxChars: "600",
  candidateCount: "4",
  includeCta: true,
  refineWinner: true,
};

export const presets: Array<{
  label: string;
  topic: string;
  platform: Platform;
  audience: string;
  goal: string;
  tone: string;
}> = [
  {
    label: "Design Systems",
    topic: "Why design systems fail in startups",
    platform: "linkedin",
    audience: "Startup founders and early-stage product teams",
    goal: "thought leadership",
    tone: "Confident and clear",
  },
  {
    label: "Hiring",
    topic: "Why startups hire senior people too late",
    platform: "linkedin",
    audience: "Early-stage founders",
    goal: "Spark discussion",
    tone: "Direct and credible",
  },
  {
    label: "AI Products",
    topic: "The hidden cost of adding AI features before product fit",
    platform: "linkedin",
    audience: "Product leaders",
    goal: "Educate audience",
    tone: "Sharp and analytical",
  },
];

export const toneOptions = [
  "Confident and clear",
  "Direct and credible",
  "Sharp and analytical",
  "Conversational and warm",
];

export const goalOptions = [
  "Thought leadership",
  "Spark discussion",
  "Educate audience",
  "Drive replies",
];

export const lengthOptions = [
  { value: "280", label: "280 characters" },
  { value: "600", label: "600 characters" },
  { value: "900", label: "900 characters" },
];

export const scoreRows = [
  {
    key: "hook_score",
    label: "Opening pull",
    helper: "How quickly the post earns attention in the first moments.",
  },
  {
    key: "sustained_response_score",
    label: "Sustained momentum",
    helper: "How well the post keeps strength through the middle.",
  },
  {
    key: "clarity_stability_score",
    label: "Clarity and control",
    helper: "How stable and readable the response pattern remains.",
  },
  {
    key: "end_strength_score",
    label: "Closing strength",
    helper: "How firmly the ending lands.",
  },
  {
    key: "platform_fit_score",
    label: "Platform fit",
    helper: "How well the draft matches the chosen publishing context.",
  },
] as const;

export const refineFocusOptions: RefineFocus[] = [
  {
    id: "opening",
    label: "Sharpen opening",
    prompt: "Sharpen the opening and make the first sentence harder to ignore.",
  },
  {
    id: "clarity",
    label: "Increase clarity",
    prompt: "Tighten the structure and make the argument easier to scan quickly.",
  },
  {
    id: "ending",
    label: "Strengthen close",
    prompt: "Make the ending land harder and improve the call to respond.",
  },
  {
    id: "executive",
    label: "More executive",
    prompt: "Keep the idea strong but make the tone more senior and controlled.",
  },
  {
    id: "shorten",
    label: "Reduce length",
    prompt: "Reduce the length without losing the main argument or force.",
  },
];

export const screenStepCopy: Array<{
  id: "brief" | "results" | "compare" | "refine";
  label: string;
  copy: string;
  longCopy: string;
}> = [
  {
    id: "brief",
    label: "Brief",
    copy: "Define intent & constraints",
    longCopy:
      "Define the topic, audience, platform, tone, and goal. Set constraints and preferences.",
  },
  {
    id: "results",
    label: "Generate",
    copy: "Create multiple directions",
    longCopy: "The AI creates multiple high-quality directions based on your brief.",
  },
  {
    id: "compare",
    label: "Compare",
    copy: "Compare & pick winner",
    longCopy:
      "Review all directions side-by-side and choose the strongest narrative.",
  },
  {
    id: "refine",
    label: "Refine",
    copy: "Polish & finalize post",
    longCopy: "Polish the winning direction into a final, publish-ready post.",
  },
];
