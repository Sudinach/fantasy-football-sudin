import { z } from "zod";

// Mirrors analysis/src/fpl_analysis/snapshot.py's build_snapshot() output.
// Any drift between the Python producer and this schema fails loudly at
// build time (see lib/snapshot.ts) instead of rendering `undefined`.

const FixtureDifficultySchema = z.object({
  event: z.number(),
  opponent: z.string(),
  is_home: z.boolean(),
  difficulty: z.number(),
});

const SquadPlayerSchema = z.object({
  player_id: z.number(),
  web_name: z.string(),
  club: z.string(),
  club_id: z.number(),
  position: z.enum(["GK", "DEF", "MID", "FWD"]),
  squad_role: z.enum(["starting", "bench"]),
  is_captain: z.boolean(),
  is_vice_captain: z.boolean(),
  now_cost: z.number(),
  bought_price: z.number(),
  sell_price: z.number(),
  status: z.string(),
  news: z.string(),
  chance_of_playing_next_round: z.number().nullable(),
  total_points_season: z.number(),
  recent_gw_points: z.array(z.number()),
  trend: z.number().nullable(),
  consistency: z.number().nullable(),
  defcon_hit_rate: z.number().nullable(),
  fixture_difficulty_next_3: z.array(FixtureDifficultySchema),
  quality_score: z.number(),
});

const PlayerRefSchema = z.object({
  player_id: z.number(),
  web_name: z.string(),
  position: z.string(),
});

const SuggestionSchema = z.object({
  id: z.string(),
  player_out: PlayerRefSchema,
  player_in: PlayerRefSchema,
  cost_delta: z.number(),
  projected_point_gain: z.number(),
  hit_cost: z.number(),
  net_projected_gain: z.number(),
  free_transfers_available_at_suggestion: z.number(),
  rationale: z.array(z.string()),
});

const ChipAdviceSchema = z.object({
  chip: z.enum(["wildcard", "freehit"]),
  is_available: z.boolean(),
  recommended: z.boolean(),
  target_gameweek: z.number().nullable(),
  reasoning: z.array(z.string()),
});

export const SnapshotSchema = z.object({
  schema_version: z.number(),
  generated_at: z.string(),
  gameweek: z.object({
    current: z.number(),
    next_deadline: z.string().nullable(),
    is_current_gw_finished: z.boolean(),
  }),
  manager: z.object({
    entry_id: z.number(),
    team_name: z.string(),
    manager_name: z.string(),
    overall_rank: z.number(),
    total_points: z.number(),
    bank: z.number(),
    team_value: z.number(),
    free_transfers_available: z.number(),
  }),
  squad: z.array(SquadPlayerSchema),
  points_trend: z.object({
    by_gameweek: z.array(
      z.object({ event: z.number(), points: z.number(), overall_rank: z.number() })
    ),
  }),
  suggestions: z.array(SuggestionSchema),
  chip_advice: z.array(ChipAdviceSchema),
  meta: z.object({
    analysis_horizon_gws: z.number(),
    trend_window_gws: z.number(),
    scoring_weights: z.record(z.string(), z.number()),
    source_data_as_of_event: z.number(),
  }),
});

export type Snapshot = z.infer<typeof SnapshotSchema>;
export type SquadPlayer = z.infer<typeof SquadPlayerSchema>;
export type Suggestion = z.infer<typeof SuggestionSchema>;
export type ChipAdvice = z.infer<typeof ChipAdviceSchema>;
