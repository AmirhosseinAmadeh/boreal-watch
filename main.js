/* SISTEM BOREAL YIS401GC — visual study. No dependencies.
   Geometry ratios (R = dial radius) were measured from the official product photo; see DESIGN-NOTES.md. */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const shortest = (from, to) => ((to - from + 540) % 360) - 180;
  const sinD = a => Math.sin(a * Math.PI / 180), cosD = a => Math.cos(a * Math.PI / 180);
  const P = (r, a) => [+(r * sinD(a)).toFixed(2), +(-r * cosD(a)).toFixed(2)];   // clock angle: 0 = 12 o'clock, clockwise

  /* ---------------- data: palette (sampled from the official photo) ---------------- */
  const GROUPS = [
    { fa: 'صفحه', en: 'Dial', items: [
      ['Dial · dark wedge', '#02103D', 'تیره‌ترین ناحیه‌ی خط‌های شعاعی', 'darkest brushed wedge'],
      ['Dial · median', '#05255A', 'میانه‌ی کل صفحه', 'median of the whole dial'],
      ['Dial · lit lobe', '#094782', 'ناحیه‌ی روشنِ زیر نور', 'the lit lobe'],
      ['Dial · outer band', '#063A6E', 'حلقه‌ی بیرونی کنار شیار', 'outer chapter band'],
      ['Printed lines', '#D3D9E4', 'خطوط و اعداد چاپی', 'printed lines and numerals'] ] },
    { fa: 'فلز', en: 'Metal', items: [
      ['Hands', '#BBBABC', 'عقربه‌ها (میانه)', 'hands (median)'],
      ['Hands · shadow', '#87878B', 'سایه‌ی وجه عقربه', 'hand facet shadow'],
      ['Hands · highlight', '#E7E6EA', 'برق وجه عقربه', 'hand facet highlight'],
      ['Fluted bezel', '#807E7F', 'حلقه‌ی شیاردار', 'fluted bezel'],
      ['Bezel groove', '#595758', 'شیار حلقه', 'bezel groove'],
      ['Case · polished', '#C4C5C1', 'بدنه‌ی صیقلی', 'polished case'],
      ['Case · highlight', '#EDEDEB', 'برق بدنه', 'case highlight'],
      ['Bracelet', '#B8B8B8', 'بند', 'bracelet'] ] },
    { fa: 'سیگنال', en: 'Signal', items: [
      ['Seconds hand', '#C81A35', 'ثانیه‌شمار', 'seconds hand'] ] },
    { fa: 'پشت‌بند باز', en: 'Openwork caseback', items: [
      ['Movement plate', '#A7AEB4', 'صفحه‌ی موتور', 'movement plate'],
      ['Gold gears', '#D9B866', 'چرخ‌دنده‌های طلایی', 'gold wheels'],
      ['Dark parts', '#3B3D3D', 'پیچ‌ها و قطعات تیره', 'screws and dark parts'] ] },
    { fa: 'رابط سایت رسمی', en: 'Official site UI', items: [
      ['Paper', '#FFFFFF', 'پس‌زمینه', 'background'],
      ['Ink', '#000000', 'متن و دکمه‌ها', 'text and buttons'] ] }
  ];

  /* ---------------- i18n ---------------- */
  const T = {
    fa: {
      nav_light: 'نور', nav_geo: 'هندسه', nav_pal: 'رنگ‌ها', nav_ana: 'کالبد', nav_mov: 'موتور', nav_spec: 'مشخصات',
      h1: 'آبی‌ای که با نور نفس می‌کشد',
      lead: 'صفحه‌ی آبی sun-brushed، هندسه‌ی قطب‌نما، بدنه و بند استیل صیقلی و یک عقربه‌ی ثانیه‌شمار قرمز.',
      cta: 'ببین چطور ساخته شده',
      hint: 'نشانگر را حرکت بده تا نور بچرخد · عقربه‌ها را بکش',
      k_light: '01 — نور', t_light: 'یک آبی، هزار زاویه',
      p_light: 'صفحه‌ی ساعت sun-brushed است: خطوط ریز شعاعی دارد و نور روی آن دو لکه‌ی روشن مقابل هم می‌سازد. بسته به زاویه از سرمه‌ای تقریباً سیاه تا آبی کبالتی دیده می‌شود، پس هویتش یک گرادیان است، نه یک HEX.',
      l_angle: 'زاویه‌ی نور', l_perceived: 'آبی دیده‌شده، سمت چپِ صفحه',
      k_geo: '02 — هندسه', t_geo: 'هندسه‌ی قطب‌نما روی صفحه',
      p_geo: 'روی صفحه فقط خطوط نازک سفید-آبی است: سه حلقه‌ی هم‌مرکز، یک ستاره‌ی شش‌پر (دو مثلث)، هشت پرتو دور مرکز و دو ردیف عدد. لایه‌ها را روشن و خاموش کن.',
      geo_note: 'شعاع‌ها نسبت به شعاع صفحه (R) از روی عکس رسمی اندازه‌گیری شده‌اند.',
      tg_rings: 'سه حلقه‌ی هم‌مرکز', tg_hex: 'ستاره‌ی شش‌پر', tg_rays: 'هشت پرتو', tg_hours: 'اعداد ساعت', tg_track: 'ردیف دقیقه', tg_hands: 'عقربه‌ها',
      k_pal: '03 — رنگ‌ها', t_pal: 'رنگ‌هایی که از عکس رسمی اندازه گرفتم',
      p_pal: 'این HEXها میانه‌ی پیکسل‌های همان ناحیه از عکس محصول‌اند، نه حدس. ترکیب سطح ساعت: حدود ۶۴٪ فلز، ۳۵٪ آبی و کمتر از ۱٪ قرمز؛ قرمز فقط خود عقربه‌ی ثانیه‌شمار است.',
      copyhint: 'برای کپی HEX کلیک کن', copied: 'کپی شد',
      k_ana: '04 — کالبد', t_ana: 'لایه به لایه', p_ana: 'با اسکرول، ساعت باز می‌شود.',
      c1: 'بدنه', c1d: 'استیل صیقلی', c2: 'حلقه‌ی شیاردار', c2d: 'لبه‌ی سکه‌ای (fluted) دور صفحه',
      c3: 'صفحه', c3d: 'آبی sun-brushed با خطوط قطب‌نما', c4: 'عقربه‌ها', c4d: 'استیل، وجه‌دار، با ثانیه‌شمار قرمز',
      c5: 'کریستال', c5d: 'شیشه‌ی شفاف روی صفحه',
      k_mov: '05 — موتور', t_mov: 'ساعت را برگردان',
      p_mov: 'پشت‌بند باز (openwork) است و موتور خودکوکِ SISTEM51 پشت شیشه دیده می‌شود.',
      f1: 'قطعه؛ تنها موتور دنیا با فقط ۵۱ قطعه و تولید کاملاً خودکار', f2: 'ذخیره‌ی انرژی', f3: 'مقاومت عالی در برابر میدان مغناطیسی (طبق متن رسمی)',
      k_cmp: '06 — قطب‌نما', t_cmp: 'شمال همیشه قرمز است',
      p_cmp: 'طراحی ساعت از قطب‌نمای دریایی الهام گرفته. روی خود ساعت تنها رنگ گرم، همین قرمز است. نشانگر را حرکت بده.',
      k_spec: '07 — مشخصات', t_spec: 'مشخصات ساعت',
      spec_note: '«رسمی» یعنی از صفحه‌ی محصول سواچ. «فهرست فروشگاه» یعنی از فهرست‌های خرده‌فروشی که با جست‌وجو پیدا شد و در صفحه‌ی رسمی نبود. «عکس» یعنی از روی تصویر رسمی.',
      foot: 'این صفحه یک مطالعه‌ی بصریِ غیررسمی است و ارتباطی با Swatch ندارد. تصویر ساعت از روی عکس رسمی، از نو با کد کشیده شده است.',
      foot_link: 'صفحه‌ی رسمی محصول ↗',
      title: 'SISTEM BOREAL YIS401GC — مطالعه‌ی ساعت',
      src: { official: 'رسمی', store: 'فهرست فروشگاه', photo: 'عکس' },
      specs: [
        ['مدل', 'SISTEM BOREAL · YIS401GC', 'official'], ['مجموعه', 'Core', 'official'],
        ['موتور', 'SISTEM51، مکانیکی خودکوک', 'official'], ['قطعات موتور', '۵۱', 'official'],
        ['ذخیره‌ی انرژی', '۹۰ ساعت', 'official'], ['ضدمغناطیس', 'مقاومت عالی (طبق متن رسمی)', 'official'],
        ['ساخت', 'سوئیس', 'official'], ['بدنه', 'استیل صیقلی', 'official'],
        ['بند', 'استیل صیقلی', 'official'], ['جنس قفل', 'استیل', 'official'], ['نوع قفل', 'پروانه‌ای (butterfly)', 'store'],
        ['پشت‌بند', 'باز (openwork)؛ موتور دیده می‌شود', 'official'],
        ['صفحه', 'آبی sun-brushed، طراحی الهام‌گرفته از قطب‌نمای دریایی', 'official'],
        ['تقویم', 'پنجره‌ی تاریخ در ساعت ۳', 'photo'], ['مقاومت در برابر آب', '3 bar', 'official'],
        ['قطر', '۴۲٫۰۰ mm', 'store'], ['ضخامت', '۱۳٫۸۰ mm', 'store'], ['فاصله‌ی شاخک‌ها', '۵۰٫۶۰ mm', 'store']
      ]
    },
    en: {
      nav_light: 'Light', nav_geo: 'Geometry', nav_pal: 'Colors', nav_ana: 'Anatomy', nav_mov: 'Movement', nav_spec: 'Specs',
      h1: 'A blue that breathes with the light',
      lead: 'A sun-brushed blue dial, compass geometry, a polished steel case and bracelet, and one red seconds hand.',
      cta: 'See how it is built',
      hint: 'Move the pointer to turn the light · drag the hands',
      k_light: '01 — Light', t_light: 'One blue, a thousand angles',
      p_light: 'The dial is sun-brushed: fine radial lines, and the light makes two bright lobes facing each other. Depending on the angle it reads from near-black navy to cobalt, so the identity is a gradient, not a HEX.',
      l_angle: 'Light angle', l_perceived: 'Perceived blue, left of the dial',
      k_geo: '02 — Geometry', t_geo: 'The compass geometry on the dial',
      p_geo: 'The dial carries only thin white-blue lines: three concentric rings, a six-point star (two triangles), eight rays around the centre and two rows of numerals. Toggle the layers.',
      geo_note: 'Radii are relative to the dial radius (R) and measured from the official photo.',
      tg_rings: 'Three concentric rings', tg_hex: 'Six-point star', tg_rays: 'Eight rays', tg_hours: 'Hour numerals', tg_track: 'Minute track', tg_hands: 'Hands',
      k_pal: '03 — Colors', t_pal: 'Colors measured from the official photo',
      p_pal: 'These HEX values are the median pixel of each region of the product photo, not guesses. Composition of the watch surface: about 64% metal, 35% blue and under 1% red; the red is only the seconds hand.',
      copyhint: 'Click to copy a HEX', copied: 'Copied',
      k_ana: '04 — Anatomy', t_ana: 'Layer by layer', p_ana: 'Scroll to open the watch.',
      c1: 'Case', c1d: 'Polished stainless steel', c2: 'Fluted bezel', c2d: 'A coin-edge ring around the dial',
      c3: 'Dial', c3d: 'Sun-brushed blue with compass lines', c4: 'Hands', c4d: 'Steel, faceted, with a red seconds hand',
      c5: 'Crystal', c5d: 'Clear glass over the dial',
      k_mov: '05 — Movement', t_mov: 'Turn the watch over',
      p_mov: 'The caseback is openwork, so the self-winding SISTEM51 movement shows through the glass.',
      f1: 'parts: the only movement in the world with just 51 parts and fully automated production', f2: 'power reserve', f3: 'exceptional anti-magnetic qualities (official wording)',
      k_cmp: '06 — Compass', t_cmp: 'North is always red',
      p_cmp: 'The design draws on the maritime compass. On the watch itself, the only warm colour is this red. Move the pointer.',
      k_spec: '07 — Specs', t_spec: 'Watch specifications',
      spec_note: '"Official" means from the Swatch product page. "Store listing" means from retailer listings found by search, not on the official page. "Photo" means read off the official image.',
      foot: 'This page is an unofficial visual study and is not affiliated with Swatch. The watch is redrawn in code from the official photo.',
      foot_link: 'Official product page ↗',
      title: 'SISTEM BOREAL YIS401GC — Watch study',
      src: { official: 'official', store: 'store listing', photo: 'photo' },
      specs: [
        ['Model', 'SISTEM BOREAL · YIS401GC', 'official'], ['Collection', 'Core', 'official'],
        ['Movement', 'SISTEM51, mechanical self-winding', 'official'], ['Movement parts', '51', 'official'],
        ['Power reserve', '90 hours', 'official'], ['Anti-magnetic', 'Exceptional (official wording)', 'official'],
        ['Made in', 'Switzerland', 'official'], ['Case', 'Polished stainless steel', 'official'],
        ['Bracelet', 'Polished stainless steel', 'official'], ['Clasp material', 'Stainless steel', 'official'], ['Clasp type', 'Butterfly', 'store'],
        ['Caseback', 'Openwork; the movement is visible', 'official'],
        ['Dial', 'Sun-brushed blue, maritime compass-inspired design', 'official'],
        ['Date', 'Date window at 3 o’clock', 'photo'], ['Water resistance', '3 bar', 'official'],
        ['Diameter', '42.00 mm', 'store'], ['Thickness', '13.80 mm', 'store'], ['Lug-to-lug', '50.60 mm', 'store']
      ]
    }
  };
  let lang = 'fa';
  const toastEl = $('#toast');
  let toastTimer;
  const toast = msg => { toastEl.textContent = msg; toastEl.classList.add('on'); clearTimeout(toastTimer); toastTimer = setTimeout(() => toastEl.classList.remove('on'), 1600); };
  const copy = async hex => { try { await navigator.clipboard.writeText(hex); } catch (_) { /* clipboard may be blocked */ } toast(`${T[lang].copied} ${hex}`); };

  function renderPalette() {
    $('#swatch-groups').innerHTML = GROUPS.map(g => `
      <div class="sw-group"><h3>${g[lang]}</h3><ul class="swatches">${g.items.map(([name, hex, rfa, ren]) => `
        <li><button class="sw" type="button" data-hex="${hex}" aria-label="${name} ${hex}">
          <span class="chipbig" style="background:${hex}"></span>
          <span class="meta"><b>${name}</b><span class="hex">${hex}</span><span class="role">${lang === 'fa' ? rfa : ren}</span></span>
        </button></li>`).join('')}</ul></div>`).join('');
    $$('.sw').forEach(b => b.addEventListener('click', () => copy(b.dataset.hex)));
  }
  function renderSpecs() {
    $('#spec-table').innerHTML = T[lang].specs.map(([k, v, s]) =>
      `<div><dt>${k}</dt><dd>${v}</dd><span class="src ${s === 'official' ? 'official' : ''}">${T[lang].src[s]}</span></div>`).join('');
  }
  function renderToggles() {
    const defs = [['rings', '0.22R · 0.53R · 0.73R'], ['hex', '0.77R'], ['rays', '0.24R – 0.36R'], ['hours', '0.63R'], ['track', '0.84R – 0.98R'], ['hands', '10:09:36']];
    const had = {};
    $$('#toggles input').forEach(i => had[i.dataset.k] = i.checked);
    $('#toggles').innerHTML = defs.map(([k, m]) => `<li><label data-k="${k}"><input type="checkbox" data-k="${k}" ${had[k] === false ? '' : 'checked'}><b>${T[lang]['tg_' + k]}</b><em>${m}</em></label></li>`).join('');
    $$('#toggles label').forEach(l => {
      const g = () => $(`#blueprint .g[data-k="${l.dataset.k}"]`);
      l.addEventListener('mouseenter', () => g() && g().classList.add('hl'));
      l.addEventListener('mouseleave', () => g() && g().classList.remove('hl'));
    });
    $$('#toggles input').forEach(i => i.addEventListener('change', () => {
      const g = $(`#blueprint .g[data-k="${i.dataset.k}"]`); if (g) g.classList.toggle('off', !i.checked);
    }));
  }
  function setLang(l) {
    lang = l;
    const d = document.documentElement;
    d.lang = l; d.dir = l === 'fa' ? 'rtl' : 'ltr';
    $$('[data-i18n]').forEach(e => { const v = T[l][e.dataset.i18n]; if (v) e.textContent = v; });
    $('[data-lang-label]').textContent = l === 'fa' ? 'EN' : 'FA';
    document.title = T[l].title;
    renderPalette(); renderSpecs(); renderToggles();
    try { localStorage.setItem('boreal-lang', l); } catch (_) { /* storage may be blocked */ }
  }
  $('#lang').addEventListener('click', () => setLang(lang === 'fa' ? 'en' : 'fa'));

  /* ---------------- dial geometry (R = 200 units; ratios measured from the photo) ---------------- */
  const LINE = '#D3D9E4';
  const G = { inner: 44.6, mid: 105.4, outer: 146, hexR: 154, hourR: 126, minR: 160, rayA: 48, rayB: 72 };
  const ringsMk = (cls = '') => [G.inner, G.mid, G.outer].map(r => `<circle class="${cls}" r="${r}" fill="none" stroke="${LINE}" stroke-width="1.1" stroke-opacity=".9"/>`).join('');
  const hexMk = (cls = '') => [[0, 120, 240], [60, 180, 300]].map(t => `<polygon class="${cls}" points="${t.map(a => P(G.hexR, a).join(',')).join(' ')}" fill="none" stroke="${LINE}" stroke-width="1" stroke-opacity=".8" stroke-linejoin="round"/>`).join('');
  const raysMk = (cls = '') => Array.from({ length: 8 }, (_, k) => { const a = k * 45, [x1, y1] = P(G.rayA, a), [x2, y2] = P(G.rayB, a); return `<line class="${cls}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${LINE}" stroke-width="1.7" stroke-linecap="round"/>`; }).join('');
  const hoursMk = () => {
    let s = '';
    for (let h = 1; h <= 12; h++) {
      if (h === 3) continue;
      const a = h * 30, [x, y] = P(G.hourR, a), rot = (h >= 4 && h <= 8) ? a - 180 : a;
      s += `<text class="d-num" transform="translate(${x} ${y}) rotate(${rot})">${h}</text>`;
    }
    return s;
  };
  const trackMk = (cls = '') => {
    let s = `<circle r="187" fill="none" stroke="#2A74C8" stroke-opacity=".13" stroke-width="26"/>`;
    for (let i = 0; i < 60; i++) {
      const big = i % 5 === 0, a = i * 6, [x1, y1] = P(196, a), [x2, y2] = P(big ? 177 : 188, a);
      s += `<line class="${cls}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${big ? '#CFE0F6' : LINE}" stroke-width="${big ? 3.4 : 1.1}" stroke-opacity="${big ? 1 : .85}"/>`;
    }
    for (let m = 0; m < 60; m += 5) {
      const a = m * 6, [x, y] = P(G.minR, a), lower = m >= 20 && m <= 40, rot = lower ? a - 180 : a;
      s += `<text class="d-min" transform="translate(${x} ${y}) rotate(${rot})">${m === 0 ? '60' : String(m).padStart(2, '0')}</text>`;
    }
    return s;
  };
  const handsMk = id => `
    <g class="w-shadow">
      <g class="h-h"><path d="M-8 24 L-7.5 -20 L-5 -118 L0 -132 L5 -118 L7.5 -20 L8 24Z" fill="url(#hl${id})" stroke="#fff" stroke-opacity=".5" stroke-width=".5"/></g>
      <g class="h-m"><path d="M-6.5 26 L-6 -20 L-4 -166 L0 -178 L4 -166 L6 -20 L6.5 26Z" fill="url(#hl${id})" stroke="#fff" stroke-opacity=".5" stroke-width=".5"/></g>
      <circle r="13" fill="url(#hl${id})" stroke="#fff" stroke-opacity=".5" stroke-width=".5"/>
      <g class="h-s"><line y1="70" y2="-196" stroke="#C81A35" stroke-width="3.2"/><circle r="10" fill="#C81A35"/><circle r="3.4" fill="#4A0A17"/></g>
    </g>`;
  const handDefs = id => `<linearGradient id="hl${id}" x1="0" x2="1"><stop offset="0" stop-color="#EDEDEF"/><stop offset=".5" stop-color="#C9C9CC"/><stop offset=".5" stop-color="#9A9A9F"/><stop offset="1" stop-color="#787880"/></linearGradient>`;
  const faceMk = (id, { hands = true } = {}) => `<defs>${handDefs(id)}</defs>
    ${trackMk()}${ringsMk()}${hexMk()}${raysMk()}${hoursMk()}
    <rect x="119" y="-16.5" width="42" height="33" rx="3" fill="#C9CDD3" stroke="#9AA0A8" stroke-width=".8"/>
    <rect x="121.5" y="-14" width="37" height="28" rx="2" fill="#fff"/><text class="d-date date-txt" x="140" y="1">${new Date().getDate()}</text>
    <text class="d-brand" y="-84">swatch</text><text class="d-swiss" y="-70">SWISS</text><text class="d-auto" y="92">AUTOMATIC</text>
    ${hands ? handsMk(id) : ''}`;

  /* ---------------- case, bracelet and caseback (SVG, metal gradients) ---------------- */
  function caseInner(id, { L, crownLeft = false }) {
    let links = '';
    for (const [x, w, y0] of [[-25, 50, 148], [-75, 48, 128], [27, 48, 128]]) {
      for (let y = y0; y < L; y += 40) {
        for (const s of [1, -1]) {
          const yy = s > 0 ? y : -y - 38;
          links += `<rect x="${x}" y="${yy}" width="${w}" height="38" rx="3" fill="url(#lg${id})" stroke="#fff" stroke-opacity=".75" stroke-width=".8"/>`
            + `<rect x="${x + 2}" y="${s > 0 ? yy + 1.5 : yy + 34.5}" width="${w - 4}" height="2" fill="#fff" fill-opacity=".7"/>`
            + `<rect x="${x + 2}" y="${s > 0 ? yy + 34.5 : yy + 1.5}" width="${w - 4}" height="2" fill="#000" fill-opacity=".18"/>`;
        }
      }
    }
    const stops = [[0, '#F4F5F6'], [.18, '#C9CBCD'], [.34, '#EEEFF0'], [.5, '#A8AAAD'], [.66, '#E6E7E8'], [.84, '#B6B8BB'], [1, '#F1F2F3']].map(([o, c]) => `<stop offset="${o}" stop-color="${c}"/>`).join('');
    const ridges = Array.from({ length: 5 }, (_, i) => `M${137 + i * 3} -14V14`).join('');
    return `<defs>
      <linearGradient id="cg${id}" class="cg" gradientUnits="userSpaceOnUse" x1="-134" y1="-134" x2="134" y2="134">${stops}</linearGradient>
      <linearGradient id="cf${id}" class="cg" gradientUnits="userSpaceOnUse" x1="-90" y1="-150" x2="90" y2="150"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".4" stop-color="#D9DBDD"/><stop offset=".7" stop-color="#F6F7F8"/><stop offset="1" stop-color="#BFC1C4"/></linearGradient>
      <linearGradient id="lg${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#EFF0F1"/><stop offset=".45" stop-color="#CBCCCE"/><stop offset=".9" stop-color="#A9ABAE"/><stop offset="1" stop-color="#D6D7D9"/></linearGradient>
      <linearGradient id="cr${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E6E7E9"/><stop offset=".5" stop-color="#9A9C9F"/><stop offset="1" stop-color="#D5D6D8"/></linearGradient></defs>
      ${links}
      <path d="M-80 -152 L80 -152 L97 -92 A134 134 0 0 1 97 92 L80 152 L-80 152 L-97 92 A134 134 0 0 1 -97 -92 Z" fill="url(#cg${id})" stroke="#5E6063" stroke-width="1"/>
      <path d="M-64 -104 L-56 -146 L56 -146 L64 -104 Z" fill="url(#cf${id})" stroke="#fff" stroke-opacity=".7" stroke-width=".8"/>
      <path d="M-64 104 L-56 146 L56 146 L64 104 Z" fill="url(#cf${id})" stroke="#fff" stroke-opacity=".7" stroke-width=".8"/>
      <circle r="124" fill="#2E3032" fill-opacity=".6"/><circle r="121.5" fill="none" stroke="#fff" stroke-opacity=".75"/>
      <g transform="${crownLeft ? 'scale(-1 1)' : ''}"><rect x="132" y="-15" width="17" height="30" rx="3" fill="url(#cr${id})" stroke="#6A6C6F" stroke-width=".8"/><path d="${ridges}" stroke="#000" stroke-opacity=".3" stroke-width="1"/></g>`;
  }
  const caseSvg = (id, { E, L, open = false }) => `<svg class="w-svg${open ? ' open' : ''}" viewBox="-150 ${-E} 300 ${2 * E}" aria-hidden="true">${caseInner(id, { L })}</svg>`;

  function movementMk() {
    let s = `<defs>
      <radialGradient id="plate" cx=".4" cy=".35" r=".85"><stop offset="0" stop-color="#C3CBD3"/><stop offset=".6" stop-color="#A7AEB4"/><stop offset="1" stop-color="#868B92"/></radialGradient>
      <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F1CB6B"/><stop offset=".5" stop-color="#D9B866"/><stop offset="1" stop-color="#B88A1E"/></linearGradient>
      <linearGradient id="gearS" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F1F2F3"/><stop offset=".5" stop-color="#B9BBBE"/><stop offset="1" stop-color="#E4E5E6"/></linearGradient>
      <clipPath id="win"><circle r="104"/></clipPath></defs>
      <g clip-path="url(#win)"><circle r="104" fill="url(#plate)"/>`;
    for (let k = 0; k < 36; k++) s += `<ellipse rx="100" ry="34" transform="rotate(${k * 5})" fill="none" stroke="#587099" stroke-opacity=".36" stroke-width=".6"/>`;
    for (let k = 0; k < 24; k++) s += `<ellipse rx="62" ry="21" transform="rotate(${k * 7.5 + 3})" fill="none" stroke="#fff" stroke-opacity=".22" stroke-width=".6"/>`;
    s += `<path d="M-64 -50 A82 82 0 0 1 22 -78" fill="none" stroke="url(#gold)" stroke-width="14"/>
      <path d="M-82 18 A84 84 0 0 0 -34 74" fill="none" stroke="url(#gold)" stroke-width="14"/>
      <g transform="translate(58 34)"><circle r="23" fill="none" stroke="url(#gold)" stroke-width="9"/><circle r="9" fill="#3B3D3D"/><path d="M-23 0H23M0 -23V23" stroke="url(#gold)" stroke-width="3"/></g>
      <g class="spin slow"><circle cx="-34" cy="-6" r="12" fill="none" stroke="#C9CBCE" stroke-width="3" stroke-dasharray="2.4 1.6"/><circle cx="-34" cy="-6" r="4" fill="#565454"/></g>
      <g class="spin"><circle r="31" fill="none" stroke="url(#gearS)" stroke-width="9" stroke-dasharray="3.1 2.3"/><circle r="25" fill="url(#gearS)"/><circle r="25" fill="none" stroke="#7A7C80" stroke-width=".8"/>
        <path d="M0 -25V25M-25 0H25M-18 -18L18 18M18 -18L-18 18" stroke="#8D8F93" stroke-width="1"/><circle r="8" fill="#565454"/><circle r="3" fill="#D9DBDD"/></g>
      <path d="M-18 12 L72 -52" stroke="#2B2D2E" stroke-width="1.5" stroke-linecap="round"/>`;
    for (const [x, y] of [[-70, -30], [60, -62], [-52, 66], [86, 8], [14, 84], [-12, -90]]) s += `<circle cx="${x}" cy="${y}" r="3.4" fill="#3B3D3D" stroke="#C9CBCE" stroke-width=".8"/>`;
    return s + '</g>';
  }
  function caseBackMk() {
    return `<svg id="caseback" viewBox="-150 -190 300 380" aria-hidden="true">${caseInner('bk', { L: 230, crownLeft: true })}
      <circle r="119" fill="url(#cf${'bk'})" stroke="#6F7174" stroke-width=".8"/><circle r="107" fill="none" stroke="#7B7D81" stroke-width="3"/>
      <path id="bkarc" d="M-113 0 A113 113 0 0 1 113 0" fill="none"/>
      <text font-family="Poppins,sans-serif" font-size="8" font-weight="600" letter-spacing="3" fill="#4A4C4F"><textPath href="#bkarc" startOffset="64%">SWISS</textPath></text>
      ${movementMk()}</svg>`;
  }

  /* ---------------- watch instances ---------------- */
  let uid = 0;
  const watches = [];
  function mountWatch(slot, { E = 190, L = 232, open = false, drag = false, live = true } = {}) {
    const id = ++uid;
    slot.innerHTML = `<div class="watch" role="img" aria-label="SISTEM BOREAL YIS401GC" style="--ar:300 / ${2 * E}">
      ${caseSvg(id, { E, L, open })}<div class="w-bezel"></div>
      <div class="w-dial"><svg class="w-face" viewBox="-200 -200 400 400" aria-hidden="true">${faceMk(id)}</svg></div><div class="w-crystal"></div></div>`;
    const el = slot.firstElementChild;
    const w = { el, offset: 0, live, h: $('.h-h', el), m: $('.h-m', el), s: $('.h-s', el), date: $('.date-txt', el), grads: $$('.cg', el) };
    if (drag) {
      const dial = $('.w-dial', el);
      dial.style.cursor = 'grab';
      const move = e => {
        const r = el.getBoundingClientRect();
        const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
        let a = Math.atan2(e.clientX - cx, -(e.clientY - cy)) * 180 / Math.PI;
        if (a < 0) a += 360;
        const d = new Date(Date.now() + w.offset);
        const cur = d.getMinutes() + d.getSeconds() / 60 + d.getMilliseconds() / 60000;
        w.offset += (((a / 6 - cur + 30) % 60 + 60) % 60 - 30) * 60000;
      };
      let down = false;
      dial.addEventListener('pointerdown', e => { down = true; dial.setPointerCapture(e.pointerId); dial.style.cursor = 'grabbing'; move(e); });
      dial.addEventListener('pointermove', e => { if (down) move(e); });
      const up = () => { down = false; dial.style.cursor = 'grab'; };
      dial.addEventListener('pointerup', up); dial.addEventListener('pointercancel', up);
      dial.addEventListener('dblclick', () => { w.offset = 0; });
    }
    watches.push(w);
    return w;
  }
  function setHands(w, ms) {
    const d = new Date(ms);
    const s = reduce ? d.getSeconds() : d.getSeconds() + d.getMilliseconds() / 1000;
    const m = d.getMinutes() + s / 60, h = (d.getHours() % 12) + m / 60;
    w.s.setAttribute('transform', `rotate(${(s * 6).toFixed(2)})`);
    w.m.setAttribute('transform', `rotate(${(m * 6).toFixed(2)})`);
    w.h.setAttribute('transform', `rotate(${(h * 30).toFixed(2)})`);
    const dd = String(d.getDate());
    if (w.date && w.date.textContent !== dd) w.date.textContent = dd;
  }
  const setMetalLight = (w, deg) => w.grads.forEach(g => g.setAttribute('gradientTransform', `rotate(${deg.toFixed(1)})`));

  const hero = $('#hero');
  const heroW = mountWatch($('#watch-hero'), { E: 260, L: 480, open: true, drag: true });
  const lightW = mountWatch($('#watch-light'), { E: 190 });
  mountWatch($('#watch-flip'), { E: 190 });
  { const el = $('.watch', $('#watch-flip')); el.style.setProperty('--la', '40deg'); }
  $('#caseback').outerHTML = caseBackMk();

  /* ---------------- hero background: the dial geometry, enlarged ---------------- */
  $('#hero-lines').innerHTML = `<g transform="scale(2)" stroke-opacity=".5" fill="none">${ringsMk()}${hexMk()}${raysMk()}</g>`;

  /* ---------------- exploded anatomy layers ---------------- */
  $('#ex-dial').innerHTML = `<svg viewBox="-200 -200 400 400">${faceMk('ed', { hands: false })}</svg>`;
  $('#static-hands').innerHTML = `<svg viewBox="-200 -200 400 400"><defs>${handDefs('sx')}</defs>${handsMk('sx')}</svg>`;
  { const g = $('#static-hands'); $('.h-h', g).setAttribute('transform', 'rotate(305.3)'); $('.h-m', g).setAttribute('transform', 'rotate(57.6)'); $('.h-s', g).setAttribute('transform', 'rotate(216)'); }

  /* ---------------- blueprint (geometry lab) ---------------- */
  (() => {
    const bp = $('#blueprint');
    const grp = (k, inner) => `<g class="g" data-k="${k}" style="--len:1200">${inner}</g>`;
    bp.innerHTML = `<defs>${handDefs('bp')}</defs>`
      + grp('track', trackMk('draw')) + grp('rings', ringsMk('draw')) + grp('hex', hexMk('draw')) + grp('rays', raysMk('draw')) + grp('hours', hoursMk())
      + grp('hands', handsMk('bp'));
    $('.h-h', bp).setAttribute('transform', 'rotate(305.3)'); $('.h-m', bp).setAttribute('transform', 'rotate(57.6)'); $('.h-s', bp).setAttribute('transform', 'rotate(216)');
  })();

  /* ---------------- light lab ---------------- */
  const mix = (a, b, t) => {
    const p = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
    const A = p(a), B = p(b);
    return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, '0')).join('').toUpperCase();
  };
  // two opposite lobes: brightness on the left of the dial (screen angle 180deg) as the light turns
  const perceived = la => {
    const k = (1 + Math.cos(2 * (180 - la) * Math.PI / 180)) / 2;
    return k < .5 ? mix('#02103D', '#05255A', k * 2) : mix('#05255A', '#094782', (k - .5) * 2);
  };
  const angle = $('#angle');
  const setLight = deg => {
    lightW.el.style.setProperty('--la', deg + 'deg');
    setMetalLight(lightW, deg);
    $('#angle-out').textContent = Math.round(deg) + '°';
    const hex = perceived(deg);
    $('#chip').style.background = hex; $('#chip-hex').textContent = hex;
  };
  angle.addEventListener('input', () => setLight(+angle.value));
  setLight(+angle.value);

  /* ---------------- compass rose ---------------- */
  const rose = $('#rose');
  (() => {
    let s = '<defs><linearGradient id="needleS" x1="0" x2="1"><stop offset="0" stop-color="#87878B"/><stop offset=".5" stop-color="#E7E6EA"/><stop offset="1" stop-color="#87878B"/></linearGradient></defs>';
    s += `<circle r="204" fill="none" stroke="${LINE}" stroke-opacity=".4"/><circle r="120" fill="none" stroke="${LINE}" stroke-opacity=".16"/><circle r="62" fill="none" stroke="${LINE}" stroke-opacity=".16"/>`;
    s += `<path d="M-204 0H204M0 -204V204" stroke="${LINE}" stroke-opacity=".14"/>`;
    for (let a = 0; a < 360; a += 5) {
      const big = a % 30 === 0;
      s += `<line y1="-204" y2="${big ? -184 : -194}" transform="rotate(${a})" stroke="${LINE}" stroke-width="${big ? 2 : 1}" stroke-opacity="${big ? .95 : .55}"/>`;
    }
    [['N', 0], ['E', 90], ['S', 180], ['W', 270]].forEach(([t, a]) => {
      const [x, y] = P(160, a);
      s += `<text x="${x}" y="${y + 9}" text-anchor="middle" style="font:600 26px 'Barlow Condensed',sans-serif;letter-spacing:.08em" fill="#F2F6FB">${t}</text>`;
    });
    s += '<polygon points="0,-222 -7,-208 7,-208" fill="#C81A35"/>';
    s += '<g id="needle"><polygon points="0,-150 -15,0 15,0" fill="#C81A35"/><polygon points="0,150 -15,0 15,0" fill="url(#needleS)"/><circle r="11" fill="#E7E6EA" stroke="#fff" stroke-opacity=".6"/><circle r="4" fill="#02103D"/></g>';
    rose.innerHTML = s;
  })();
  const needle = $('#needle'), bearingOut = $('#bearing');
  let bearing = 0, bearingTarget = 0, lastPointer = -1e9;

  /* ---------------- pointer + animation loop ---------------- */
  let px = innerWidth / 2, py = innerHeight / 2;
  addEventListener('pointermove', e => { px = e.clientX; py = e.clientY; lastPointer = performance.now(); }, { passive: true });
  let la = 40, tx = 0, ty = 0;

  function frame(now) {
    const idle = now - lastPointer > 2600;
    const heroVisible = hero.getBoundingClientRect().bottom > 0;
    if (heroVisible) {
      const r = heroW.el.getBoundingClientRect();
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      const targetLa = idle ? 40 + 55 * Math.sin(now / 3600) : Math.atan2(py - cy, px - cx) * 180 / Math.PI + 90;
      if (!reduce) la += shortest(la, targetLa) * .07;
      const tTx = reduce || idle ? 0 : clamp(-(py / innerHeight - .5) * 10, -6, 6);
      const tTy = reduce || idle ? 0 : clamp((px / innerWidth - .5) * 12, -8, 8);
      tx += (tTx - tx) * .08; ty += (tTy - ty) * .08;
      hero.style.setProperty('--la', la.toFixed(2) + 'deg');
      heroW.el.style.setProperty('--tx', tx.toFixed(2) + 'deg');
      heroW.el.style.setProperty('--ty', ty.toFixed(2) + 'deg');
      setMetalLight(heroW, la);
    }
    watches.forEach(w => setHands(w, Date.now() + w.offset));
    const rr = rose.getBoundingClientRect();
    if (rr.bottom > 0 && rr.top < innerHeight) {
      if (idle || reduce) bearingTarget = reduce ? 0 : 24 * Math.sin(now / 1500);
      else bearingTarget = Math.atan2(px - (rr.left + rr.width / 2), -(py - (rr.top + rr.height / 2))) * 180 / Math.PI;
      bearing += shortest(bearing, bearingTarget) * .1;
      needle.setAttribute('transform', `rotate(${bearing.toFixed(2)})`);
      bearingOut.textContent = String(Math.round(((bearing % 360) + 360) % 360)).padStart(3, '0') + '°';
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  /* ---------------- scroll ---------------- */
  const arc = $('#chrono-arc'), tip = $('#chrono-tip');
  const ex = $('#explode'), exWrap = $('#anatomy'), mv = $('#move'), mvWrap = $('#movement');
  const navLinks = $$('.bar nav a');
  const secs = navLinks.map(a => $(a.getAttribute('href')));
  const progress = (wrap) => clamp(-wrap.getBoundingClientRect().top / Math.max(1, wrap.offsetHeight - innerHeight), 0, 1);
  function onScroll() {
    const doc = document.documentElement;
    const p = clamp(scrollY / Math.max(1, doc.scrollHeight - innerHeight), 0, 1);
    arc.style.strokeDashoffset = (150.8 * (1 - p)).toFixed(2);
    const a = p * 2 * Math.PI - Math.PI / 2;
    tip.setAttribute('cx', (24 * Math.cos(a)).toFixed(2)); tip.setAttribute('cy', (24 * Math.sin(a)).toFixed(2));
    ex.style.setProperty('--p', progress(exWrap).toFixed(4));
    mv.style.setProperty('--p', progress(mvWrap).toFixed(4));
    let cur = -1;
    secs.forEach((s, i) => { const b = s.getBoundingClientRect(); if (b.top < innerHeight * .45 && b.bottom > innerHeight * .45) cur = i; });
    navLinks.forEach((l, i) => l.classList.toggle('on', i === cur));
  }
  addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', onScroll);
  onScroll();

  /* reveal + draw-on for the blueprint */
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('in'); const bp = $('#blueprint', e.target); if (bp) bp.classList.add('in'); io.unobserve(e.target); }
  }), { threshold: .15 });
  $$('.reveal').forEach(el => io.observe(el));

  let saved = 'fa';
  try { saved = localStorage.getItem('boreal-lang') || 'fa'; } catch (_) { /* ignore */ }
  setLang(saved === 'en' ? 'en' : 'fa');
})();
