import PointsTrendChart from "@/components/PointsTrendChart";
import { readSnapshot } from "@/lib/snapshot";

export default function TrendPage() {
  const snapshot = readSnapshot();
  const data = snapshot.points_trend.by_gameweek;

  return (
    <div>
      <h1 className="mb-1 text-xl font-semibold">Points Trend</h1>
      <p className="mb-6 text-sm text-zinc-500">
        {snapshot.manager.team_name}&rsquo;s gameweek points across the season so far.
      </p>
      {data.length === 0 ? (
        <p className="text-sm text-zinc-500">No gameweek history yet.</p>
      ) : (
        <PointsTrendChart data={data} />
      )}
    </div>
  );
}
