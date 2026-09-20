# turingpi.xyz

The site for [this fork of the Turing Pi 2 BMC firmware](https://github.com/excavador-turing).
Material for MkDocs, built by CI, deployed to GitHub Pages.

```
just            # the recipes
just serve      # live reload on :8000
just check      # everything CI checks, in the order CI checks it
```

The environment is devbox and direnv: `cd` into the repository and the venv
builds itself. Nothing here needs a board except `just refresh-gate-history`.

## Four rules, and why each one exists

Everything below was learned by getting it wrong first. If a rule looks
arbitrary, the paragraph under it is the reason.

### A screen is a promise, and it is measured

A **page** may scroll. A **screen** may not: a section marked `data-screen` is
something a reader must take in at once, and it must fit the viewport with
nothing clipped and no picture stretched to fill leftover height.

The promise lives in the stylesheet, not the markup. A section is claiming to
be a screen only while its computed `min-height` is viewport-sized, so where
the CSS releases that -- on a phone, where a screenshot, a heading, a
paragraph and three numbers genuinely do not fit 667px -- the page stacks and
scrolls, and `scripts/screens.py` stops asking.

`just screens` measures every built page at nine viewports. It is in
`checks.yml`, which runs on pull requests, and **not** in the deploy.

> The front page used to be locked to one screen with no scrolling at all.
> That constraint is what broke it: the destination pictures took whatever
> height was left over, so the same drawing got a 90px box on a 1280x720
> laptop and a 501px box on a 2560x1440 monitor, and on the short screens the
> sentence under each card was cut off — 69px of it at 1280x720. None of that
> scrolled, and "does the document scroll" was the only question the old gate
> asked. All five viewports it asked at were in the clean middle.

**Height fails before width.** A 1366x768 laptop fails where a 1440x900 has
room. Tier on `max-height`, not only `max-width`, and set the same words
smaller rather than hiding any of them.

### Every fact has one home

`docs/data/facts.yaml` (`just facts`) holds every number the site quotes about
itself, each with where it came from and when. Pages ask for it —
`{{ gate.promoted }}`, never `26` — through the macros plugin, which is
**opt-in per page** via `render_macros: true`. Opt-in because macros expands
Jinja before Markdown and would otherwise eat the Prometheus alert template in
`reference/metrics.md`.

> Five numbers had already drifted apart. The features index said 18 updates
> where the board said 26. About said 66 releases where the changelog said
> 107, and 4 open faults where the list had 5. None were wrong when written.
> They were written more than once.

The changelog and the roadmap are generated too, from each repository's
`CHANGELOG.md` and from the Ideas discussions and their votes. Generated
output is **committed**, so the site builds offline and a change arrives as a
reviewable diff — and because nobody remembers to run the scripts, the hourly
Pages job runs them and commits what moved.

### A feature is a page, and every feature page is the same page

Data in front matter, rendered by `main.py`. The index is generated from those
pages, so the count cannot disagree with them. `just feature-lint` enforces
the content: lede 25–35 words, three proofs each with a source and a date,
four next links in the fixed roles `demo`, `do`, `evidence`, `related`
reaching four different places, a capture and an icon that exist.

Captures are full interfaces at 2240 wide, taken from the demo, with the exit
ribbon removed (`just crop-ribbon`). A cropped card is a second picture, never
the only one.

> The skeleton used to live in eleven copies of the markup. Ledes ran 22 to 48
> words in two voices, eight different labels opened the same demo, and five
> captures carried the demo's lime ribbon while six did not.

### The deploy publishes; it does not judge

`pages.yml` builds and deploys. `checks.yml` runs every check, on pull
requests. Make Checks a required check on `main`: it is the only thing between
a bad layout and the live site.

> The screen gate used to be 132 seconds of a 178-second deploy, while
> building the site took 3. Publishing a typo waited two minutes on a browser
> re-measuring pages that had not changed — and a layout regression should
> block a merge anyway, because by the time a deploy runs the change is
> already on `main`.

## What is generated, and by what

| output | recipe | source |
|---|---|---|
| `docs/data/facts.yaml` | `just facts` | the pages and data that own each number |
| `docs/changelog/*.md`, `docs/feed.xml` | `just refresh-changelog` | each repository's `CHANGELOG.md`, with the release note where there is no entry |
| `docs/roadmap.md`, `docs/data/roadmap.json` | `just refresh-roadmap` | the Ideas discussions and their votes |
| `docs/reference/api/*.md` | `just refresh-api vX.Y.Z` | the board's own OpenAPI document |
| `docs/reference/api-history.md` | `just refresh-api-history` | which release gained which operation |
| `docs/reference/gate-history.md` | `just refresh-gate-history <board ip>` | a real board's promotion counter |
| `docs/demo/{fork,fleet}/` | built at deploy | the latest `BMC-UI` release |

`just refresh` runs the three the hourly job runs. The gate history needs a
route to a board, so it runs on a workstation and the result is committed; CI
has no such route and must never be the thing that notices.

## Things that will bite

- **The demo panes are not in this repository.** They are built at every
  deploy from the latest `BMC-UI` release and are gitignored. Locally:
  `just demo-fork-latest <BMC-UI checkout>`. A pane is proved to be a demo
  build before it publishes, including when it comes from the cache.
- **Media is in Git LFS.** A checkout without `lfs: true` publishes 130-byte
  pointer files as the images: a build that succeeds and a site that is
  broken.
- **Material's instant loading rewrites every content href to an absolute URL
  after load.** A selector on `a[href="#x"]` finds nothing; `a[href$="#x"]`
  does.
- **A markdown-attributed div wraps a raw block child in a `<p>`.** That is
  how the front page's explainer card ended up 468px wide in a 1368px row.
  Raw HTML for anything whose width matters.
- **`turing.excavador.xyz` is dead** and has been since the docs moved here.
  Never link it.
- **This site is not Turing Machines.** The footer says so on every page, and
  it should keep saying so.

## Layout

```
docs/            the site
  data/          generated facts, roadmap data, the screen baseline
  features/      one page per feature; data in front matter
  why/           the full argument behind each feature
  changelog/     generated from each repository's CHANGELOG.md
overrides/       the footer, and the analytics beacon
main.py          macros: the feature template and the index
scripts/         every generator and every check
```
