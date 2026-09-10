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

# Rebuild the changelog pages from the GitHub release notes.
# `just refresh-changelog` for all four, or name one: `just refresh-changelog bmcd`.
#
# Committed rather than fetched at build time, for the same reason the OpenAPI
# document is: the site builds offline and reproducibly, and a change to the
# history arrives as a reviewable diff instead of appearing the next time CI
# runs. Needs `gh` authenticated; it reads public releases and writes nothing.
refresh-changelog *COMPONENTS:
    ./scripts/refresh-changelog.py {{COMPONENTS}}
