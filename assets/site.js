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

// 料金と約束：言語化レポートの見本（見本 c1）。
// JS が動くときだけ紙の上のほうに切り詰めて「見本の全文を読む」ボタンを出し、押すと全文を窓（dialog）に写して開く。
// JS が動かないときは、ボタンを出さず全文をそのまま見せる。dialog が使えない古いブラウザでは、その場で全文を広げる。
// 窓は Esc・「閉じる」・窓の外の暗い所を押すと閉じ、閉じるとボタンに戻る。
(function () {
  var sheet = document.querySelector('.report-sheet');
  var dlg = document.querySelector('.report-dialog');
  if (!sheet || !dlg) return;
  var more = sheet.querySelector('.report-more');
  var opener = sheet.querySelector('.report-more-btn');
  var slot = dlg.querySelector('.report-dialog-doc');
  sheet.classList.add('is-clipped');
  more.hidden = false;

  opener.addEventListener('click', function () {
    if (typeof dlg.showModal !== 'function') {
      sheet.classList.remove('is-clipped');
      more.hidden = true;
      return;
    }
    if (!slot.firstElementChild) slot.appendChild(sheet.querySelector('.report-doc').cloneNode(true));
    dlg.showModal();
    dlg.scrollTop = 0;
  });
  Array.prototype.forEach.call(dlg.querySelectorAll('.report-close'), function (b) {
    b.addEventListener('click', function () { dlg.close(); });
  });
  dlg.addEventListener('click', function (e) {
    if (e.target !== dlg) return;
    var r = dlg.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dlg.close();
  });
  dlg.addEventListener('close', function () { opener.focus(); });
})();
