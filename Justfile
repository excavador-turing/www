# One site: turingpi.xyz (moved from turing.excavador.xyz, SQU-189), built
# with Astro Starlight in site/. It was Material for MkDocs until
# 2026-10-26, when Material went into maintenance mode.
#
# Two toolchains, both from devbox: Node for the site, Python for the
# generators that write its pages and the checks that judge what was built.

default:
    @just --list

# Install the build's dependencies exactly as the lockfile says.
install:
    cd site && yarn install --immutable

# A strict build into site/dist: no warning, no broken internal link,
# no LFS pointer, and what the site must carry (search, llms.txt, the feed).
build: install
    site/scripts/strict-build.sh
    site/scripts/stamp-build.py
    site/scripts/check-built.sh

# The site on http://localhost:4321 with live reload.
serve: install
    cd site && yarn dev

# Refresh the API document from a bmcd release. `just refresh-api v2.26.0`
#
# The spec is committed rather than fetched at build time, so the site builds
# offline and reproducibly, and so a change to the API arrives as a reviewable
# diff instead of appearing silently the next time CI runs.
refresh-api version:
    gh release download {{version}} --repo excavador-turing/bmcd \
        --pattern openapi.json --output site/public/reference/openapi.json --clobber
    @just _describe-api
    ./scripts/generate-api-pages.py

# What the committed document says about itself. Its own version is the thing
# to read: a spec that reports a different release than the one you fetched
# means the download did not land.
_describe-api:
    #!/usr/bin/env python3
    import json
    doc = json.load(open("site/public/reference/openapi.json"))
    print("openapi {} from bmcd {}: {} paths, {} schemas".format(
        doc["openapi"], doc["info"]["version"],
        len(doc["paths"]), len(doc["components"]["schemas"])))

# Rewrite the gate's record from a board. `just refresh-gate-history 192.168.77.20`
#
# The page says every count on this site comes from the board. It did not:
# the numbers were typed in, and had drifted from 14 to 17 within a day of
# being written. This is what makes the claim true. It needs a route to a
# board, so it runs here and the result is committed -- CI has no such route
# and must never be the thing that notices.
refresh-gate-history board:
    ./scripts/refresh-gate-history.py {{board}}

# Everything CI checks, in the order CI checks it. Run this before pushing;
# `site.yaml` runs exactly these, and `publish.yaml` runs them again before
# it deploys.
check: facts-check facts-lint feature-lint ribbon-check build description-lint structured-data llms-check links-internal reach urls screens

# Prove every screen reads whole, at nine viewports.
#
# A page may scroll. A SCREEN may not: a part of a page marked `data-screen`
# is a thing the reader must take in at once, and it must fit, with nothing
# clipped and no picture stretched to fill leftover height.
#
# This replaced `one-screen.py`, which asked only whether the document
# scrolled. The front page cut its cards off mid-sentence at 1366x768 and gave
# a drawing a 501px box at 2560x1440, and neither scrolled, so both passed --
# for 132 seconds of every deploy.
screens: build
    ./scripts/screens.py

# Prove every nav page is within two clicks of the front page, and the
# changelog and roadmap within one -- counting only links a reader can see.
# The changelog was three clicks deep before the tabs and footer existed;
# this is what keeps it from going deep again.
reach: build
    ./scripts/reach.py

# Re-record the faults the site is allowed to have.
#
# 467 the day the gate could first see them. Run this after fixing some, and
# commit the smaller file -- the gate fails on a baselined fault that no
# longer happens, so the count cannot drift back up.
screens-baseline: build
    ./scripts/screens.py --update-baseline

# Every URL turingpi.xyz served under MkDocs still answers: each page, each
# heading anchor a deep link can name, each file. A URL leaves
# site/served-urls.json only with a redirect, or retired with a reason.
urls: build
    ./scripts/served-urls.py

# Rebuild site/src/data/facts.yaml from the pages and data that own each
# number.
facts:
    ./scripts/facts.py

# Prove the eleven feature pages are still one page eleven times.
#
# They shared a skeleton in eleven copies of the markup and it had drifted in
# every direction: ledes from 22 to 48 words, eight different labels opening
# the same demo, proof numbers with no source. <FeatureScreen /> renders the
# shape now; this checks the content a component cannot.
feature-lint:
    ./scripts/feature-lint.py

# Take the demo's exit ribbon off any capture that was taken through it.
# Five of the eleven had it and six did not, so the pages looked like two
# different sites side by side.
crop-ribbon:
    ./scripts/crop-ribbon.py

ribbon-check:
    ./scripts/crop-ribbon.py --check

# Fail if the committed facts file no longer matches its sources.
facts-check:
    ./scripts/facts.py --check

# Fail if a page does not say what it is for, or the built page does not
# carry that description whole.
#
# A page with no description repeats the site's, so all 91 pages once told a
# search result, a link preview and an AI summariser the same sentence about
# the site and nothing about the page.
description-lint: build
    ./scripts/description-lint.py --site site/dist

# The JSON-LD in every built page parses and says what is there, with no
# template left unrendered in it and no description that disagrees with the
# page's meta tag.
structured-data: build
    ./scripts/structured-data.py --strict

# Every href and src in the built HTML lands on a page or file -- the header,
# footer and components included, which starlight-links-validator does not
# see. Under MkDocs 62 links in raw HTML were 404s on the live site until
# this existed.
links-internal: build
    ./scripts/internal-links.py

# Every link that leaves the site still answers. Weekly in CI (links.yml);
# here when you want it now. Needs lychee on the path (devbox has it).
links: build
    lychee --no-progress --base-url https://turingpi.xyz \
        --exclude '^https://turingpi\.xyz' --exclude-path site/dist/demo \
        --exclude localhost --exclude 'turingpi\.local' --exclude '192\.168\.' \
        --exclude 'linkedin\.com' \
        --accept '200..=204,206,301..=308,429' --timeout 20 --max-retries 2 \
        'site/dist/**/*.html'

# The index an assistant reads instead of the nav.
llms:
    ./scripts/llms.py

# llms.txt matches the nav, the build serves it byte for byte, and every link
# in it lands on a built page.
llms-check: build
    ./scripts/llms.py --check --site site/dist

# Fail if a page types a number the facts file owns.
#
# facts.py claimed this script existed from the day it was written -- in its
# own docstring and in the header it generates into facts.yaml -- and it did
# not. The claim shipped and was served on the site inside a generated file.
facts-lint:
    ./scripts/facts-lint.py

clean:
    rm -rf site/dist site/.astro

# Which bmcd release gained which API operation.
#
# NOT `mike`. SQU-152 asked for versioning "the Reference section only", and
# mike cannot do that -- it publishes whole-site versions and would version
# Features and Guides too, which the same ticket refuses. The reader's real
# question is narrower and one table answers it.
refresh-api-history *ARGS:
    ./scripts/api-history.py {{ARGS}}

# Rebuild the changelog pages, the news posts and the feed from each
# repository's CHANGELOG.md. `just refresh-changelog` for all four, or name
# one: `just refresh-changelog bmcd`.
#
# NOT from the GitHub release notes, which is where this used to read. Every
# firmware release note is the same fixed paragraph -- v2.28.0 and v2.32.0,
# fourteen entries apart, published byte-identical bodies -- so the page a
# returning reader comes to for "what changed" said nothing, twenty-eight
# times. The repositories keep real changelogs; those are the source.
#
# Where a release has no changelog entry the release note is used instead and
# the page says so. Neither source is complete: BMC-UI's changelog stops ten
# releases back, and bmcd's carries five versions that only ever shipped
# inside a firmware image.
#
# Committed rather than fetched at build time, for the same reason the OpenAPI
# document is: the site builds offline and reproducibly, and a change arrives
# as a reviewable diff. The hourly publish job runs this and commits what
# moves.
refresh-changelog *COMPONENTS:
    ./scripts/refresh-changelog.py {{COMPONENTS}}

# Rebuild the roadmap from the Ideas discussions and their votes.
#
# The page always claimed the most-voted thing gets done first. It was typed
# by hand, showed no votes and was in no particular order, so the claim could
# not be checked from the page that made it.
refresh-roadmap:
    ./scripts/refresh-roadmap.py

# Everything the hourly job refreshes, in one go.
refresh: refresh-changelog refresh-roadmap facts llms

# Build the fork pane of the demo from a BMC-UI checkout at a tag.
#   just refresh-demo ../BMC-UI v3.19.0
#
# The pane is the real interface -- the same bundle a board serves -- built
# with VITE_DEMO=1 so it answers from its captured fixtures, and with the
# site's subpath as its base. The deploy builds both panes from the latest
# BMC-UI release (publish.yaml); this puts one in place locally, where it is
# git-ignored.
refresh-demo checkout tag:
    #!/usr/bin/env bash
    set -euo pipefail
    src="{{checkout}}"
    test -f "$src/package.json" || { echo "not a BMC-UI checkout: $src" >&2; exit 1; }
    git -C "$src" fetch --tags -q origin
    git -C "$src" checkout -q "{{tag}}"
    ( cd "$src" && npm ci --no-audit --no-fund >/dev/null && \
      VITE_DEMO=1 VITE_BASE=/demo/fork/ BMC_UI_VERSION="{{tag}}" npm run build >/dev/null )
    rm -rf site/public/demo/fork && mkdir -p site/public/demo/fork
    cp -a "$src/dist/." site/public/demo/fork/
    echo "demo fork pane: {{tag}} ($(find site/public/demo/fork -type f | wc -l) files)"
    python3 scripts/demo-ribbon.py

# The fork demo pane the way the site deploys it: from the latest BMC-UI
# release. Needs a BMC-UI checkout to build in, and gh for the release lookup.
demo-fork-latest checkout:
    #!/usr/bin/env bash
    set -euo pipefail
    tag=$(gh api repos/excavador-turing/BMC-UI/releases/latest --jq .tag_name)
    just refresh-demo "{{checkout}}" "$tag"
    echo "$tag" > site/public/demo/fork/VERSION
