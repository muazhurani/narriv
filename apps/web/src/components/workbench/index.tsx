"use client";

import { WorkbenchSidebar } from "./layout/sidebar";
import { StepProgress } from "./layout/step-progress";
import { BriefStep } from "./steps/brief-step";
import { GenerateStep } from "./steps/generate-step";
import { CompareStep } from "./steps/compare-step";
import { RefineStep } from "./steps/refine-step";
import { useWorkbench } from "./use-workbench";

export function OptimizerWorkbench() {
  const state = useWorkbench();
  const { screenStep } = state;

  return (
    <main className="h-screen overflow-hidden bg-[#ededed] text-[#111111]">
      <div className="flex h-screen bg-[#f7f7f7]">
        <WorkbenchSidebar state={state} />

        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <StepProgress state={state} />

          <div className="flex-1 overflow-y-auto bg-[#f7f7f7] px-6 py-8 sm:px-10">
            {screenStep === "brief" ? <BriefStep state={state} /> : null}
            {screenStep === "results" ? <GenerateStep state={state} /> : null}
            {screenStep === "compare" ? <CompareStep state={state} /> : null}
            {screenStep === "refine" ? <RefineStep state={state} /> : null}
          </div>
        </div>
      </div>
    </main>
  );
}
