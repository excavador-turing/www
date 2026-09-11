---
hide:
  - navigation
  - toc
---

<div class="tp-hero-band" markdown>
<span class="tp-eyebrow">Feature</span>
# The board describes its own API

<p>Upstream documented its API in prose on a web page. This fork's daemon serves an OpenAPI 3.1 document describing every operation it has, and that document is the source both this site's reference and the interface's own types are generated from.</p>
</div>

<div class="tp-proof">
<div><b>33</b><span>operations, described by the board itself</span></div>
<div><b>3</b><span>things generated from that description</span></div>
<div><b>0</b><span>hand-written pages that can drift</span></div>
</div>

A prose page is a description of an API that drifts from it. Nothing checks
it, nothing regenerates from it, and the moment a handler changes the page is
quietly wrong. The only way to find out is to call the endpoint and compare.

The document the board serves cannot drift in that way, because it is what
everything else is built from.

## What is in it

| | |
|---|---|
| Operations | 33 |
| Paths | 26 |
| Schemas | 44 |
| Version | OpenAPI 3.1 |

Every operation carries its parameters, its response schema, and the shape of
a refusal. The legacy spelling upstream used — `GET /api/bmc?opt=get&type=about`
— is described too, because it still works and scripts still use it. It
answers `{"response":[{"result":…}]}` and puts a refusal's message inside
`result`; the newer path answers the bare result and sets a real status code.
Both are documented rather than one being pretended away.

## Three things are generated from it, not written

**This site's API reference.** Every page under
[the API reference](../reference/api/index.md) is emitted from the committed
document by `just refresh-api`. They are never hand-edited — a page saying
something the board does not do would be the exact failure the document
exists to prevent.

**The interface's TypeScript types.** BMC-UI used to hand-write twenty-three
interfaces describing the daemon's responses. They are now aliases onto a file
generated from the same document, and CI regenerates and diffs it. A hand edit,
or a pin moved without regenerating, fails in CI rather than on a board.

**The contract tests.** The daemon's own tests validate real responses against
the schemas, so a captured response is by construction a valid one. That is
what makes the [live demo](../demo/fork/) honest: its fixtures are real
captures that the schema already accepts.

## The version is pinned, so a diff is an API change

The document is committed at a pinned daemon release, and the site names which
one it was rendered from. That is the whole discipline: regenerating produces
a diff exactly when the API changed, and never otherwise. A reference that
regenerates from whatever is currently running would show the reader today's
board and tell them nothing about what changed.

!!! note "What this does not give you"
    A served description is not a served playground. There is no request
    console on this site, deliberately — the operations that matter here power
    modules off and flash them, and a documentation page is the wrong place to
    have that one click away from a reader who is browsing.

<div class="tp-next">
<a href="../../#demo/fork"><b>See the interface →</b><span>Built from the types this document generates.</span></a>
<a href="../../reference/api/"><b>Every operation →</b><span>The generated reference, one page per group.</span></a>
<a href="../../reference/cli/"><b>The command line →</b><span><code>tpi</code> reaches every endpoint the document describes.</span></a>
<a href="../pick-a-version/"><b>Pick a version →</b><span>The next feature: sources, candidates and checksums.</span></a>
</div>
