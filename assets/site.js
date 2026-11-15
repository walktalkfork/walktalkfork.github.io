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

// 言語化レポートの見本（2回目の見本 s2・s1）。
// スマホの幅（767px以下）では、JS が動くときだけ「進みたい方向」までを見せ（.is-folded）、「続きを読む」でその場に広げる。
// PCでは CSS が .is-folded を使わないので、いつも全文が見えている。JS が動かないときは、どの幅でも最初から全文。
// 広げるときは、同じページの中の view transition で紙が下へ伸びるように広げる（s1「持ち上がる動きだけ」）。
// 紙に名前（report-sheet）を付けてから広げ、終わったら名前を外す。html の .is-unfolding は、ページのほかの所を薄れさせないための印（style.css）。
// view transition に対応しないブラウザと、動きを減らす設定の人には、一瞬で広げる。広げたあとは、続きの最初の書き込みに移る
(function () {
  var sheet = document.querySelector('.report-sheet');
  if (!sheet) return;
  var btn = sheet.querySelector('.report-unfold .report-more-btn');
  var next = document.getElementById('report-more-at');
  if (!btn) return;
  sheet.classList.add('is-folded');
  var calm = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : { matches: true };

  function unfold() {
    sheet.classList.remove('is-folded');
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
