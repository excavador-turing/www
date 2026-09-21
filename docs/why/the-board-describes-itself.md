---
title: The board describes its own API
description: "Why the API reference is generated from the board's own OpenAPI document rather than written and kept by hand."
---

# The board describes its own API

This is the argument behind [The board describes its own API](../features/the-board-describes-itself.md), with the measurements that back it. The feature page is the short version.

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
[the API reference](../reference/api/operations.md) is emitted from the committed
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

## What it does not cover

A served description is not a served playground. There is no request
console on this site, deliberately — the operations that matter here power
modules off and flash them, and a documentation page is the wrong place to
have that one click away from a reader who is browsing.

<div class="tp-next tp-next--argument"><a href="../../features/the-board-describes-itself/"><b>Back to the feature →</b><span>The short version: the claim, its numbers and the picture.</span></a><a href="../#demo/fork"><b>See it in the demo →</b><span>The interface built from the types this document generates.</span></a><a href="../reference/cli/"><b>Do it on your board →</b><span>tpi reaches every operation the document describes.</span></a><a href="../reference/api/"><b>The evidence →</b><span>Every operation, on pages emitted from the document.</span></a><a href="../see-what-the-board-sees/"><b>See what the board sees →</b><span>The readings those operations return.</span></a></div>
