import { readSnapshot } from "@/lib/snapshot";
import type { Suggestion } from "@/lib/types";

function SuggestionCard({ suggestion }: { suggestion: Suggestion }) {
  const gainColor =
    suggestion.net_projected_gain >= 0
      ? "text-emerald-600 dark:text-emerald-400"
      : "text-red-600 dark:text-red-400";

  return (
    <li className="rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm">
          <span className="font-medium">{suggestion.player_out.web_name}</span>
          <span className="mx-2 text-zinc-400">&rarr;</span>
          <span className="font-medium">{suggestion.player_in.web_name}</span>
          <span className="ml-2 text-xs text-zinc-500">({suggestion.player_out.position})</span>
        </div>
        <div className={`text-right text-sm font-semibold tabular-nums ${gainColor}`}>
          {suggestion.net_projected_gain >= 0 ? "+" : ""}
          {suggestion.net_projected_gain.toFixed(1)} pts
        </div>
      </div>
      <dl className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-500">
        <div>
          <dt className="inline">Cost: </dt>
          <dd className="inline tabular-nums">
            {suggestion.cost_delta >= 0 ? "+" : ""}£{suggestion.cost_delta.toFixed(1)}m
          </dd>
        </div>
        <div>
          <dt className="inline">Projected gain: </dt>
          <dd className="inline tabular-nums">+{suggestion.projected_point_gain.toFixed(1)} pts</dd>
        </div>
        {suggestion.hit_cost > 0 && (
          <div className="text-orange-600 dark:text-orange-400">
            <dt className="inline">Hit: </dt>
            <dd className="inline tabular-nums">-{suggestion.hit_cost} pts</dd>
          </div>
        )}
      </dl>
      <ul className="mt-3 space-y-1 text-sm text-zinc-600 dark:text-zinc-300">
        {suggestion.rationale.map((line, i) => (
          <li key={i} className="flex gap-1.5">
            <span className="text-zinc-400">&bull;</span>
            <span>{line}</span>
          </li>
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
        {snapshot.meta.analysis_horizon_gws}-gameweek look-ahead.
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
