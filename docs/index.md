---
hide:
  - navigation
  - toc
---

<div class="tp-landing" markdown>

<div class="tp-bar">
<nav class="tp-seg tp-switch" aria-label="View">
<a href="#overview" data-view="home">Overview</a>
<a href="#demo/fork" data-view="demo">Live demo</a>
</nav>
<nav class="tp-seg tp-panes" aria-label="Which interface" hidden="hidden">
<a href="#demo/stock" data-pane="stock">Stock firmware</a>
<a href="#demo/fork" data-pane="fork">This fork</a>
<a href="#demo/fleet" data-pane="fleet">turing-fleet</a>
</nav>
</div>

<section class="tp-view tp-view--home" markdown>

<div class="tp-hero" markdown>

# Firmware for the Turing Pi 2 that undoes its own mistakes

<p class="lede">Upstream stopped in February 2025. This fork keeps the board on a supported kernel, makes a bad flash undo itself, and reads the sensors the hardware always had.</p>

<div class="tp-actions"><a class="md-button md-button--primary" href="#demo/fork">Try it, live</a> <a class="md-button" href="guides/install/">Install it</a> <a class="md-button" href="guides/upgrade-from-stock/">Coming from stock?</a></div>

</div>

<div class="tp-claims" markdown>
<div markdown><b>Flash it wrong and lose nothing.</b><span>A new image boots on trial and is kept only if the board comes back right. On this board: 18 updates, 1 automatic rollback, 0 trips to the rack — [read off the board](reference/gate-history.md).</span></div>
<div markdown><b>Update the BMC without touching your nodes.</b><span>Upstream power-cycles all four compute modules during a firmware update. This fork leaves their rails alone.</span></div>
<div markdown><b>Software that is still maintained.</b><span>Kernel 6.12 LTS on Buildroot 2025.02 LTS. Upstream ships 6.8 on an end-of-life Buildroot, and its last release was February 2025.</span></div>
</div>

<div class="tp-dest">
<a class="tp-dest__card" href="#demo/fork"><img src="assets/icons/screen.svg" alt=""><b>Live demo</b><span>Stock and this fork, side by side, answering from a real board's data. Click anything.</span></a>
<a class="tp-dest__card" href="features/"><img src="assets/icons/undo.svg" alt=""><b>Features</b><span>Self-undoing updates, a console to every module, the sensor upstream never read.</span></a>
<a class="tp-dest__card" href="guides/"><img src="assets/icons/book.svg" alt=""><b>Documentation</b><span>Install, upgrade from stock, recover a bad flash, monitor it, and the full API.</span></a>
<a class="tp-dest__card" href="about/"><img src="assets/icons/fork.svg" alt=""><b>About</b><span>Why the fork exists, what changed against upstream, and what is still not fixed.</span></a>
</div>

</section>

<section class="tp-view tp-view--demo" hidden="hidden">
<div class="tp-stage">
<iframe data-pane="stock" data-src="demo/stock/" title="Stock Turing Pi 2 interface, demo" hidden="hidden"></iframe>
<iframe data-pane="fork" data-src="demo/fork/" title="This fork's interface, demo" hidden="hidden"></iframe>
<div class="tp-stage__soon" data-pane="fleet" hidden="hidden"><div><h2>turing-fleet</h2><p>One interface over every board. It is the next thing being built, and this space is honest about that rather than showing a mock-up.</p></div></div>
</div>
<p class="tp-stage__note">Every reading is the board's own, captured off real hardware. Controls refuse and say why. The console replays a recording. <a href="about/#the-demo">What is and isn't real</a> · <a href="demo/fork/" target="_blank" rel="noopener">open this fork full size</a> · <a href="demo/stock/" target="_blank" rel="noopener">open stock full size</a></p>
</section>

<script>
(function () {
  var root = document.querySelector('.tp-landing');
  if (!root || root.dataset.wired) return;
  root.dataset.wired = '1';
  function apply () {
    var h = location.hash.replace(/^#/, '');
    var demo = h.indexOf('demo') === 0;
    var pane = demo ? (h.split('/')[1] || 'fork') : null;
    root.querySelector('.tp-view--home').hidden = demo;
    root.querySelector('.tp-view--demo').hidden = !demo;
    root.querySelector('.tp-panes').hidden = !demo;
    root.querySelectorAll('.tp-switch a').forEach(function (a) {
      a.setAttribute('aria-current', a.dataset.view === (demo ? 'demo' : 'home') ? 'true' : 'false');
    });
    root.querySelectorAll('.tp-panes a').forEach(function (a) {
      a.setAttribute('aria-current', a.dataset.pane === pane ? 'true' : 'false');
    });
    root.querySelectorAll('.tp-stage [data-pane]').forEach(function (el) {
      var on = el.dataset.pane === pane;
      el.hidden = !on;
      if (on && el.tagName === 'IFRAME' && !el.getAttribute('src')) el.setAttribute('src', el.dataset.src);
    });
  }
  // Material's instant loading owns every click on the page. A same-page
  // hash link must stay a hash change, not become a fetch of the page it is
  // already on -- which is what "#" alone turned into once the page had been
  // opened with a hash. Capture phase, so this runs before Material's
  // listener on the body and the click never reaches it.
  root.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!a) return;
    var u = new URL(a.getAttribute('href'), location.href);
    if (u.origin !== location.origin || u.pathname !== location.pathname || !u.hash) return;
    e.preventDefault();
    e.stopPropagation();
    if (location.hash !== u.hash) location.hash = u.hash; else apply();
  }, true);
  window.addEventListener('hashchange', apply);
  apply();
})();
</script>

</div>
