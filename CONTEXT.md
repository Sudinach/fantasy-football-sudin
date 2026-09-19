# Fantasy Football Sudin

A personal dashboard that analyzes an FPL manager's squad against live Premier League data and suggests transfers to improve points.

## Language

**Manager**:
The FPL term for the person who owns and manages a fantasy squad — the user of this app.
_Avoid_: User, Team

**Squad**:
A manager's 15 fantasy players (2 GK, 5 DEF, 5 MID, 3 FWD), split into a Starting XI and a Bench.
_Avoid_: Team (overloaded — also used for real-world Premier League clubs)

**Club**:
A real-world Premier League team (e.g. Arsenal). Distinct from a manager's Squad.
_Avoid_: Team

**Player**:
A real Premier League footballer eligible for selection into a Squad. Carries FPL stats (points, form, price, injury status) independent of any manager.

**Entry ID**:
The public numeric identifier for a manager's FPL account, used to fetch their squad and history from the FPL API without authentication. Visible in the URL when viewing "Points" on the official FPL site.
_Avoid_: Team ID, Manager ID

**Gameweek (GW)**:
One round of Premier League fixtures that FPL scores as a single unit; the basic time unit for transfers, deadlines, and scoring.

**Free Transfer (FT)**:
A transfer a manager can make without a points penalty. One is granted per Gameweek, banking up to a cap of 5.

**Hit**:
The -4 point penalty applied to each transfer made beyond the manager's available Free Transfers.

**Trend**:
This app's own computed measure of a Player's point-scoring trajectory across recent Gameweeks, distinct from FPL's built-in `form` stat (a simple last-4-Gameweek average). Trend feeds this app's suggestion ranking, not the official FPL stat.

**Consistency**:
This app's own computed measure of how reliably a Player returns points Gameweek-to-Gameweek, as opposed to a boom-bust profile with the same average.

**Look-ahead Horizon**:
The number of upcoming Gameweeks (default: 3) the suggestion engine considers when weighing fixture difficulty and projected returns for a potential transfer.

**Transfer Suggestion**:
A structured recommendation produced by the analysis: a Player to sell, a Player to buy, the cost delta, the projected point gain over the Look-ahead Horizon, and any Hit cost incurred. Suggestions are advisory only — the app does not execute them (see ADR-0002).

**Snapshot**:
The JSON output of one analysis run: the Squad state, computed Trend/Consistency figures, and the resulting Transfer Suggestions at that point in time. Each run's Snapshot is committed to the repo, so the accumulated Snapshots double as historical data.
