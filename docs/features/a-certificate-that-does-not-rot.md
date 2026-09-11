---
hide:
  - navigation
  - toc
---

<div class="tp-hero-band tp-one-screen" markdown>
<span class="tp-eyebrow">Feature</span>
# A certificate that does not rot

<p>The board serves its login page over HTTPS, and on stock firmware that certificate is unusable by any browser made since 2017, expires in thirty days, and is never replaced. This fork fixes all three.</p>
</div>

<div class="tp-proof">
<div><b>825 days</b><span>validity, renewed 30 days before it ends</span></div>
<div><b>5</b><span>key types served, each proved by a real handshake</span></div>
<div><b>0</b><span>certificates this firmware will overwrite that it did not issue</span></div>
</div>

??? note "The argument, and the measurements behind it"

    A BMC is reachable before it is enrolled in anything, so it has to speak TLS
    on its own from the first boot. That certificate is not a formality: it is
    what protects the password typed into the login page on the management
    network, which is the break-glass path and the whole reason the board keeps
    its own interface.

    ## What the stock certificate actually is

    One line of the factory script, and four problems in it:

    ```sh
    openssl req -x509 -newkey rsa:4096 -nodes -subj "/CN=Turing-Pi self signed"
    ```

    **No subjectAltName.** Every browser has matched the name against the SAN and
    ignored the common name since 2017. A certificate with no SAN cannot be
    accepted by any of them — not by clicking through in some, and never by a
    tool that checks properly. A self-signed certificate nobody can choose to
    trust is decoration.

    **No `-days`,** so openssl's default of thirty applies, and the script only
    regenerated when a file was *missing*. A board left running served an expired
    certificate for as long as it stayed up. One of ours did for over a year.

    **RSA 4096** on a board with about 87 MB of usable RAM, for a key protecting
    a local login.

    **A pair check that could delete your certificate.** It compared RSA moduli,
    which fails outright on any key that is not RSA — and the failure branch
    removes both files and regenerates. Install an EC or Ed25519 certificate on
    stock firmware and the next boot can throw it away.

    ## What it is here

    Named, so a browser can accept it: the board's hostname, its `.local` name
    and every global address it currently holds. **825 days** of validity, the
    longest a publicly trusted certificate may have, and it reissues **30 days
    before expiry** — so neither a long uptime nor a month powered off produces
    an expired certificate. EC P-384 rather than RSA 4096.

    And it will not touch a certificate it did not issue. A certificate from a
    real certificate authority is left exactly where it is, expired or not, with
    a warning rather than a replacement. Fifteen assertions cover this in CI, and
    the two that matter most check that somebody else's certificate comes back
    byte for byte unchanged.

    ## TLS 1.3, and why 1.2 was not merely dated

    The daemon's acceptor was built from Mozilla's version 4 intermediate
    profile, which pins the maximum protocol version to TLS 1.2. The board's
    OpenSSL is 3.5.7 and was capable of 1.3 the whole time.

    That was not a cosmetic gap. Under TLS 1.2 a client's `supported_groups`
    extension constrains the curve of the **server's** certificate as well as the
    key exchange, so a client whose curve list stops at P-256 cannot use a P-384
    certificate at all and the handshake simply fails.

    That is not hypothetical. It is what happened here: a gateway holding a
    perfectly valid client certificate failed every connection to a board, while
    the page in front of it drew correctly and every board card read "did not
    answer". The only trace anywhere was a counter inside the proxy.

    Under TLS 1.3 the certificate's curve is governed by `signature_algorithms`
    instead, and the problem does not arise. TLS 1.2 remains available, because a
    BMC is reached with whatever client is to hand.

    ## Whatever key you install, it is served

    RSA, EC P-256, P-384 and P-521, and Ed25519. Each one is covered by a test
    that performs a **real handshake against the real acceptor** over both
    protocol versions, so it exercises the cipher list and the signature
    algorithms rather than only parsing a PEM file.

    This matters at renewal time, which is the worst moment to discover that a
    daemon quietly served only some key types.

    ## The board tells you before it expires

    ```
    bmcd_tls_certificate_expiry_timestamp_seconds 1.79e+09
    bmcd_tls_certificate_info{key="ecdsa-p384"} 1
    ```

    A number a scrape can alert on is the difference between noticing an expiry
    and a calendar reminder somebody stops reading. The key label is the first
    thing anyone reaches for when a client will not negotiate.

    Both are read from the certificate the daemon actually loaded, at start, so
    the metric cannot disagree with the listener about which certificate is in
    use — replacing the file without restarting is exactly when a fresh read
    would describe something that is not being served.

    !!! note "Why no series is better than a zero"
        A daemon that cannot make sense of the date reports **nothing** rather
        than `0`. Zero reads as 1 January 1970, which is comfortably expired, and
        would fire every alert ever written against that metric on a board whose
        certificate is fine.

    ## What is next

    The board still receives its key from elsewhere when it is enrolled into a
    real authority. The next step is for it to generate its own key and emit a
    certificate signing request, so the private key never leaves the board at
    all — which also makes it enrollable into any internal PKI rather than one
    particular setup.

<div class="tp-next">
<a href="../../#demo/fork"><b>See the interface it protects →</b><span>The login page, and everything behind it.</span></a>
<a href="../one-page-over-every-board/"><b>One page over every board →</b><span>What the client certificate on that connection buys.</span></a>
<a href="../../reference/metrics/"><b>Every metric the board exposes →</b><span>Including the expiry above.</span></a>
<a href="../../reference/known-faults/"><b>What is still not fixed →</b><span>The honest list, with tickets.</span></a>
</div>
