"use client";

import { cn } from "@/lib/utils";

import { scorePercent } from "../utils";

export function ScorePill({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-full border border-border/70 bg-white/76 px-3 py-2 text-center">
      <p className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-semibold text-foreground">{scorePercent(value)}</p>
    </div>
  );
}

export function OverviewMetric({
  label,
  value,
  copy,
}: {
  label: string;
  value: string;
  copy: string;
}) {
  return (
    <div className="rounded-[22px] border border-border/70 bg-white/76 p-4">
      <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">{label}</p>
      <p className="mt-3 text-2xl font-semibold text-foreground">{value}</p>
      <p className="mt-2 text-xs leading-5 text-muted-foreground">{copy}</p>
    </div>
  );
}

export function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[20px] border border-border/70 bg-white/76 p-4">
      <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">{label}</p>
      <p className="mt-2 text-sm leading-6 text-foreground/84">{value}</p>
    </div>
  );
}

export function CompareInsight({ title, copy }: { title: string; copy: string }) {
  return (
    <div className="rounded-[22px] border border-border/70 bg-white/76 p-4">
      <p className="text-sm font-medium text-foreground">{title}</p>
      <p className="mt-2 text-sm leading-7 text-muted-foreground">{copy}</p>
    </div>
  );
}

export function StepperTab({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={cn(
        "rounded-full border px-4 py-2 text-sm transition",
        active
          ? "border-black bg-black text-white"
          : "border-border bg-white/76 text-foreground hover:bg-white",
      )}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

export function ScoreRow({
  label,
  helper,
  value,
  compareValue,
}: {
  label: string;
  helper: string;
  value: number;
  compareValue: number | null;
}) {
  const delta = compareValue === null ? null : scorePercent(value) - scorePercent(compareValue);

  return (
    <div className="rounded-[22px] border border-border/70 bg-white/76 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-foreground">{label}</p>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">{helper}</p>
        </div>
        <div className="text-right">
          <p className="text-lg font-semibold text-foreground">{scorePercent(value)}</p>
          {delta !== null ? (
            <p className={cn("text-xs", delta >= 0 ? "text-black" : "text-black/70")}>
              {delta >= 0 ? "+" : ""}
              {delta} vs compare
            </p>
          ) : null}
        </div>
      </div>
      <div className="mt-4 space-y-2">
        <div className="h-2 overflow-hidden rounded-full bg-stone-200">
          <div
            className="h-full rounded-full bg-black"
            style={{ width: `${scorePercent(value)}%` }}
          />
        </div>
        {compareValue !== null ? (
          <div className="h-1 overflow-hidden rounded-full bg-stone-200/80">
            <div
              className="h-full rounded-full bg-stone-500/70"
              style={{ width: `${scorePercent(compareValue)}%` }}
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function DraftPanel({
  title,
  copy,
  footer,
}: {
  title: string;
  copy: string;
  footer: string;
}) {
  return (
    <div className="rounded-[24px] border border-border/70 bg-white/76 p-5">
      <p className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">{title}</p>
      <p className="mt-3 text-sm leading-7 text-foreground/84">{copy}</p>
      <p className="mt-4 text-xs leading-6 text-muted-foreground">{footer}</p>
    </div>
  );
}
