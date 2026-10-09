# Maintenance

## Layout

```text
README.md                     profile page (live blocks between <!-- NAME:START/END --> markers)
data/profile.json             all project, skill, leadership and timeline content
data/insights.json            weekly "design decision" entries (each tied to a real repo)
scripts/svgkit.py             palette, font subsetting/embedding, text measurement, primitives
scripts/build_hero.py         hero.svg + hero-static.svg
scripts/build_assets.py       buttons, pipeline, project cards, architecture diagrams, matrix, leadership, timeline
scripts/update_activity.py    live: recent repos table, contribution map, weekly insight
scripts/validate.py           quality gate (offline; --online also checks links)
fonts/                        Inter / JetBrains Mono static subsets + OFL licenses
assets/                       generated output. Do not hand-edit; rebuild instead
.github/workflows/update-profile.yml
```

## Common tasks

```bash
pip install -r scripts/requirements.txt

python scripts/build_assets.py                          # rebuild every static graphic
GITHUB_TOKEN=$(gh auth token) python scripts/update_activity.py   # refresh live blocks locally
python scripts/validate.py --online                     # before every publish
```

- **Add or edit a project.** Edit `data/profile.json` (`flagships`, `groups[].projects` or `more`), rebuild, then add or update its README block. Card text is measured with the real font metrics, and the build fails loudly if a tagline would overflow the card.
- **Add a design decision.** Append to `data/insights.json` with a title, a body of about 200 characters, the project and its repo URL. It enters the weekly rotation automatically.
- **Hide a repo from "Recently active".** Add it to `activity.exclude`. Repos need a curated description in `activity.descriptions` or a GitHub description to appear. Demo links come only from `activity.demos`, never from repo homepage fields.
- **Change colors or type.** Edit the constants at the top of `scripts/svgkit.py` and rebuild.

## Automation

The workflow runs daily at 06:17 UTC, on manual dispatch, and on pushes that touch data, scripts or fonts. It needs only `contents: write` and the built-in `GITHUB_TOKEN`; there are no secrets. Every API step fails soft, so if GitHub's API is down the previous table and graphics stay in place. Commits made with `GITHUB_TOKEN` do not re-trigger the workflow.

> The contribution total generated in Actions reflects what GitHub shows publicly for the account. If "Include private contributions on my profile" is off, it may be lower than a run with your personal token.

## Before publishing changes

1. `python scripts/validate.py --online`
2. View the README on GitHub in light and dark mode and on a phone. Images are served through GitHub's camo proxy, so check that animations play and fonts render.
3. Pin the six flagship and discipline repos on the profile: TalonCV, Morph, observ-e, CampGrids, ConfusionClassifier, ComputeCollaborative.
