import { readSnapshot } from "@/lib/snapshot";
import type { ChipAdvice, ChipPlan, PlannedTransfer } from "@/lib/types";

const CHIP_LABEL: Record<ChipAdvice["chip"], string> = {
  wildcard: "Wildcard",
  freehit: "Free Hit",
};

const CHIP_BLURB: Record<ChipAdvice["chip"], string> = {
  wildcard: "Unlimited free transfers this gameweek, and the changes stick.",
  freehit: "Unlimited free transfers for one gameweek only; your squad reverts straight after.",
};

function PlannedTransferRow({ transfer }: { transfer: PlannedTransfer }) {
  return (
    <li className="rounded-md border border-zinc-200 p-2 dark:border-zinc-800">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm">
          <span className="text-red-600 dark:text-red-400">{transfer.player_out.web_name}</span>
          <span className="mx-1.5 text-zinc-400">&rarr;</span>
          <span className="font-medium text-emerald-700 dark:text-emerald-400">
            {transfer.player_in.web_name}
          </span>
          <span className="ml-2 text-xs text-zinc-500">({transfer.player_in.position})</span>
        </div>
        <div className="text-right text-sm font-semibold tabular-nums text-emerald-600 dark:text-emerald-400">
          +{transfer.projected_point_gain.toFixed(1)} pts
        </div>
      </div>
      <dl className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-500">
        <div>
          <dt className="inline">Sell for: </dt>
          <dd className="inline tabular-nums">£{transfer.sell_price.toFixed(1)}m</dd>
        </div>
        <div>
          <dt className="inline">Buy at: </dt>
          <dd className="inline tabular-nums">£{transfer.buy_price.toFixed(1)}m</dd>
        </div>
      </dl>
      <ul className="mt-1.5 space-y-0.5 text-xs text-zinc-600 dark:text-zinc-300">
        {transfer.rationale.map((line, i) => (
          <li key={i} className="flex gap-1.5">
            <span className="text-zinc-400">&bull;</span>
            <span>{line}</span>
          </li>
        ))}
      </ul>
    </li>
  );
}

function PlanSection({ plan }: { plan: ChipPlan }) {
  const window =
    plan.horizon_gws === 1
      ? `GW${plan.target_gameweek} only`
      : `the next ${plan.horizon_gws} gameweeks`;

  if (plan.transfer_count === 0) {
    return (
      <p className="mt-3 border-t border-zinc-200 pt-3 text-sm text-zinc-500 dark:border-zinc-800">
        No transfers worth making over {window} came out of the plan &mdash; the chip is worth playing
        on the reasoning above, but your budget and the available replacements don&rsquo;t currently
        support a rebuild.
      </p>
    );
  }

  return (
    <div className="mt-3 border-t border-zinc-200 pt-3 dark:border-zinc-800">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-sm font-medium">
          If you play it: {plan.transfer_count} transfer{plan.transfer_count === 1 ? "" : "s"} before
          the GW{plan.target_gameweek} deadline
        </h3>
        <p className="text-xs text-zinc-500">
          <span className="font-semibold text-emerald-600 dark:text-emerald-400">
            +{plan.projected_point_gain.toFixed(1)} pts
          </span>{" "}
          projected over {window} &middot; bank £{plan.bank_before.toFixed(1)}m &rarr; £
          {plan.bank_after.toFixed(1)}m
        </p>
      </div>
      <ul className="mt-2 space-y-1.5">
        {plan.transfers.map((transfer) => (
          <PlannedTransferRow key={transfer.player_out.player_id} transfer={transfer} />
        ))}
      </ul>
    </div>
  );
}

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
      {advice.plan && <PlanSection plan={advice.plan} />}
    </li>
  );
}

export default function ChipsPage() {
  const snapshot = readSnapshot();

  return (
    <div>
      <h1 className="mb-1 text-xl font-semibold">Chips</h1>
      <p className="mb-6 text-sm text-zinc-500">
        Advisory only &mdash; decide and play chips yourself in the official FPL app. A recommended chip
        also comes with the transfers to make with it: apply them as one package, since the plan&rsquo;s
        budget assumes every earlier sale in the list has gone through.
      </p>
      <ul className="space-y-3">
        {snapshot.chip_advice.map((advice) => (
          <ChipCard key={advice.chip} advice={advice} />
        ))}
      </ul>
    </div>
  );
}
