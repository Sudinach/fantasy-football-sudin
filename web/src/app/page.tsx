import { readSnapshot } from "@/lib/snapshot";
import type { SquadPlayer } from "@/lib/types";

const DIFFICULTY_STYLES: Record<number, string> = {
  1: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200",
  2: "bg-lime-100 text-lime-800 dark:bg-lime-900 dark:text-lime-200",
  3: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  4: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
  5: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
};

const STATUS_STYLES: Record<string, string> = {
  available: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  doubtful: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  injured: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  suspended: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  unavailable: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
};

function FixtureStrip({ player }: { player: SquadPlayer }) {
  if (player.fixture_difficulty_next_3.length === 0) {
    return <span className="text-xs text-zinc-400">No fixtures scheduled</span>;
  }
  return (
    <div className="flex gap-1">
      {player.fixture_difficulty_next_3.map((f) => (
        <span
          key={`${f.event}-${f.opponent}`}
          title={`GW${f.event}: ${f.is_home ? "vs" : "at"} ${f.opponent} (difficulty ${f.difficulty})`}
          className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${DIFFICULTY_STYLES[f.difficulty] ?? ""}`}
        >
          {f.opponent.slice(0, 3).toUpperCase()}
        </span>
      ))}
    </div>
  );
}

function PlayerRow({ player }: { player: SquadPlayer }) {
  return (
    <tr className="border-b border-zinc-100 last:border-0 dark:border-zinc-800">
      <td className="py-2 pr-2">
        <div className="flex items-center gap-1.5">
          <span className="font-medium">{player.web_name}</span>
          {player.is_captain && (
            <span className="rounded bg-zinc-900 px-1 text-[10px] font-bold text-white dark:bg-zinc-100 dark:text-zinc-900">
              C
            </span>
          )}
          {player.is_vice_captain && (
            <span className="rounded border border-zinc-400 px-1 text-[10px] font-bold text-zinc-500">
              VC
            </span>
          )}
        </div>
        <div className="text-xs text-zinc-500 dark:text-zinc-400">
          {player.position} &middot; {player.club}
        </div>
      </td>
      <td className="px-2 py-2 text-right tabular-nums">£{player.now_cost.toFixed(1)}m</td>
      <td className="px-2 py-2">
        <span className={`rounded px-1.5 py-0.5 text-xs ${STATUS_STYLES[player.status] ?? ""}`}>
          {player.status}
        </span>
        {player.news && <div className="mt-0.5 max-w-40 text-xs text-zinc-500">{player.news}</div>}
      </td>
      <td className="px-2 py-2 text-right tabular-nums">
        {player.trend !== null ? player.trend.toFixed(1) : "—"}
      </td>
      <td className="px-2 py-2 text-right tabular-nums">
        {player.consistency !== null ? player.consistency.toFixed(2) : "—"}
      </td>
      <td className="px-2 py-2 text-right tabular-nums font-medium">{player.quality_score.toFixed(0)}</td>
      <td className="px-2 py-2">
        <FixtureStrip player={player} />
      </td>
    </tr>
  );
}

function SquadTable({ title, players }: { title: string; players: SquadPlayer[] }) {
  return (
    <section className="mb-6">
      <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-500">{title}</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-zinc-500">
              <th className="pb-1 pr-2 font-normal">Player</th>
              <th className="px-2 pb-1 text-right font-normal">Cost</th>
              <th className="px-2 pb-1 font-normal">Status</th>
              <th className="px-2 pb-1 text-right font-normal">Trend</th>
              <th className="px-2 pb-1 text-right font-normal">Consistency</th>
              <th className="px-2 pb-1 text-right font-normal">Quality</th>
              <th className="px-2 pb-1 font-normal">Next 3</th>
            </tr>
          </thead>
          <tbody>
            {players.map((p) => (
              <PlayerRow key={p.player_id} player={p} />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default function SquadPage() {
  const snapshot = readSnapshot();
  const starting = snapshot.squad.filter((p) => p.squad_role === "starting");
  const bench = snapshot.squad.filter((p) => p.squad_role === "bench");

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="text-xl font-semibold">{snapshot.manager.team_name}</h1>
        <p className="text-sm text-zinc-500">
          {snapshot.manager.total_points} pts &middot; rank{" "}
          {snapshot.manager.overall_rank.toLocaleString("en-GB")} &middot; bank £
          {snapshot.manager.bank.toFixed(1)}m &middot; {snapshot.manager.free_transfers_available} FT
          {snapshot.manager.free_transfers_available === 1 ? "" : "s"}
        </p>
      </div>
      <SquadTable title="Starting XI" players={starting} />
      <SquadTable title="Bench" players={bench} />
    </div>
  );
}
