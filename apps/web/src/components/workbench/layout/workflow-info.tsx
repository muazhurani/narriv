"use client";

import { Lightbulb, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

import { screenStepCopy } from "../constants";
import type { ScreenStep } from "../types";

export function WorkflowInfo({ currentStep }: { currentStep: ScreenStep }) {
  const activeIndex = screenStepCopy.findIndex((step) => step.id === currentStep);

  return (
    <aside className="space-y-5 rounded-[20px] border border-[#e5e5e5] bg-white p-6 shadow-[0_8px_24px_rgba(0,0,0,0.04)]">
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-[#111111]">
          <Sparkles className="size-4 text-black" />
          <p className="text-[15px] font-semibold">How the workflow works</p>
        </div>
        <p className="text-[13px] text-[#666666]">
          You&apos;re on <Badge className="rounded-full border-[#dddddd] bg-[#f3f3f3] text-black">
            Step {activeIndex + 1}
          </Badge>{" "}
          of {screenStepCopy.length}
        </p>
      </div>

      <div className="space-y-3">
        {screenStepCopy.map((step, index) => {
          const isActive = step.id === currentStep;
          const isCompleted = index < activeIndex;
          const isUpcoming = index > activeIndex;

          return (
            <div
              key={step.id}
              className={cn(
                "rounded-[16px] border p-4 transition",
                isActive
                  ? "border-black bg-[#f6f6f6]"
                  : "border-[#ebebeb] bg-[#fafafa]",
              )}
            >
              <div className="flex items-start gap-3">
                <div
                  className={cn(
                    "flex size-7 shrink-0 items-center justify-center rounded-full text-[12px] font-semibold",
                    isActive
                      ? "bg-black text-white"
                      : isCompleted
                        ? "bg-[#222222] text-white"
                        : "bg-[#e2e2e2] text-[#444444]",
                  )}
                >
                  {index + 1}
                </div>
                <div className="space-y-2">
                  <p
                    className={cn(
                      "text-[14px] font-semibold",
                      isActive ? "text-black" : "text-[#111111]",
                    )}
                  >
                    {step.label}
                  </p>
                  <p className="text-[12px] leading-5 text-[#666666]">{step.longCopy}</p>
                  <span
                    className={cn(
                      "inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium",
                      isActive
                        ? "bg-black text-white"
                        : isCompleted
                          ? "bg-[#ececec] text-[#111111]"
                          : "bg-[#f1f1f1] text-[#666666]",
                    )}
                  >
                    {isActive ? "You are here" : isUpcoming ? "Upcoming" : "Completed"}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex items-start gap-3 rounded-[14px] border border-[#e5e5e5] bg-[#f7f7f7] p-4">
        <div className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full bg-[#111111] text-white">
          <Lightbulb className="size-3.5" />
        </div>
        <div>
          <p className="text-[13px] font-semibold text-[#111111]">Tip</p>
          <p className="mt-1 text-[12px] leading-5 text-[#666666]">
            Great briefs lead to great posts. Be specific about your audience and desired outcome.
          </p>
        </div>
      </div>
    </aside>
  );
}
