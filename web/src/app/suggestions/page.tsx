import { readSnapshot } from "@/lib/snapshot";
import type { BuyOption, Suggestion } from "@/lib/types";

function OptionRow({ option, isBest }: { option: BuyOption; isBest: boolean }) {
  const gainColor =
    option.net_projected_gain >= 0
      ? "text-emerald-600 dark:text-emerald-400"
      : "text-red-600 dark:text-red-400";

  return (
    <li
      className={`rounded-md p-2 ${isBest ? "bg-emerald-50 dark:bg-emerald-950/30" : ""}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm">
          <span className="font-medium">{option.player_in.web_name}</span>
          {isBest && (
            <span className="ml-2 rounded bg-emerald-600 px-1.5 py-0.5 text-[10px] font-bold tracking-wide text-white">
              BEST
            </span>
          )}
          <span className="ml-2 text-xs text-zinc-500">quality {option.quality_score.toFixed(0)}</span>
        </div>
        <div className={`text-right text-sm font-semibold tabular-nums ${gainColor}`}>
          {option.net_projected_gain >= 0 ? "+" : ""}
          {option.net_projected_gain.toFixed(1)} pts
        </div>
      </div>
      <dl className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-500">
        <div>
          <dt className="inline">Cost: </dt>
          <dd className="inline tabular-nums">
            {option.cost_delta >= 0 ? "+" : ""}£{option.cost_delta.toFixed(1)}m
          </dd>
        </div>
        <div>
          <dt className="inline">Projected gain: </dt>
          <dd className="inline tabular-nums">+{option.projected_point_gain.toFixed(1)} pts</dd>
        </div>
      </dl>
      <ul className="mt-1.5 space-y-0.5 text-xs text-zinc-600 dark:text-zinc-300">
        {option.rationale.map((line, i) => (
          <li key={i} className="flex gap-1.5">
            <span className="text-zinc-400">&bull;</span>
            <span>{line}</span>
          </li>
        ))}
      </ul>
    </li>
  );
}

function SuggestionCard({ suggestion }: { suggestion: Suggestion }) {
  return (
    <li className="rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm">
          <span className="text-zinc-500">Sell</span>{" "}
          <span className="font-medium">{suggestion.player_out.web_name}</span>
          <span className="ml-2 text-xs text-zinc-500">({suggestion.player_out.position})</span>
        </div>
        {suggestion.hit_cost > 0 && (
          <div className="text-xs font-medium text-orange-600 dark:text-orange-400">
            Hit: -{suggestion.hit_cost} pts
          </div>
        )}
      </div>
      <ul className="mt-3 space-y-1.5">
        {suggestion.options.map((option, i) => (
          <OptionRow key={option.player_in.player_id} option={option} isBest={i === 0} />
        ))}
      </ul>
    </li>
  );
}

export default function SuggestionsPage() {
  const snapshot = readSnapshot();

  return (
    <div>
      <h1 className="mb-1 text-xl font-semibold">Transfer Suggestions</h1>
      <p className="mb-6 text-sm text-zinc-500">
        Advisory only &mdash; review and make transfers yourself in the official FPL app. Ranked over a{" "}
        {snapshot.meta.analysis_horizon_gws}-gameweek look-ahead. Each card is one player worth selling,
        with its best replacement highlighted and runner-up alternatives below.
      </p>
      {snapshot.suggestions.length === 0 ? (
        <p className="text-sm text-zinc-500">No suggestions this week &mdash; your squad looks solid.</p>
      ) : (
        <ul className="space-y-3">
          {snapshot.suggestions.map((s) => (
            <SuggestionCard key={s.id} suggestion={s} />
          ))}
        </ul>
      )}
    </div>
  );
}
