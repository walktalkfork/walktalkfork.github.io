// サイト共通の小さなスクリプト（index.html で defer で読み込む）。
// サイトの JS はこのファイルにまとめる。

// data-play を付けた要素が画面に入ったら、一度だけ .play を付ける。
// 時間で動くアニメーションは style.css で .play が付いたときだけ再生する（prefers-reduced-motion: no-preference のときだけ）。
// .play が付かなくても（JS が動かない・古いブラウザ）、要素は最後の姿のまま全部見えている。
(function () {
  var els = document.querySelectorAll('[data-play]');
  if (!els.length || !('IntersectionObserver' in window)) return;
  // これから .play が付くことを CSS に知らせる（押す前の印を隠すのに使う）。IntersectionObserver が無いときは付けない
  document.documentElement.classList.add('js-play');
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.classList.add('play');
      io.unobserve(e.target);
    });
  }, { rootMargin: '0px 0px -10% 0px' });
  els.forEach(function (el) { io.observe(el); });
})();

// PCのヘッダーの目次：今読んでいるセクションの名前に aria-current を付け、下に緑の線を置く（見本 u3）。
// 画面の上から35%の高さに引いた細い帯に重なっているセクションを「今読んでいる」とみなす。
// 線はこのスクリプトが作るので、JS が動かないときは今までと同じ目次のまま。目次は画面幅960px以上でだけ出る。
(function () {
  var nav = document.querySelector('.header-nav');
  if (!nav || !('IntersectionObserver' in window)) return;
  var links = Array.prototype.slice.call(nav.querySelectorAll('a[href^="#"]'));
  var targets = links.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
  var mark = document.createElement('span');
  mark.className = 'nav-mark';
  mark.setAttribute('aria-hidden', 'true');
  nav.appendChild(mark);
  var current = null;

  function place(a, jump) {
    if (!a || !a.offsetWidth) { mark.style.opacity = '0'; return; }
    var t = 'translateX(' + a.offsetLeft + 'px) scaleX(' + a.offsetWidth + ')';
    if (jump || mark.style.opacity !== '1') {
      // 線が見えていなかったときや幅が変わったときは、横に動かさずその場に置く
      mark.classList.add('is-jump');
      mark.style.transform = t;
      void mark.offsetWidth;
      mark.classList.remove('is-jump');
    } else {
      mark.style.transform = t;
    }
    mark.style.opacity = '1';
  }
  function setCurrent(a) {
    if (a === current) return;
    links.forEach(function (x) {
      if (x === a) x.setAttribute('aria-current', 'location'); else x.removeAttribute('aria-current');
    });
    current = a;
    place(a, false);
  }

  var on = new Map();
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { on.set(e.target, e.isIntersecting); });
    var hit = null;
    for (var i = 0; i < links.length; i++) { if (targets[i] && on.get(targets[i])) { hit = links[i]; break; } }
    setCurrent(hit);
  }, { rootMargin: '-35% 0px -64% 0px', threshold: 0 });
  targets.forEach(function (t) { if (t) io.observe(t); });

  // 画面の幅や書体が変わったら（目次が出たときも）、線の位置を合わせ直す
  function refit() { place(current, true); }
  if ('ResizeObserver' in window) new ResizeObserver(refit).observe(nav);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(refit);
})();

// 言語化レポートの見本（2回目の見本 s2・s1、並べ方は 2026-11-16 の見本の案B）。
// スマホの幅（767px以下）では、JS が動くときだけ「進みたい方向」までと5の頭を見せ（.is-folded）、紙の中の「続きを読む」でその場に広げる。
// PCでは CSS が .is-folded を使わないので、いつも全文が見えている。JS が動かないときは、どの幅でも最初から全文。
// 広げるときは、同じページの中の view transition で紙が下へ伸びるように広げる（s1「持ち上がる動きだけ」）。
// 紙に名前（report-sheet）を付けてから広げ、終わったら名前を外す。html の .is-unfolding は、ページのほかの所を薄れさせないための印（style.css）。
// view transition に対応しないブラウザと、動きを減らす設定の人には、一瞬で広げる。広げたあとは、続きの最初の項目（5）に移る。
// 項目の一覧（.report-toc）で、たたんだ部分の項目（5・6）を押したときは、先に広げてからその項目へ移る。
// アドレスの # がたたむ部分の項目を指して開かれたときは、最初から広げておく
(function () {
  var sheet = document.querySelector('.report-sheet');
  if (!sheet) return;
  var btn = sheet.querySelector('.report-unfold .report-more-btn');
  if (!btn) return;
  var next = document.getElementById(btn.getAttribute('aria-controls'));
  var calm = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : { matches: true };
  // アドレスの # が指す要素。# が壊れていて読めない（#100% など）ときは何も指していないことにする
  function byHash() {
    try { return location.hash ? document.getElementById(decodeURIComponent(location.hash.slice(1))) : null; }
    catch (e) { return null; }
  }
  var hashed = byHash();
  if (hashed && sheet.contains(hashed) && hashed.closest('.report-rest')) return;
  sheet.classList.add('is-folded');

  function open() {
    sheet.classList.remove('is-folded');
    btn.setAttribute('aria-expanded', 'true');
  }
  function unfold() {
    open();
    if (next) next.focus({ preventScroll: true });
  }
  btn.addEventListener('click', function () {
    if (typeof document.startViewTransition !== 'function' || calm.matches) { unfold(); return; }
    var root = document.documentElement;
    sheet.style.viewTransitionName = 'report-sheet';
    root.classList.add('is-unfolding');
    var t = document.startViewTransition(unfold);
    t.ready.catch(function () {});
    var done = function () { sheet.style.viewTransitionName = ''; root.classList.remove('is-unfolding'); };
    t.finished.then(done, done);
    // 画面が描かれない状態（裏のタブなど）で広げる処理が始まらないときは、動きを飛ばしてその場で広げ、名前と印も外す。
    // 動きを飛ばしたあとは、遅れて広げる処理が動いても root の動き（ページの移動用）は再生されない。unfold() は2回動いても同じ
    setTimeout(function () {
      if (!sheet.classList.contains('is-folded')) return;
      if (typeof t.skipTransition === 'function') t.skipTransition();
      unfold();
      done();
    }, 1500);
  });

  // 項目の一覧：たたんだ部分の項目へのリンクだけ、広げてから移る（ほかの項目はふつうのページ内リンクのまま）。
  // 移る先は tabindex="-1" にして、キーボードで読む人の次の Tab がその項目から続くようにする
  document.querySelectorAll('.report-toc a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (ev) {
      var t = document.getElementById(a.getAttribute('href').slice(1));
      if (!t || !sheet.classList.contains('is-folded') || !t.closest('.report-rest')) return;
      ev.preventDefault();
      open();
      if (!t.hasAttribute('tabindex')) t.setAttribute('tabindex', '-1');
      if (history.pushState) history.pushState(null, '', '#' + t.id);
      t.scrollIntoView({ behavior: calm.matches ? 'auto' : 'smooth', block: 'start' });
      t.focus({ preventScroll: true });
    });
  });
  // ほかの所のリンクで # がたたんだ部分の項目に変わったときも、広げてからそこへ移る
  window.addEventListener('hashchange', function () {
    var t = byHash();
    if (!t || !sheet.classList.contains('is-folded') || !sheet.contains(t) || !t.closest('.report-rest')) return;
    open();
    t.scrollIntoView({ block: 'start' });
  });
})();

// 印刷：印刷の前によくある質問をすべて開き、終わったら元に戻す（見本 b4）。
// name="faq"（1つ開くとほかが閉じる）があると1つしか開けないので、印刷の間だけ外す。もともと開いていた質問はそのままにする
(function () {
  window.addEventListener('beforeprint', function () {
    document.querySelectorAll('.faq details:not([open])').forEach(function (d) {
      d.setAttribute('data-print', d.getAttribute('name') || '');
      d.removeAttribute('name');
      d.open = true;
    });
  });
  window.addEventListener('afterprint', function () {
    document.querySelectorAll('.faq details[data-print]').forEach(function (d) {
      d.open = false;
      if (d.getAttribute('data-print')) d.setAttribute('name', d.getAttribute('data-print'));
      d.removeAttribute('data-print');
    });
  });
})();

// 最後の予約欄（2026-11-16 見本の案A「地図の終点」）：白い点が道を歩き、歩いた所が実線になる。
// ボタンの真上の目的地に着くと輪が一度だけ広がり、約5秒休んでから点と線が薄れ、また最初から歩く（1回に18秒）。
// 帯に .play が付いてから（[data-play]）、道が画面に見えている間だけ動かす。画面の外・別のタブにいる間は止める。
// 動きを減らす設定のときと JS が動かないときは、道が全部引かれた形で止まっている（点は出さない）
(function () {
  var band = document.querySelector('.closing');
  var map = band && band.querySelector('.closing-map');
  if (!map || !('IntersectionObserver' in window)) return;
  var plan = map.querySelector('.closing-plan');
  var trail = map.querySelector('.closing-trail');
  var walker = map.querySelector('.closing-walker');
  if (!plan || !trail || !walker || !plan.getTotalLength) return;
  var still = window.matchMedia('(prefers-reduced-motion: reduce)');
  var WALK = 18000, REST = 5200, FADE = 1400, CYCLE = WALK + REST + FADE;
  var HOME = walker.getAttribute('transform');
  var L = 0, raf = 0, running = false, t0 = 0, elapsed = 0, arrived = false, visible = false;

  function ease(x) { return (1 - Math.cos(Math.PI * x)) / 2; }
  function place(p) {
    var q = plan.getPointAtLength(p * L);
    walker.setAttribute('transform', 'translate(' + q.x.toFixed(1) + ' ' + q.y.toFixed(1) + ')');
    trail.style.strokeDashoffset = (1 - p).toFixed(4);
    trail.style.opacity = p < 0.004 ? '0' : '';
  }
  function frame(now) {
    raf = 0;
    if (!running) return;
    elapsed = now - t0;
    var t = elapsed % CYCLE;
    if (t < WALK) {
      if (arrived) { arrived = false; map.classList.remove('is-arrived', 'is-fading'); }
      place(ease(t / WALK));
    } else if (t < WALK + REST) {
      if (!arrived) { arrived = true; place(1); map.classList.add('is-arrived'); }
    } else {
      map.classList.add('is-fading');
    }
    raf = requestAnimationFrame(frame);
  }
  function run() {
    if (running) return;
    if (!L) L = plan.getTotalLength();
    running = true;
    map.classList.add('is-walking');
    raf = requestAnimationFrame(function (now) { t0 = now - elapsed; frame(now); });
  }
  function pause() { running = false; if (raf) cancelAnimationFrame(raf); raf = 0; }
  function reset() {
    pause(); elapsed = 0; arrived = false;
    map.classList.remove('is-walking', 'is-arrived', 'is-fading');
    trail.style.strokeDashoffset = ''; trail.style.opacity = '';
    walker.setAttribute('transform', HOME);
  }
  function update() {
    if (still.matches) { reset(); return; }
    if (band.classList.contains('play') && visible && !document.hidden) run(); else pause();
  }
  new IntersectionObserver(function (entries) {
    visible = entries[entries.length - 1].isIntersecting;
    update();
  }).observe(map);
  new MutationObserver(update).observe(band, { attributes: true, attributeFilter: ['class'] });
  document.addEventListener('visibilitychange', update);
  if (still.addEventListener) still.addEventListener('change', update); else if (still.addListener) still.addListener(update);
})();

// index.html のフッター（2026-11-16 見本の案E「名前で終わる」）：マウスに近い字ほど起き上がる（style.css の .mark-ch が --lift を使う）。
// マウスのある端末で、フッターが画面に見えていて、動きを減らす設定でないときだけ。字の位置はマウスが入ったときと幅が変わったときに測り直す
(function () {
  var foot = document.querySelector('.site-footer.is-band');
  if (!foot || !('IntersectionObserver' in window)) return;
  var chars = foot.querySelectorAll('.mark-ch');
  if (!chars.length) return;
  var fine = window.matchMedia('(hover: hover) and (pointer: fine)');
  var still = window.matchMedia('(prefers-reduced-motion: reduce)');
  var cx = [], cur = [], tx = 0, fy = 0, active = false, visible = false, raf = 0, sigma = 60;

  function clamp(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }
  function on() { return visible && fine.matches && !still.matches; }
  function measure() {
    var r = foot.getBoundingClientRect();
    sigma = Math.max(40, r.width * .075);
    chars.forEach(function (c, i) {
      var q = c.getBoundingClientRect();
      cx[i] = q.left - r.left + q.width / 2;
    });
  }
  function frame() {
    raf = 0;
    var moving = false, live = on();
    chars.forEach(function (c, i) {
      var d = live && active && cx.length ? (tx - cx[i]) / sigma : Infinity;
      var g = d === Infinity ? 0 : Math.exp(-d * d) * (.3 + .7 * fy);
      cur[i] = (cur[i] || 0) + (g - (cur[i] || 0)) * .12;
      if (Math.abs(g - cur[i]) > .002) moving = true; else cur[i] = g;
      if (cur[i]) c.style.setProperty('--lift', cur[i].toFixed(3)); else c.style.removeProperty('--lift');
    });
    if (moving) raf = requestAnimationFrame(frame);
  }
  function kick() { if (!raf) raf = requestAnimationFrame(frame); }
  function settle() { active = false; kick(); }

  foot.addEventListener('pointerenter', function () { if (on()) measure(); });
  foot.addEventListener('pointermove', function (e) {
    if (!on() || (e.pointerType && e.pointerType !== 'mouse' && e.pointerType !== 'pen')) return;
    if (!cx.length) measure();
    var r = foot.getBoundingClientRect();
    tx = e.clientX - r.left;
    fy = clamp((e.clientY - r.top) / (r.height || 1));
    active = true; kick();
  }, { passive: true });
  foot.addEventListener('pointerleave', settle);
  window.addEventListener('resize', function () { cx = []; });
  new IntersectionObserver(function (entries) {
    visible = entries[entries.length - 1].isIntersecting;
    if (!visible) settle();
  }).observe(foot);
  [fine, still].forEach(function (m) {
    if (m.addEventListener) m.addEventListener('change', settle); else if (m.addListener) m.addListener(settle);
  });
})();
