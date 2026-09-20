---
hide:
  - navigation
  - toc
render_macros: true
---

<div class="tp-landing" markdown>

<div class="tp-bar" hidden="hidden">
<a class="tp-back" href="#overview">← Overview</a>
<span class="tp-bar__note">Readings are real, captured off a board; controls refuse and say why; the console replays a recording. <a href="about/">What is and isn't real</a> · <a href="demo/fork/" target="_blank" rel="noopener">full size</a></span>
<nav class="tp-seg tp-panes" aria-label="Which interface">
<a href="#demo/stock" data-pane="stock">Stock firmware</a>
<a href="#demo/fork" data-pane="fork">This fork</a>
<a href="#demo/fleet" data-pane="fleet">The fleet</a>
</nav>
</div>

<section class="tp-view tp-view--home" markdown>

<section class="tp-screen tp-hero" data-screen="hero" markdown>

<div class="tp-hero__say" markdown>

# Flash it wrong and lose nothing

<p class="lede">Firmware for the Turing Pi 2 that boots a new image on trial and takes it back if the board does not come back right. Upstream stopped in February 2025.</p>

<div class="tp-actions"><a class="md-button md-button--primary" href="#demo/fork">Try it, live</a> <a class="md-button" href="guides/install/">Install it</a></div>

</div>

<figure class="tp-hero__show" markdown>
![The Firmware tab: the running slot, the image the board can fall back to, and when the gate last promoted one.](assets/captures/firmware.png)
</figure>

</section>

<section class="tp-screen tp-chapter" data-screen="rollback" markdown>

<div class="tp-chapter__say" markdown>
<span class="tp-eyebrow">Updates that undo themselves</span>

## A bad image takes itself back

<p>Upstream promotes a new image the moment it boots, which proves the kernel started and nothing else. Here it boots on trial and is kept only if the board comes back right. It has said no once, on purpose, to a tampered image — in about 35 seconds.</p>

<div class="tp-proof">
<div><b>{{ gate.promoted }}</b><span>updates taken on this board</span></div>
<div><b>{{ gate.rolled_back }}</b><span>rolled back by the board itself</span></div>
<div><b>{{ gate.rack_trips }}</b><span>trips to the rack</span></div>
</div>

<a class="tp-why" href="features/updates-that-undo-themselves/">How the gate decides →</a>
</div>

<figure class="tp-chapter__show" markdown>
![The board's own About tab, naming the firmware, daemon and interface it is running.](assets/captures/about.png)
<figcaption>Read off the board on {{ gate.as_of }}, not counted by hand.</figcaption>
</figure>

</section>

<section class="tp-screen tp-chapter tp-chapter--flip" data-screen="nodes" markdown>

<div class="tp-chapter__say" markdown>
<span class="tp-eyebrow">Update without touching your nodes</span>

## Patch the BMC, leave the cluster alone

<p>Upstream power-cycles all four compute modules to update the management computer beside them. This fork leaves their rails alone, so patching the board that manages your cluster does not take the cluster down.</p>

<div class="tp-proof">
<div><b>0</b><span>modules power-cycled by a BMC update</span></div>
<div><b>0</b><span>cluster nodes lost, measured</span></div>
<div><b>48 s</b><span>for the board itself to come back</span></div>
</div>

<a class="tp-why" href="features/update-without-touching-your-nodes/">What upstream does instead →</a>
</div>

<figure class="tp-chapter__show" markdown>
![The four compute modules, powered and counted in uptime, across a BMC upgrade.](assets/captures/nodes.png)
<figcaption>Every module exactly as it was, uptime unbroken.</figcaption>
</figure>

</section>

<section class="tp-screen tp-chapter" data-screen="fleet" markdown>

<div class="tp-chapter__say" markdown>
<span class="tp-eyebrow">One page over every board</span>

## Every board on one page, and none of them exposed

<p>A board that can reflash four computers should not face the internet. One page inside the cluster drives them all, with every control a board has, and it holds no credential of its own.</p>

<div class="tp-proof">
<div><b>1</b><span>hostname for the whole estate</span></div>
<div><b>9</b><span>tabs per board, the same ones the board serves</span></div>
<div><b>0</b><span>credentials held by the page</span></div>
</div>

<a class="tp-why" href="features/one-page-over-every-board/">Why a board is never exposed →</a>
</div>

<figure class="tp-chapter__show" markdown>
![Both boards on one page, each answering for itself.](assets/captures/fleet.png)
<figcaption>A board that is down costs you its card and nothing else.</figcaption>
</figure>

</section>

<section class="tp-screen tp-chapter tp-chapter--flip" data-screen="maintained" markdown>

<div class="tp-chapter__say" markdown>
<span class="tp-eyebrow">Fresh, and fixed</span>

## Software that is still maintained

<p>Upstream's last release was {{ platform.upstream_last_version }}, in February 2025, on a kernel that is not a longterm release and a Buildroot that is end of life. This fork tracks both, and has taken out six named faults — including the one that killed this board twice in a day.</p>

<div class="tp-proof">
<div><b>{{ platform.kernel.fork.split()[0] }}</b><span>kernel, against upstream's 6.8</span></div>
<div><b>{{ releases.total }}</b><span>releases across four components</span></div>
<div><b>{{ faults.count }}</b><span>faults still open, each with a ticket</span></div>
</div>

<a class="tp-why" href="reference/comparison/">Every row, with its measurement →</a>
</div>

<figure class="tp-chapter__show" markdown>
![The board's About tab: kernel, daemon, interface and firmware, each a version you can check against a release.](assets/captures/info.png)
<figcaption>What the board says it is running, every part of it checkable.</figcaption>
</figure>

</section>

<section class="tp-screen tp-chapter tp-chapter--news" data-screen="news" markdown>

<div class="tp-news" markdown>
<span class="tp-eyebrow">What's new</span>

## {{ releases.firmware.newest }} shipped, {{ roadmap.count }} things planned

<div class="tp-news__grid" markdown>

<div class="tp-news__col" markdown>
<b>Just shipped</b>
<p>{{ news_lede() }}</p>
<a href="news/">Everything that changed →</a> <a href="feed.xml">Follow by feed →</a>
</div>

<div class="tp-news__col" markdown>
<b>Decided by vote</b>
<p>{{ roadmap.count }} things are planned and {{ roadmap.votes }} votes have been cast. Leading: <b>{{ roadmap.top }}</b>.</p>
<a href="roadmap/">Vote on what comes next →</a> <a href="feedback/">Propose something →</a>
</div>

</div>
</div>

</section>

<section class="tp-screen tp-chapter tp-chapter--what" data-screen="what" markdown>

<!-- No `markdown` attribute: python-markdown wraps a raw block child in a
     <p>, and the anchor below then shrank to fit its contents -- 468px of a
     1368px row, with the paragraph beside a third of the screen of white. -->
<div class="tp-what-grid">

<a class="tp-what" href="https://turingpi.com/" rel="noopener">
<img src="assets/turing-pi-2-hand.jpg" alt="A hand placing a compute module onto a Turing Pi 2 board that already carries three">
<span class="tp-what__text"><b>What is a Turing Pi?</b><span class="tp-what__body"> A mini-ITX board carrying four compute modules — Raspberry Pi CM4, Turing RK1 or Nvidia Jetson — with their network switch, power, and a small management computer on the board itself. That computer, the BMC, is what this firmware runs on: it powers the modules, flashes them and hands you their consoles. Made by Turing Machines — </span><span class="tp-what__link">turingpi.com →</span></span>
</a>

<div class="tp-dest">
<a class="tp-dest__card" href="#demo/fork"><b>Live demo</b><span>Stock and this fork, side by side, answering from a real board's data.</span></a>
<a class="tp-dest__card" href="features/"><b>Features</b><span>{{ features.count }} of them, each with the measurement behind it.</span></a>
<a class="tp-dest__card" href="guides/"><b>Documentation</b><span>Install, upgrade, recover, monitor, and the full API.</span></a>
<a class="tp-dest__card" href="about/"><b>About</b><span>Why the fork exists, and what is still not fixed.</span></a>
</div>

</div>

</section>

</section>

<section class="tp-view tp-view--demo" hidden="hidden">
<div class="tp-stage">
<iframe data-pane="stock" data-src="demo/stock/" title="Stock Turing Pi 2 interface, demo" hidden="hidden"></iframe>
<iframe data-pane="fork" data-src="demo/fork/" title="This fork's interface, demo" hidden="hidden"></iframe>
<iframe data-pane="fleet" data-src="demo/fleet/" title="The fleet interface over every board, demo" hidden="hidden"></iframe>
</div>
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
    root.querySelector('.tp-bar').hidden = !demo;
    // The footer belongs to the page, not to the demo: a sitemap under a
    // framed interface puts a scrollbar on the one view whose whole job is
    // to be as large as the screen allows.
    document.body.classList.toggle('tp-demo-open', demo);
    root.querySelectorAll('.tp-panes a').forEach(function (a) {
      a.setAttribute('aria-current', a.dataset.pane === pane ? 'true' : 'false');
    });
    root.querySelectorAll('.tp-stage [data-pane]').forEach(function (el) {
      var on = el.dataset.pane === pane;
      el.hidden = !on;
      if (on && el.tagName === 'IFRAME' && !el.getAttribute('src')) el.setAttribute('src', el.dataset.src);
    });
    if (!demo && h === 'overview') window.scrollTo(0, 0);
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
