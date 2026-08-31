# Boston Villa FC — matchday page

A single-page fixture list, ground directions and league table for Boston Villa FC,
Over 62 Division 2 (Central flight), Fall 2026.

It exists because the league's own team page is hard to move around in: the kick-off
times that differ from the usual 10:00 AM are easy to miss, and the grounds are listed
as plain text with no way to navigate to them.

**Live page:** https://michaelhopkins.github.io/boston-villa/

## How it works

`index.html` has no build step and no dependencies. Fixture and standings data lives
in `data.json` beside it and is fetched same-origin at load; the page never contacts
the league's servers. Club logos are deliberately not loaded for the same reason.

Two things adapt on their own:

- **The next match** is chosen from the browser's current date, so it advances through
  the season without an edit.
- **The running order** puts the league table first once any club has `gp > 0`, and
  leads with the next match before then.

## Updating the data

`data.json` is rewritten hourly by `.github/workflows/refresh.yml`, which runs
`scripts/fetch_data.py` on a GitHub runner. Nothing needs to run on your machine.
The job writes only `data.json`, and only when the fixtures or table actually
differ — an unchanged week produces no commit at all.

### Refreshing it by hand

GitHub treats scheduled workflows as best-effort and drops most firings on free
public repos — in practice this runs every few hours, not every hour. That's
usually fine, since referees take a day or two to file. When you already know a
score has been posted and want the page to catch up now:

**https://github.com/michaelhopkins/boston-villa/actions/workflows/refresh.yml**
→ *Run workflow* → *Run workflow*

Takes about twenty seconds, then another thirty for Pages to redeploy. Worth
bookmarking on your phone alongside the page itself. From a terminal it's
`gh workflow run refresh.yml`.

### Endpoints

The numbers come from the league's public JSON API, which needs no authentication:

```
https://reg.mass-soccer.org/api/standings/?league_id=7&season_id=179&bracket_id=60&division_id=152
https://reg.mass-soccer.org/api/games/?league_id=7&season_id=179&bracket_id=60&division_id=152&team_id=30071&fa=1
```

Note it is served from `reg.mass-soccer.org`, not the `victory.mass-soccer.org` host the
public site runs on. The API is CORS-locked to the league's own domain, so the page
cannot fetch it from a browser — any refresh has to happen server-side.

Use `game_datetime` for kick-off times. The `game_time` and `game_time_text` fields in
the same records are UTC and format misleadingly (the 10:00 AM opener reads "02:00 PM").

Be a considerate guest: at most one poll an hour, and send `If-None-Match` with the
`ETag` so unchanged data costs them almost nothing.

## Venue corrections

Any fixture may carry a `moved` block, used when we've been told a game isn't where the
league says it is. It renders as a *Moved* flag with the league's listing still shown
underneath, rather than silently replacing it — so anyone cross-checking against the
official page can see why the two differ, and where the correction came from.

These live in the `OVERRIDES` block in `index.html`, keyed by game date, and are
merged in the browser — so the hourly refresh, which only rewrites `data.json`,
can never clobber them. Delete an entry once the league's listing catches up.

The Aug 30 opener is the current example: Hopkinton's manager says it's at Fruit Street
Athletic Complex, roughly three miles from the listed high school field, and turf rather
than grass. The league listing still shows the old ground.
