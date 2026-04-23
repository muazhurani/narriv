"use client";

import Image from "next/image";
import {
  FileStack,
  LayoutGrid,
  PlayCircle,
} from "lucide-react";

import { cn } from "@/lib/utils";

import type { UseWorkbenchReturn } from "../use-workbench";

type SidebarItem = {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  active?: boolean;
  disabled?: boolean;
  onClick: () => void;
};

export function WorkbenchSidebar({ state }: { state: UseWorkbenchReturn }) {
  const { screenStep, setScreenStep, result, resultMode, applyTemplate, templateIndex } = state;

  const items: SidebarItem[] = [
    {
      label: "Workbench",
      icon: LayoutGrid,
      active: screenStep === "brief",
      onClick: () => setScreenStep("brief"),
    },
    {
      label: "Runs",
      icon: PlayCircle,
      active: screenStep === "results" || screenStep === "compare" || screenStep === "refine",
      disabled: !result,
      onClick: () => {
        if (result) {
          setScreenStep("results");
        }
      },
    },
    {
      label: "Templates",
      icon: FileStack,
      onClick: () => applyTemplate(templateIndex + 1),
    },
  ];

  return (
    <aside className="hidden min-h-0 border-r border-[#e5e5e5] bg-[#fcfcfc] lg:flex lg:w-[232px] lg:flex-col">
      <div className="px-6 pt-7 pb-8">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center overflow-hidden rounded-xl  bg-white">
            <Image
              src="/Narriv.svg"
              alt="Narriv"
              width={26}
              height={26}
              className="h-6 w-6"
              priority
            />
          </div>
          <div className="leading-tight">
            <p className="text-[16px] font-semibold text-[#111111]">Narriv</p>
            <p className="text-[13px] text-[#666666]">Narrative engine</p>
          </div>
        </div>
      </div>

      <div className="flex-1 px-4">
        <div className="space-y-1">
          {items.map((item) => (
            <SidebarButton key={item.label} {...item} />
          ))}
        </div>
      </div>


      <div className="mx-4 mb-5 rounded-[14px] border border-[#e5e5e5] bg-white px-4 py-4">
        <div className="flex items-center gap-2">
          <span className="size-2.5 rounded-full bg-black" />
          <p className="text-[13px] font-semibold text-[#111111]">Local workspace</p>
        </div>
        <div className="mt-2 flex items-start justify-between gap-2">
          <p className="text-[12px] leading-5 text-[#666666]">
            All models running offline on this device.
          </p>
          <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-[#f1f1f1] text-black">
            <CheckMark />
          </span>
        </div>
      </div>

      {/* Make sidebar hidden route dependent */}
      {resultMode === "generate" ? null : null}
    </aside>
  );
}

function SidebarButton({
  label,
  icon: Icon,
  active = false,
  disabled = false,
  onClick,
}: SidebarItem) {
  return (
    <button
      type="button"
      className={cn(
        "flex w-full items-center gap-3 rounded-[12px] px-3 py-2.5 text-left text-[14px] font-medium transition",
        active
          ? "bg-black text-white"
          : "text-[#444444] hover:bg-[#f3f3f3] hover:text-[#111111]",
        disabled && "cursor-not-allowed opacity-45 hover:bg-transparent hover:text-[#444444]",
      )}
      onClick={onClick}
      disabled={disabled}
    >
      <Icon className="size-4" />
      <span>{label}</span>
    </button>
  );
}

function CheckMark() {
  return (
    <svg viewBox="0 0 24 24" className="size-3" fill="none" stroke="currentColor" strokeWidth="3">
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}
