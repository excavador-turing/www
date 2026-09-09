# The API

The BMC serves an HTTP API, and this is its description. It is not written by
hand: the daemon emits it, so it describes the code rather than somebody's
memory of the code.

The board you are holding serves its own copy at
`GET /api/bmc/openapi.json`, which is the one to trust if it disagrees with
this page. This page renders the document from a released version, named at
the bottom.

## Two spellings of every operation

Upstream's API routes on query parameters: `GET /api/bmc?opt=get&type=about`.
Everything, including mutations, is a `GET`. That convention is in people's
scripts and in upstream's own `tpi`, so it is not going anywhere.

This fork added a second spelling of the same operations — `GET /api/bmc/about`,
`POST /api/bmc/reboot` — as a routing table over the *same handlers*. Same
JSON, same authentication, same code. Not a v2, and not a migration you are
being asked to make.

They differ in exactly two ways, both about the envelope:

| | legacy `?opt=&type=` | path form |
|---|---|---|
| success | `{"response":[{"result": …}]}` | the bare result, or `204` |
| refusal | the message inside `result`, with a `200` | `application/problem+json` |

The refusal difference is the one that matters. A client reading the legacy
form has to parse a success envelope to discover it failed, and `tpi` shipped
three formatters that got this wrong.

## What the document does and does not describe

Every operation is described: its path, its method, its parameters, which
ones are refused if omitted, and both security schemes.

**Every read operation describes its response body.** The schemas are derived
from the Rust types the daemon serialises, so they cannot drift from what it
sends, and contract tests hold a realistic response against each of them.

Ten of those operations built their answer inline until v2.15.0, and had no
type to derive from. They have one now — reconstructed from what the handler
already sent, not redesigned. A rename would have broken `tpi` and the web
interface for nothing.

Three shapes are odd, and the document describes the oddity rather than
correcting it:

- **`power`, `usb` and `sdcard` answer a one-element array.** That is
  upstream's convention. A schema claiming an object would be a lie that
  compiles, and a client has to index it either way.
- **`sdcard`'s used-bytes field is called `use`.** Upstream's spelling. It is
  also a Rust keyword, so the daemon renames it on the way out, and a test
  asserts the name on the wire rather than the one in the source.
- **`power` reports strings, not booleans.** A rail the daemon cannot read is
  `"Unknown"`, and a boolean would leave a generated client unable to say so.

The daemon still keeps a list of operations that describe nothing, and a test
refuses to let one join it silently. The list is empty, and that is the point
of keeping it.

## Authentication

Two schemes, both described in the document. A bearer token from
`POST /api/bmc/authenticate`, or HTTP basic with the board's root credentials.

Requests from the board itself skip authentication entirely. That is a
[known fault](known-faults.md), not a feature, and since v2.14.0 it at least
leaves an audit line saying so.

`/metrics` is separate and has no such exception: it takes
[its own credential](metrics.md), which cannot touch this API.

!!! note "Which version this is"
    Rendered from **bmcd 2.28.0**, fetched from that release rather than
    written here. Refresh it with `just refresh-api v2.28.0` in the `www`
    repository; the diff is then the API change, which is the point of
    committing it rather than fetching at build time.

    A board running something else serves its own document at
    `GET /api/bmc/openapi.json`, and that one is authoritative for that board.

[OAD(./docs/reference/openapi.json)]
