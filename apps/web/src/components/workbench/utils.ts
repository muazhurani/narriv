import type {
  OptimizeRequest,
  OptimizeResponse,
  Platform,
  RankedCandidate,
  SentenceFeature,
} from "@/lib/brainopt";
import type { BriefFormState } from "./types";

export function scorePercent(value: number) {
  return Math.round(value * 100);
}

export function formatPlatform(platform: Platform | string) {
  switch (platform) {
    case "linkedin":
      return "LinkedIn";
    case "twitter":
    case "x":
      return "X";
    case "instagram":
      return "Instagram";
    case "threads":
      return "Threads";
    default:
      return "General";
  }
}

export function platformConsequence(platform: Platform) {
  switch (platform) {
    case "linkedin":
      return {
        headline: "Authority, clearer claims, stronger resolution.",
        detail:
          "LinkedIn runs favor explicit positioning, firmer claims, and a cleaner final landing.",
      };
    case "twitter":
    case "x":
      return {
        headline: "Faster setup, tighter phrasing, sharper contrast.",
        detail: "X runs push harder openings, shorter turns, and more obvious argument contrast.",
      };
    case "threads":
      return {
        headline: "More conversational momentum.",
        detail:
          "Threads runs bias toward looser cadence, warmer transitions, and a more social payoff.",
      };
    default:
      return {
        headline: "Balanced scoring for general publishing.",
        detail:
          "General runs keep the ranking neutral when you do not want a platform-specific bias.",
      };
  }
}

export function chartData(candidate: RankedCandidate) {
  return candidate.temporal_energy.map((value, index) => ({
    step: index + 1,
    energy: Number(value.toFixed(4)),
  }));
}

export function compareChartData(
  primary: RankedCandidate,
  compare?: RankedCandidate | null,
) {
  const maxLength = Math.max(
    primary.temporal_energy.length,
    compare?.temporal_energy.length ?? 0,
  );

  return Array.from({ length: maxLength }, (_, index) => ({
    step: index + 1,
    primary:
      primary.temporal_energy[index] === undefined
        ? null
        : Number(primary.temporal_energy[index].toFixed(4)),
    compare:
      compare?.temporal_energy[index] === undefined || !compare
        ? null
        : Number(compare.temporal_energy[index].toFixed(4)),
  }));
}

export function buildPayload(
  form: BriefFormState,
  refinementPrompt?: string,
): OptimizeRequest {
  const baseTopic = form.topic.trim();
  const topic = refinementPrompt
    ? `${baseTopic || "Derive the strongest post angle from the supplied source material."}\n\nRefinement priority: ${refinementPrompt}`
    : baseTopic;
  const sourceMaterial = form.sourceMaterial.trim();

  return {
    topic,
    source_material: sourceMaterial || undefined,
    platform: form.platform,
    audience: form.audience,
    goal: form.goal,
    tone: form.tone,
    constraints: {
      max_chars: Number(form.maxChars) || undefined,
      include_cta: form.includeCta,
    },
    candidate_count: Number(form.candidateCount) || 4,
    refine_winner: form.refineWinner,
  };
}

export function confidenceLabel(result: OptimizeResponse | null) {
  if (!result || result.candidates.length < 2) {
    return "Single recommendation";
  }

  const [best, second] = [...result.candidates].sort(
    (left, right) => right.scores.final_score - left.scores.final_score,
  );
  const delta = best.scores.final_score - second.scores.final_score;

  if (delta >= 0.12) {
    return "Clear lead";
  }
  if (delta >= 0.06) {
    return "Moderate lead";
  }
  return "Close call";
}

export function leadSummary(candidate: RankedCandidate) {
  const parts: string[] = [];

  if (candidate.scores.hook_score >= 0.8) {
    parts.push("strong opening energy");
  }
  if (candidate.scores.sustained_response_score >= 0.75) {
    parts.push("stable mid-post momentum");
  }
  if (candidate.scores.end_strength_score >= 0.75) {
    parts.push("firm closing strength");
  }
  if (candidate.scores.clarity_stability_score >= 0.75) {
    parts.push("controlled pacing");
  }

  if (parts.length === 0) {
    return "This candidate leads on blended momentum and platform fit.";
  }

  return `This candidate leads on ${parts.slice(0, 3).join(", ")} and platform-fit discipline.`;
}

export function weaknessSummary(candidate: RankedCandidate) {
  if (candidate.diagnostics.dropoff_after_sentence !== null) {
    return `Momentum dips after sentence ${candidate.diagnostics.dropoff_after_sentence + 1}.`;
  }
  if (candidate.diagnostics.weakest_sentence !== null) {
    return `Sentence ${candidate.diagnostics.weakest_sentence + 1} is the softest segment.`;
  }
  if (candidate.scores.end_strength_score < 0.65) {
    return "The ending lands softly relative to the rest of the draft.";
  }
  return "The draft is usable, but it leaves room for a sharper final polish.";
}

export function sentenceTone(sentence: SentenceFeature, candidate: RankedCandidate) {
  if (candidate.diagnostics.strongest_sentence === sentence.sentence_index) {
    return {
      label: "Strongest sentence",
      className: "border-black/15 bg-black/5 text-black",
    };
  }

  if (candidate.diagnostics.weakest_sentence === sentence.sentence_index) {
    return {
      label: "Weak segment",
      className: "border-black/12 bg-black/8 text-black/80",
    };
  }

  return {
    label: "Supporting",
    className: "border-stone-300/70 bg-stone-100 text-stone-700",
  };
}

export function sentenceWindowLabel(sentence: SentenceFeature) {
  return `${sentence.start_t}-${sentence.end_t}`;
}

export function railTone(active: boolean) {
  return active
    ? "border-foreground/15 bg-white shadow-[0_18px_42px_rgba(36,31,22,0.10)]"
    : "border-border/80 bg-[rgba(255,252,248,0.72)] hover:border-foreground/12 hover:bg-white";
}
