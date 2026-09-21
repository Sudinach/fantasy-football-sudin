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

**Chip**:
A one-per-window special power a manager can play instead of the normal transfer rules. FPL's current chips are Wildcard, Free Hit, Bench Boost, and Triple Captain. This app only reasons about Wildcard and Free Hit, since those two affect transfers (its domain); Bench Boost and Triple Captain affect scoring only and are out of scope.

**Wildcard**:
A Chip that makes every transfer in that Gameweek free of Hits, with no cap on how many are made. Offered twice a season, once per Chip Window; left unplayed, it doesn't carry into the next Window.

**Free Hit**:
A Chip like Wildcard (unlimited free transfers for one Gameweek), except the Squad automatically reverts to its pre-Chip state once that Gameweek ends. Used tactically for a single awkward Gameweek (see Blank Gameweek) rather than a lasting squad change.

**Chip Window**:
The span of Gameweeks, per FPL's own bootstrap data, during which one instance of a Chip can be played. Wildcard and Free Hit each get two Windows a season (first half / second half); playing the chip, or letting its Window close unplayed, ends that instance.

**Blank Gameweek**:
A Gameweek in which one or more Premier League clubs have no fixture (postponements, cup schedule clashes), so any Squad player at those clubs scores zero regardless of form.

**Chip Advice**:
A structured, advisory-only recommendation on whether to play Wildcard or Free Hit this Gameweek, and why -- distinct from a Transfer Suggestion, which recommends a single swap instead. Like Transfer Suggestions, Chip Advice is never acted on automatically (see ADR-0002).

**Transfer Suggestion**:
A structured recommendation produced by the analysis: a Player worth selling, paired with a ranked shortlist of 1-3 replacement Players to buy (best first, see Buy Option). Any Hit cost applies to the sell decision itself, not to any one replacement. Suggestions are advisory only — the app does not execute them (see ADR-0002).

**Buy Option**:
One ranked replacement candidate within a Transfer Suggestion: the Player to buy, the cost delta, and the projected point gain over the Look-ahead Horizon. Ranking multiple options per sell decision (rather than a single fixed pick) means an in-demand replacement can legitimately appear under more than one Transfer Suggestion without the list reading as duplicated.

**Snapshot**:
The JSON output of one analysis run: the Squad state, computed Trend/Consistency figures, and the resulting Transfer Suggestions at that point in time. Each run's Snapshot is committed to the repo, so the accumulated Snapshots double as historical data.
