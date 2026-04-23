"use client";

import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

import { screenStepCopy } from "../constants";
import type { UseWorkbenchReturn } from "../use-workbench";

export function StepProgress({ state }: { state: UseWorkbenchReturn }) {
  const { screenStep, setScreenStep, result, resultMode } = state;

  const steps = screenStepCopy.map((step) => ({
    ...step,
    enabled:
      step.id === "brief"
        ? true
        : step.id === "refine"
          ? Boolean(result) && resultMode === "generate"
          : Boolean(result),
  }));

  const activeStepIndex = steps.findIndex((step) => step.id === screenStep);

  return (
    <section className="border-b border-[#e5e5e5] bg-[#fcfcfc] px-8 py-5">
      <div className="flex items-center gap-6 overflow-x-auto">
        {steps.map((step, index) => {
          const isActive = screenStep === step.id;
          const isCompleted = index < activeStepIndex && step.enabled;

          return (
            <div key={step.id} className="flex min-w-[220px] flex-1 items-center gap-4">
              <button
                type="button"
                disabled={!step.enabled}
                onClick={() => step.enabled && setScreenStep(step.id)}
                className="group flex w-full min-w-0 items-center gap-3 text-left disabled:cursor-not-allowed disabled:opacity-45"
              >
                <div
                  className={cn(
                    "flex size-8 shrink-0 items-center justify-center rounded-full border text-[13px] font-semibold transition",
                    isActive
                      ? "border-black bg-black text-white"
                      : isCompleted
                        ? "border-[#222222] bg-[#f1f1f1] text-black"
                        : "border-[#dcdcdc] bg-white text-[#444444]",
                  )}
                >
                  {isCompleted ? <Check className="size-4" /> : index + 1}
                </div>
                <div className="min-w-0">
                  <p
                    className={cn(
                      "truncate text-[14px] font-semibold",
                      isActive ? "text-black" : "text-[#111111]",
                    )}
                  >
                    {step.label}
                  </p>
                  <p className="truncate text-[12px] text-[#666666]">{step.copy}</p>
                </div>
              </button>
              {index < steps.length - 1 ? (
                <div
                  className={cn(
                    "hidden h-px flex-1 md:block",
                    index < activeStepIndex ? "bg-[#222222]" : "bg-[#e5e5e5]",
                  )}
                />
              ) : null}
            </div>
          );
        })}
      </div>
    </section>
  );
}
