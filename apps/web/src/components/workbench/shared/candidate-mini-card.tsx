"use client";

import { Line, LineChart, ResponsiveContainer } from "recharts";

import type { RankedCandidate } from "@/lib/brainopt";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import { chartData, scorePercent } from "../utils";

export function CandidateMiniCard({
  candidate,
  rank,
  isWinner,
  onOpen,
}: {
  candidate: RankedCandidate;
  rank: number;
  isWinner: boolean;
  onOpen: () => void;
}) {
  return (
    <div className="rounded-[24px] border border-border/70 bg-white/76 p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge className="rounded-full border-foreground/10 bg-stone-100 text-foreground">
              #{rank}
            </Badge>
            {isWinner ? (
              <Badge className="rounded-full border-black/15 bg-black text-white">
                Winner
              </Badge>
            ) : null}
          </div>
          <p className="mt-3 text-sm font-medium text-foreground">{candidate.strategy}</p>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">{candidate.reason}</p>
        </div>
        <div className="text-right">
          <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Score</p>
          <p className="mt-1 text-xl font-semibold text-foreground">
            {scorePercent(candidate.scores.final_score)}
          </p>
        </div>
      </div>
      <div className="mt-4 h-12 rounded-2xl border border-border/60 bg-[rgba(248,244,236,0.72)] px-2 py-1.5">
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
      <Button variant="outline" className="mt-4 rounded-full bg-white/76" onClick={onOpen}>
        Open in compare
      </Button>
    </div>
  );
}
