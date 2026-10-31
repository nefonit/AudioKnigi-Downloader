# AudioKnigi V9 – separate HTTP response timeout from TCP/TLS errors

Based on the user-verified Akniga V7 functionality and V8 description/HLS cache updates.

- Manual HTTPS diagnostic now reports **HTTP response time** separately from DNS, TCP and TLS, including on HTTP 500 responses.
- TCP/TLS success followed by a stalled HTTP response is labeled as HTTP timeout, not suspected TCP filtering.
- A TLS handshake timeout is distinguished from a TCP connect timeout.
- Search diagnostics classify Requests `ReadTimeout` as waiting for a server reply; `ConnectTimeout` remains a TCP error.
- Localized new phrases for English, German and Ukrainian, retaining Russian defaults. No raw request URLs or authentication tokens are shown.
- Does **not** attempt to bypass blocked routes, does not change search APIs or downloading logic. HTTP 500 means remote server error, not a network failure.

Testing: offline unit/integration tests; Windows/real ISP behavior remains to be confirmed by running manual tests on the user's machine.
