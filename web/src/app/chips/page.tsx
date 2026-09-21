import { readSnapshot } from "@/lib/snapshot";
import type { ChipAdvice } from "@/lib/types";

const CHIP_LABEL: Record<ChipAdvice["chip"], string> = {
  wildcard: "Wildcard",
  freehit: "Free Hit",
};

const CHIP_BLURB: Record<ChipAdvice["chip"], string> = {
  wildcard: "Unlimited free transfers this gameweek, and the changes stick.",
  freehit: "Unlimited free transfers for one gameweek only; your squad reverts straight after.",
};

function ChipCard({ advice }: { advice: ChipAdvice }) {
  const badge = !advice.is_available
    ? { text: "Unavailable", style: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300" }
    : advice.recommended
      ? { text: "Recommended", style: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200" }
      : { text: "Available", style: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300" };

  return (
    <li className="rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="font-medium">{CHIP_LABEL[advice.chip]}</h2>
          <p className="text-xs text-zinc-500">{CHIP_BLURB[advice.chip]}</p>
        </div>
        <div className="flex items-center gap-2">
          {advice.target_gameweek !== null && (
            <span className="text-xs text-zinc-500">for GW{advice.target_gameweek}</span>
          )}
          <span className={`rounded px-2 py-0.5 text-xs font-medium ${badge.style}`}>{badge.text}</span>
        </div>
      </div>
      <ul className="mt-3 space-y-1 text-sm text-zinc-600 dark:text-zinc-300">
        {advice.reasoning.map((line, i) => (
          <li key={i} className="flex gap-1.5">
            <span className="text-zinc-400">&bull;</span>
            <span>{line}</span>
          </li>
        ))}
      </ul>
    </li>
  );
}

export default function ChipsPage() {
  const snapshot = readSnapshot();

  return (
    <div>
      <h1 className="mb-1 text-xl font-semibold">Chips</h1>
      <p className="mb-6 text-sm text-zinc-500">
        Advisory only &mdash; decide and play chips yourself in the official FPL app.
      </p>
      <ul className="space-y-3">
        {snapshot.chip_advice.map((advice) => (
          <ChipCard key={advice.chip} advice={advice} />
        ))}
      </ul>
    </div>
  );
}
