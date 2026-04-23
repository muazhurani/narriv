"use client";

import { ChevronDown } from "lucide-react";

import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

export function FormLabel({ children }: { children: React.ReactNode }) {
  return (
    <Label className="text-[13px] font-semibold tracking-[-0.01em] text-[#111111]">
      {children}
    </Label>
  );
}

export function FormField({
  label,
  helper,
  input,
}: {
  label: string;
  helper?: string;
  input: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <FormLabel>{label}</FormLabel>
      <div className="relative">
        {input}
        {helper ? (
          <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[12px] text-[#888888]">
            {helper}
          </span>
        ) : null}
      </div>
    </div>
  );
}

export function SelectField({
  id,
  label,
  value,
  helper,
  onChange,
  options,
  labels,
}: {
  id: string;
  label: string;
  value: string;
  helper?: string;
  onChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
  options: string[];
  labels?: Record<string, string>;
}) {
  return (
    <div className="space-y-2">
      <FormLabel>{label}</FormLabel>
      <div className="relative">
        <select
          id={id}
          value={value}
          onChange={onChange}
          className="h-11 w-full appearance-none rounded-[10px] border border-[#d9d9d9] bg-white px-4 pr-10 text-[14px] text-[#222222] outline-none transition focus:border-black"
        >
          {options.map((option) => (
            <option key={option} value={option}>
              {labels?.[option] ?? option}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-4 top-1/2 size-4 -translate-y-1/2 text-[#666666]" />
      </div>
      {helper ? (
        <p className="text-[12px] leading-5 text-[#666666]">{helper}</p>
      ) : null}
    </div>
  );
}

export function ToggleField({
  label,
  helper,
  checked,
  onClick,
  disabled = false,
}: {
  label: string;
  helper: string;
  checked: boolean;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded-[14px] border border-[#e5e5e5] bg-white px-4 py-3">
      <div className="pr-4">
        <p className="text-sm font-medium text-[#111111]">{label}</p>
        <p className="mt-1 text-xs leading-5 text-[#666666]">{helper}</p>
      </div>
      <button
        type="button"
        className={cn(
          "relative inline-flex h-6 w-11 rounded-full transition disabled:cursor-not-allowed disabled:opacity-45",
          checked ? "bg-black" : "bg-stone-300",
        )}
        onClick={onClick}
        aria-pressed={checked}
        disabled={disabled}
      >
        <span
          className={cn(
            "absolute top-0.5 size-5 rounded-full bg-white shadow-sm transition",
            checked ? "left-[22px]" : "left-0.5",
          )}
        />
      </button>
    </div>
  );
}
