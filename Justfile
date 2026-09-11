# One site: turingpi.xyz (moved from turing.excavador.xyz, SQU-189).
#
# MkDocs is the only Python in this estate -- everything else is Node 24 or
# Rust. That was a deliberate trade for Material's docs UX; devbox contains the
# cost rather than letting it spread.

default:
    @just --list

# Build into site/
build:
    mkdocs build --strict

# Refresh the API document from a bmcd release. `just refresh-api v2.26.0`
#
# The spec is committed rather than fetched at build time, so the site builds
# offline and reproducibly, and so a change to the API arrives as a reviewable
# diff instead of appearing silently the next time CI runs.
refresh-api version:
    gh release download {{version}} --repo excavador-turing/bmcd \
        --pattern openapi.json --output docs/reference/openapi.json --clobber
    @just _describe-api
    ./scripts/generate-api-pages.py

# What the committed document says about itself. Its own version is the thing
# to read: a spec that reports a different release than the one you fetched
# means the download did not land.
_describe-api:
    #!/usr/bin/env python3
    import json
    doc = json.load(open("docs/reference/openapi.json"))
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

# Serve with live reload
serve:
    mkdocs serve

# --strict fails on a broken internal link. This site points at repositories
# that move; the link check is the only thing that notices when one of them
# moves out from under a page.
check: build

clean:
    rm -rf site

# Which bmcd release gained which API operation.
#
# NOT `mike`. SQU-152 asked for versioning "the Reference section only", and
# mike cannot do that -- it publishes whole-site versions and would version
# Features and Guides too, which the same ticket refuses. The reader's real
# question is narrower and one table answers it.
refresh-api-history *ARGS:
    ./scripts/api-history.py {{ARGS}}

# Rebuild the changelog pages from the GitHub release notes.
# `just refresh-changelog` for all four, or name one: `just refresh-changelog bmcd`.
#
# Committed rather than fetched at build time, for the same reason the OpenAPI
# document is: the site builds offline and reproducibly, and a change to the
# history arrives as a reviewable diff instead of appearing the next time CI
# runs. Needs `gh` authenticated; it reads public releases and writes nothing.
refresh-changelog *COMPONENTS:
    ./scripts/refresh-changelog.py {{COMPONENTS}}

# Rebuild the fork pane of the demo from a BMC-UI checkout at a tag.
#   just refresh-demo ../BMC-UI v3.19.0
#
# The pane is the real interface -- the same bundle a board serves -- built
# with VITE_DEMO=1 so it answers from its captured fixtures, and with the
# site's subpath as its base. Committed rather than built in CI, like the
# API document and the changelog: the site builds offline, and a new demo
# arrives as a reviewable diff. The tag is what the firmware pins; check
# `docs/changelog/firmware.md` if unsure.
refresh-demo checkout tag:
    #!/usr/bin/env bash
    set -euo pipefail
    src="{{checkout}}"
    test -f "$src/package.json" || { echo "not a BMC-UI checkout: $src" >&2; exit 1; }
    git -C "$src" fetch --tags -q origin
    git -C "$src" checkout -q "{{tag}}"
    ( cd "$src" && npm ci --no-audit --no-fund >/dev/null && \
      VITE_DEMO=1 VITE_BASE=/demo/fork/ BMC_UI_VERSION="{{tag}}" npm run build >/dev/null )
    rm -rf docs/demo/fork && mkdir -p docs/demo/fork
    cp -a "$src/dist/." docs/demo/fork/
    echo "demo fork pane: {{tag}} ($(find docs/demo/fork -type f | wc -l) files)"
    python3 scripts/demo-ribbon.py

# The fork demo pane the way the site deploys it: from the latest BMC-UI
# release. Needs a BMC-UI checkout to build in, and gh for the release lookup.
demo-fork-latest checkout:
    #!/usr/bin/env bash
    set -euo pipefail
    tag=$(gh api repos/excavador-turing/BMC-UI/releases/latest --jq .tag_name)
    just refresh-demo "{{checkout}}" "$tag"
    echo "$tag" > docs/demo/fork/VERSION
