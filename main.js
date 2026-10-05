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
      ['Printed lines (core)', '#ECEBEB', 'هسته‌ی خطوط و اعداد چاپی، بدون لبه‌ی نرم‌شده', 'core of lines and numerals, without anti-aliased edges'],
      ['Outer ticks', '#D9E8F4', 'خط‌های آبی‌روشنِ حلقه‌ی بیرونی', 'pale-blue ticks on the chapter band'] ] },
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
      ['Seconds hand', '#D5051F', 'ثانیه‌شمار (هسته‌ی رنگ)', 'seconds hand (core colour)'] ] },
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
      nav_light: 'نور', nav_geo: 'هندسه', nav_pal: 'رنگ‌ها', nav_ana: 'کالبد', nav_mov: 'موتور', nav_spec: 'مشخصات', nav_lab: 'لبه‌یابی',
      k_lab: '08 — لبه‌یابی', t_lab: 'از عکس تا کد، مرحله به مرحله',
      p_lab: 'این ساعت با لبه‌یابی روی عکس رسمی بازسازی شده است. هر مرحله را انتخاب کن: چه کاری می‌کند، چه عددی اندازه می‌گیرد، و خروجی‌اش را روی همین ساعتِ برداری ببین. (عکس خام در مخزن نیست؛ فقط کد و خروجی برداری.)',
      l_tones: 'سطح‌های تن', lab_file: 'فایل', lab_note: 'بازسازی‌شده یعنی بخشی که در عکس زیر عقربه پنهان بود و از روی حروف هم‌خانواده کامل شد؛ اندازه‌گیری نیست.',
      h1: 'آبی‌ای که با نور نفس می‌کشد',
      lead: 'صفحه‌ی آبی sun-brushed، هندسه‌ی قطب‌نما، بدنه و بند استیل صیقلی و یک عقربه‌ی ثانیه‌شمار قرمز.',
      cta: 'ببین چطور ساخته شده',
      hint: 'نشانگر را حرکت بده تا نور بچرخد · عقربه‌ها را بکش',
      k_light: '01 — نور', t_light: 'یک آبی، هزار زاویه',
      p_light: 'صفحه‌ی ساعت sun-brushed است: خطوط ریز شعاعی دارد و نور روی آن دو لکه‌ی روشن مقابل هم می‌سازد. بسته به زاویه از سرمه‌ای تقریباً سیاه تا آبی کبالتی دیده می‌شود، پس هویتش یک گرادیان است، نه یک HEX.',
      l_angle: 'زاویه‌ی نور', l_perceived: 'آبی دیده‌شده، سمت چپِ صفحه',
      k_geo: '02 — هندسه', t_geo: 'هندسه‌ی قطب‌نما روی صفحه',
      p_geo: 'این هندسه از لبه‌یابی روی عکس رسمی بیرون آمده، نه از حدس: سه حلقه‌ی هم‌مرکز، شش وتر روی حلقه‌ی بیرونی (چهار خط با شیب ۲۶٫۶° و دو قطر ۴۵°) که در رأسِ بالا به یک مثلث توپُر می‌رسند، دوازده پرتو (نه هشت!) دور مرکز، دو ردیف خطِ دقیقه و دو ردیف عدد. لایه‌ها را روشن و خاموش کن.',
      geo_note: 'شعاع‌ها نسبت به شعاع صفحه (R) از روی عکس رسمی اندازه‌گیری شده‌اند.',
      tg_rings: 'سه حلقه‌ی هم‌مرکز', tg_chords: 'شش وتر و مثلث رأس', tg_rays: 'دوازده پرتو', tg_hours: 'اعداد ساعت', tg_track: 'ردیف دقیقه (۲×۶۰ خط + برچسب)', tg_brand: 'آرم، AUTOMATIC و تقویم', tg_hands: 'عقربه‌ها',
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
      nav_light: 'Light', nav_geo: 'Geometry', nav_pal: 'Colors', nav_ana: 'Anatomy', nav_mov: 'Movement', nav_spec: 'Specs', nav_lab: 'Edge lab',
      k_lab: '08 — Edge lab', t_lab: 'From photo to code, stage by stage',
      p_lab: 'This watch was rebuilt by edge detection on the official photo. Pick a stage: what it does, which numbers it measures, and its output drawn on this vector watch. (The raw photo is not in the repository, only the code and the vector output.)',
      l_tones: 'Tone levels', lab_file: 'File', lab_note: 'Reconstructed means a part that was hidden under a hand in the photo and completed from sibling glyphs; it is not a measurement.',
      h1: 'A blue that breathes with the light',
      lead: 'A sun-brushed blue dial, compass geometry, a polished steel case and bracelet, and one red seconds hand.',
      cta: 'See how it is built',
      hint: 'Move the pointer to turn the light · drag the hands',
      k_light: '01 — Light', t_light: 'One blue, a thousand angles',
      p_light: 'The dial is sun-brushed: fine radial lines, and the light makes two bright lobes facing each other. Depending on the angle it reads from near-black navy to cobalt, so the identity is a gradient, not a HEX.',
      l_angle: 'Light angle', l_perceived: 'Perceived blue, left of the dial',
      k_geo: '02 — Geometry', t_geo: 'The compass geometry on the dial',
      p_geo: 'This geometry comes from edge detection on the official photo, not from guesses: three concentric rings, six chords of the outer ring (four at 26.6 deg, two diagonals at 45 deg) meeting in a solid triangle at the top, twelve rays (not eight) around the centre, two rows of minute ticks and two rows of numerals. Toggle the layers.',
      geo_note: 'Radii are relative to the dial radius (R) and measured from the official photo.',
      tg_rings: 'Three concentric rings', tg_chords: 'Six chords + apex triangle', tg_rays: 'Twelve rays', tg_hours: 'Hour numerals', tg_track: 'Minute track (2 x 60 ticks + labels)', tg_brand: 'Logo, AUTOMATIC, date', tg_hands: 'Hands',
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
  let labReady = false;
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
    const defs = [['rings', '0.219R · 0.518R · 0.716R'], ['chords', '26.6° ×4 · 45° ×2'], ['rays', '12 × 30° · 0.21R–0.33R'], ['hours', '0.62R'], ['track', '0.93R–0.98R · 0.71R–0.78R'], ['brand', 'swatch · AUTOMATIC · 28'], ['hands', '10:10:00']];
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
    renderPalette(); renderSpecs(); renderToggles(); if (labReady) renderLab();
    try { localStorage.setItem('boreal-lang', l); } catch (_) { /* storage may be blocked */ }
  }
  $('#lang').addEventListener('click', () => setLang(lang === 'fa' ? 'en' : 'fa'));

  /* ---------------- the watch, rebuilt from the extracted data (assets/boreal-data.js + boreal-body.js) ----------------
     Everything below is drawn from numbers the edge-detection pipeline measured on the official photo (see PIPELINE.md).
     Dial units: origin = dial centre, 200 = dial radius, y down, clock angle 0 = 12 o'clock. */
  const B = window.BOREAL, DL = B.dial, HD = B.hands, BZ = B.bezel, SH = B.shading, BODY = B.body;
  const INK = DL.ink;
  const POSE = { hour: HD.hour.angle_photo, minute: HD.minute.angle_photo, second: 0.23 };
  const hexRgb = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
  const rgbHex = a => '#' + a.map(v => clamp(Math.round(v), 0, 255).toString(16).padStart(2, '0')).join('').toUpperCase();
  const UB = BODY.unit_bbox, PAD = 6;
  const VX = UB[0] - PAD, VW = UB[2] - UB[0] + 2 * PAD;        // viewBox x / width of the whole watch
  const BODY_SCALE = (1 / B.unit.px_per_unit) / BODY.grid_per_px;
  const wedge = (r0, r1, a0, a1) => {
    const [x0, y0] = P(r0, a0), [x1, y1] = P(r1, a0), [x2, y2] = P(r1, a1), [x3, y3] = P(r0, a1);
    return `M${x0} ${y0}L${x1} ${y1}A${r1} ${r1} 0 0 1 ${x2} ${y2}L${x3} ${y3}A${r0} ${r0} 0 0 0 ${x0} ${y0}Z`;
  };

  /* --- printed layers --- */
  const ringsMk = (cls = '') => DL.rings.map(r => `<circle class="${cls}" r="${r.r}" fill="none" stroke="${INK}" stroke-width="${r.w}"/>`).join('');
  const ticksMk = (cls = '') => Object.values(DL.tick_rows).map(row => Array.from({ length: 60 }, (_, k) => {
    const c = k % 5 ? row.one : row.five, a = 6 * k + row.offset_deg, [x0, y0] = P(c.r0, a), [x1, y1] = P(c.r1, a);
    return `<line class="${cls}" x1="${x0}" y1="${y0}" x2="${x1}" y2="${y1}" stroke="${k % 5 ? row.colour_one : row.colour}" stroke-width="${c.w}"/>`;
  }).join('')).join('');
  const raysMk = () => {
    const R = DL.rays;
    return R.angles.map(a => {
      const c = cosD(a), s = sinD(a), q = (r, w, sd) => { const [x, y] = P(r, a); return `${f2(x + sd * w / 2 * c)} ${f2(y + sd * w / 2 * s)}`; };
      return `<path d="M${q(R.r0, R.w0, -1)}L${q(R.r1, R.w1, -1)}L${q(R.r1, R.w1, 1)}L${q(R.r0, R.w0, 1)}Z" fill="${INK}"/>`;
    }).join('');
  };
  const f2 = v => +(+v).toFixed(2);
  const chordsMk = (cls = '') => DL.chords.map(c => `<line class="${cls}" x1="${c.a[0]}" y1="${c.a[1]}" x2="${c.b[0]}" y2="${c.b[1]}" stroke="${INK}" stroke-width="${c.w}"/>`).join('')
    + (DL.apex ? `<path d="M${DL.apex.points.map(p => p.join(' ')).join('L')}Z" fill="${INK}"/>` : '');
  const textMk = kinds => DL.text.filter(t => kinds.includes(t.kind)).map(t =>
    `<path class="glyph" d="${t.d}" fill="${t.fill}" fill-rule="evenodd" transform="translate(${t.x} ${t.y}) rotate(${t.rot})"/>`).join('');
  const dateMk = () => {
    const W = DL.date, r = W.rim;
    return `<g class="date"><rect x="${f2(W.x + r / 2)}" y="${f2(W.y + r / 2)}" width="${f2(W.w - r)}" height="${f2(W.h - r)}" rx="${W.radius}" fill="url(#datePlate)" stroke="${W.rim_colour}" stroke-width="${r}"/>
      <rect x="${f2(W.x + r)}" y="${f2(W.y + r)}" width="${f2(W.w - 2 * r)}" height="${f2(W.h - 2 * r)}" rx="${f2(W.radius * .55)}" fill="none" stroke="${W.edge_colour}" stroke-width=".7" stroke-opacity=".8"/>
      <text class="date-txt" style="direction:ltr;unicode-bidi:bidi-override" y="${f2(W.digit_cy + W.digit_h / 2)}" font-family="Poppins,Arial,sans-serif" font-weight="600" font-size="${f2(W.digit_h / .71)}" fill="${W.digit_colour}" lengthAdjust="spacingAndGlyphs"></text></g>`;
  };
  const dateDefs = () => { const W = DL.date; return `<radialGradient id="datePlate" cx=".5" cy=".5" r=".75"><stop offset="0" stop-color="${W.plate_centre}"/><stop offset="1" stop-color="${W.plate_edge}"/></radialGradient>`; };
  const setDate = (el, day) => {
    const W = DL.date, s = String(day), len = s.length * W.digit_w + (s.length - 1) * W.digit_gap;
    el.textContent = s; el.setAttribute('x', f2(W.digit_cx - len / 2)); el.setAttribute('textLength', f2(len));
  };

  /* --- hands: two facets per hand (left / right of the axis) with the measured lengthwise colour ramps --- */
  const FM = HD.facet_model;
  const facetF = ang => FM.m + FM.a * cosD(ang - FM.theta0);
  const facetFactor = (hand, ang, side) => {
    const meas = HD[hand].angle_photo;
    return clamp(side === 'l' ? facetF(ang) / facetF(meas) : facetF(-ang) / facetF(-meas), .55, 1.4);
  };
  const rampStops = (h, cols) => {
    const y1 = -h.length, y2 = h.tail;
    return h.stations.map((s, i) => `<stop offset="${f2((-s - y1) / (y2 - y1) * 100)}%" stop-color="${cols[i]}"/>`).join('');
  };
  const handDefs = id => ['hour', 'minute'].map(k => {
    const h = HD[k], y1 = -h.length, y2 = h.tail;
    return ['l', 'r'].map(s => `<linearGradient id="h${s}${k[0]}${id}" gradientUnits="userSpaceOnUse" x1="0" y1="${y1}" x2="0" y2="${y2}">${rampStops(h, s === 'l' ? h.left : h.right)}</linearGradient>`).join('');
  }).join('') + `<radialGradient id="hubpad${id}"><stop offset="0" stop-color="#9B9899"/><stop offset=".6" stop-color="#6E6A6D"/><stop offset="1" stop-color="#3A383A"/></radialGradient>`;
  const handMk = (k, id) => {
    const h = HD[k], [tl, tr, br, bl] = h.polygon;
    return `<g class="h-${k[0]}" data-hand="${k}"><path class="fl" d="M${tl[0]} ${tl[1]}L0 ${tl[1]}L0 ${bl[1]}L${bl[0]} ${bl[1]}Z" fill="url(#hl${k[0]}${id})"/>
      <path class="fr" d="M0 ${tr[1]}L${tr[0]} ${tr[1]}L${br[0]} ${br[1]}L0 ${br[1]}Z" fill="url(#hr${k[0]}${id})"/></g>`;
  };
  const handsMk = id => {
    const S = HD.second, H = HD.hub;
    return `<g class="w-shadow">${handMk('hour', id)}${handMk('minute', id)}
      <circle r="${H.pad_r}" fill="url(#hubpad${id})"/>
      <g class="h-s"><path d="M${-S.w / 2} ${-S.tip}H${S.w / 2}V${S.tail}H${-S.w / 2}Z" fill="${S.colour}"/></g>
      <circle r="${f2((H.ring_r[0] + H.ring_r[1]) / 2)}" fill="none" stroke="${H.ring_colour}" stroke-width="${f2(H.ring_r[1] - H.ring_r[0])}"/>
      <circle r="${H.screw_r}" fill="${H.screw_colour}"/><circle r="1.1" fill="#3A2A2C"/></g>`;
  };
  const setFacets = (w, k, ang) => {
    const el = $(`.h-${k[0]}`, w.el); if (!el) return;
    for (const s of ['l', 'r']) {
      const q = Math.round(facetFactor(k, ang, s) * 50) / 50, key = k + s;
      if (w.fq[key] !== q) { w.fq[key] = q; $(s === 'l' ? '.fl' : '.fr', el).style.filter = `brightness(${q})`; }
    }
  };
  const poseHands = root => {
    $('.h-h', root).setAttribute('transform', `rotate(${POSE.hour})`);
    $('.h-m', root).setAttribute('transform', `rotate(${POSE.minute})`);
    $('.h-s', root).setAttribute('transform', `rotate(${POSE.second})`);
  };

  /* --- the face (everything printed on the dial) --- */
  const faceMk = (id, { hands = true } = {}) => `<defs>${dateDefs()}${handDefs(id)}</defs>
    <g class="p-track">${ticksMk()}${textMk(['min'])}</g><g class="p-rings">${ringsMk()}</g><g class="p-chords">${chordsMk()}</g><g class="p-rays">${raysMk()}</g>
    <g class="p-hours">${textMk(['hour'])}</g><g class="p-brand">${textMk(['logo', 'automatic'])}${dateMk()}</g>
    ${hands ? handsMk(id) : ''}`;

  /* --- dial background: measured two-lobe shading + brushed texture --- */
  const dialBg = (() => {
    const st = SH.main.map((c, i) => `${c} ${i * SH.step_deg}deg`).concat(`${SH.main[0]} 360deg`).join(',');
    return `var(--brush, none), conic-gradient(from calc(var(--la, 40deg) - 40deg) at 50% 50%, ${st})`;
  })();
  const chapterBg = (() => {
    const st = SH.outer.map((c, i) => `${c} ${i * SH.step_deg}deg`).concat(`${SH.outer[0]} 360deg`).join(',');
    return `conic-gradient(from calc(var(--la, 40deg) - 40deg) at 50% 50%, ${st})`;
  })();
  // sun-brush: fine radial lines (correlation ~0.55 deg, luminance sigma ~4/255) generated once, seeded so every load is identical
  (() => {
    const N = 1024, cv = document.createElement('canvas'); cv.width = cv.height = N;
    const g = cv.getContext('2d'); if (!g) return;
    let s = 0x9E3779B9;
    const rnd = () => { s = (s + 0x6D2B79F5) | 0; let t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
    const steps = 2880, amp = SH.brush.amplitude / 255, sm = [];
    let v = 0; for (let i = 0; i < steps + 8; i++) { v = v * .62 + (rnd() - .5) * 1.6; sm.push(v); }
    g.translate(N / 2, N / 2);
    for (let i = 0; i < steps; i++) {
      const a0 = i * 2 * Math.PI / steps, a1 = (i + 1.2) * 2 * Math.PI / steps, val = sm[i] * 2.1 * amp;
      g.fillStyle = val > 0 ? `rgba(255,255,255,${Math.min(.25, val * 2.6)})` : `rgba(0,0,0,${Math.min(.3, -val * 2.6)})`;
      g.beginPath(); g.moveTo(0, 0); g.arc(0, 0, N * .72, a0 - Math.PI / 2, a1 - Math.PI / 2); g.closePath(); g.fill();
    }
    try { document.documentElement.style.setProperty('--brush', `url(${cv.toDataURL('image/png')}) center / 100% 100%`); } catch (_) { /* canvas may be blocked */ }
    document.documentElement.style.setProperty('--dial-bg', dialBg);
    document.documentElement.style.setProperty('--chapter-bg', chapterBg);
  })();

  /* --- bezel (120 teeth) and body (traced case, lugs, crown, bracelet) --- */
  const bezelMk = id => {
    const n = BZ.inner_ring_colours.length, step = 360 / n;
    let s = `<g class="bz">`;
    s += BZ.inner_ring_colours.map((c, i) => `<path d="${wedge(BZ.inner_ring[0], BZ.inner_ring[1], i * step - .2, (i + 1) * step + .2)}" fill="${c}"/>`).join('');
    s += `<circle r="${f2((BZ.r_in + BZ.r_out) / 2)}" fill="none" stroke="${BZ.groove_colour}" stroke-width="${f2(BZ.r_out - BZ.r_in + 2)}"/><g class="teeth">`;
    const pitch = 360 / BZ.count, c = BZ.corner, hg = Math.asin(BZ.groove_w / 2 / ((BZ.r_in + BZ.r_out) / 2)) * 180 / Math.PI, ce = c / BZ.r_out * 180 / Math.PI;
    for (let i = 0; i < BZ.count; i++) {
      const a0 = BZ.first_groove_deg + pitch * i + hg + ce, a1 = BZ.first_groove_deg + pitch * (i + 1) - hg - ce, col = BZ.tooth_colours[i];
      s += `<path data-i="${i}" d="${wedge(BZ.r_in + c, BZ.r_out - c, a0, a1)}" fill="${col}" stroke="${col}" stroke-width="${f2(2 * c)}" stroke-linejoin="round"/>`;
    }
    return s + '</g></g>';
  };
  const updateBezel = (root, shift) => {
    const t = $$('.teeth path', root); if (!t.length) return;
    const n = t.length;
    t.forEach((p, i) => { const col = BZ.tooth_colours[(((i - shift) % n) + n) % n]; p.setAttribute('fill', col); p.setAttribute('stroke', col); });
  };
  const bodyPaths = (flip = false) => `<g transform="${flip ? 'scale(-1 1) ' : ''}scale(${f2(BODY_SCALE * 1e4) / 1e4})" fill-rule="evenodd">${BODY.levels.map(l => `<path d="${l.d}" fill="${l.fill}"/>`).join('')}</g>`;
  const bodyInner = (id, { flip = false, bezel = true } = {}) => `<defs>
      <clipPath id="sil${id}"><path transform="${flip ? 'scale(-1 1) ' : ''}scale(${f2(BODY_SCALE * 1e4) / 1e4})" d="${BODY.levels[0].d}"/></clipPath>
      <linearGradient id="gl${id}" class="cg" gradientUnits="userSpaceOnUse" x1="-260" y1="-260" x2="260" y2="260">
        <stop offset="0" stop-color="#fff" stop-opacity=".62"/><stop offset=".38" stop-color="#fff" stop-opacity="0"/><stop offset=".62" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".5"/></linearGradient></defs>
    ${bodyPaths(flip)}<circle r="${BODY.inner_radius_units + .6}" fill="#1E1E1F"/>
    <g clip-path="url(#sil${id})"><rect x="-300" y="-520" width="620" height="1040" fill="url(#gl${id})" style="mix-blend-mode:soft-light" opacity=".55"/></g>
    ${bezel ? bezelMk(id) : ''}`;
  const caseSvg = (id, { E, open = false }) => `<svg class="w-svg${open ? ' open' : ''}" viewBox="${f2(VX)} ${-E} ${f2(VW)} ${2 * E}" aria-hidden="true">${bodyInner(id)}</svg>`;

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
  function caseBackMk(E) {
    // the body seen from behind is the same silhouette mirrored; the round caseback window and movement sit on top (drawn at 1.84x the old size)
    return `<svg id="caseback" viewBox="${f2(-(UB[2] + PAD))} ${-E} ${f2(VW)} ${2 * E}" aria-hidden="true">${bodyInner('bk', { flip: true, bezel: false })}
      <g transform="scale(1.84)"><circle r="119" fill="url(#cfbk)" stroke="#6F7174" stroke-width=".8"/><circle r="107" fill="none" stroke="#7B7D81" stroke-width="3"/>
      <path id="bkarc" d="M-113 0 A113 113 0 0 1 113 0" fill="none"/>
      <text font-family="Poppins,sans-serif" font-size="8" font-weight="600" letter-spacing="3" fill="#4A4C4F"><textPath href="#bkarc" startOffset="64%">SWISS</textPath></text>
      ${movementMk()}</g>
      <defs><linearGradient id="cfbk" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".4" stop-color="#D9DBDD"/><stop offset=".7" stop-color="#F6F7F8"/><stop offset="1" stop-color="#BFC1C4"/></linearGradient></defs></svg>`;
  }

  /* ---------------- watch instances ---------------- */
  let uid = 0;
  const watches = [];
  function mountWatch(slot, { E = 380, open = false, drag = false, live = true } = {}) {
    const id = ++uid;
    const dl = f2((-200 - VX) / VW * 100), dw = f2(400 / VW * 100);
    slot.innerHTML = `<div class="watch" role="img" aria-label="SISTEM BOREAL YIS401GC" style="--ar:${f2(VW)} / ${2 * E}">
      ${caseSvg(id, { E, open })}
      <div class="w-dial" style="left:${dl}%;width:${dw}%"><svg class="w-face" viewBox="-200 -200 400 400" aria-hidden="true">${faceMk(id)}</svg></div><div class="w-crystal" style="left:${dl}%;width:${dw}%"></div></div>`;
    const el = slot.firstElementChild;
    const w = { el, offset: 0, live, h: $('.h-h', el), m: $('.h-m', el), s: $('.h-s', el), date: $('.date-txt', el), grads: $$('.cg', el), fq: {}, shift: null, lastDay: null };
    if (drag) {
      const dial = $('.w-dial', el);
      dial.style.cursor = 'grab';
      const move = e => {
        const r = el.getBoundingClientRect(), dr = dial.getBoundingClientRect();
        const cx = dr.left + dr.width / 2, cy = dr.top + dr.height / 2;
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
    // the photo's hands are at 10:09; their drawn pose is the measured one, the clock rotates them from that reference
    w.s.setAttribute('transform', `rotate(${(s * 6).toFixed(2)})`);
    w.m.setAttribute('transform', `rotate(${(m * 6).toFixed(2)})`);
    w.h.setAttribute('transform', `rotate(${(h * 30).toFixed(2)})`);
    setFacets(w, 'hour', (h * 30) % 360); setFacets(w, 'minute', (m * 6) % 360);
    const dd = d.getDate();
    if (w.date && w.lastDay !== dd) { w.lastDay = dd; setDate(w.date, dd); }
  }
  const setMetalLight = (w, deg) => {
    w.grads.forEach(g => g.setAttribute('gradientTransform', `rotate(${deg.toFixed(1)})`));
    const sh = Math.round((deg - 40) / 3);
    if (sh !== w.shift) { w.shift = sh; updateBezel(w.el, sh); }
  };

  const hero = $('#hero');
  const heroW = mountWatch($('#watch-hero'), { E: 470, open: true, drag: true });
  const lightW = mountWatch($('#watch-light'), { E: 380 });
  mountWatch($('#watch-flip'), { E: 380 });
  { const el = $('.watch', $('#watch-flip')); el.style.setProperty('--la', '40deg'); }
  $('#caseback').outerHTML = caseBackMk(380);

  /* ---------------- hero background: the dial geometry, enlarged ---------------- */
  $('#hero-lines').innerHTML = `<g transform="scale(2)" stroke-opacity=".5" fill-opacity=".5" fill="none">${ringsMk()}${chordsMk()}${raysMk()}</g>`;

  /* ---------------- exploded anatomy layers ---------------- */
  (() => {
    const VB = '-285 -285 570 570';
    $('.l-case').innerHTML = `<svg viewBox="${VB}">${bodyInner('ec', { bezel: false })}</svg>`;
    $('.l-bezel').innerHTML = `<svg viewBox="${VB}">${bezelMk('eb')}</svg>`;
    $('#ex-dial').innerHTML = `<svg viewBox="-200 -200 400 400">${faceMk('ed', { hands: false })}</svg>`;
    $('#static-hands').innerHTML = `<svg viewBox="-200 -200 400 400"><defs>${handDefs('sx')}</defs>${handsMk('sx')}</svg>`;
    const g = $('#static-hands'); poseHands(g);
    setFacets({ el: g, fq: {} }, 'hour', POSE.hour); setFacets({ el: g, fq: {} }, 'minute', POSE.minute);
    setDate($('.date-txt', $('#ex-dial')), 28);
  })();

  /* ---------------- blueprint (geometry lab) ---------------- */
  (() => {
    const bp = $('#blueprint');
    const grp = (k, inner) => `<g class="g" data-k="${k}" style="--len:1200">${inner}</g>`;
    bp.innerHTML = `<defs>${dateDefs()}${handDefs('bp')}</defs>`
      + grp('track', ticksMk('draw') + textMk(['min'])) + grp('rings', ringsMk('draw')) + grp('chords', chordsMk('draw')) + grp('rays', raysMk())
      + grp('hours', textMk(['hour'])) + grp('brand', textMk(['logo', 'automatic']) + dateMk()) + grp('hands', handsMk('bp'));
    poseHands(bp); setDate($('.date-txt', bp), 28);
    setFacets({ el: bp, fq: {} }, 'hour', POSE.hour); setFacets({ el: bp, fq: {} }, 'minute', POSE.minute);
  })();

  /* ---------------- light lab ---------------- */
  const mix = (a, b, t) => {
    const p = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
    const A = p(a), B = p(b);
    return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, '0')).join('').toUpperCase();
  };
  // perceived blue on the left of the dial: sample the MEASURED shading profile (72 samples, 5 deg) at screen angle 270 for the current light angle
  const perceived = la => {
    const x = ((((270 - (la - 40)) % 360) + 360) % 360) / SH.step_deg, i = Math.floor(x) % SH.main.length, t = x - Math.floor(x);
    return mix(SH.main[i], SH.main[(i + 1) % SH.main.length], t);
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
  const LINE = '#D3D9E4';
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


  /* ---------------- 08 edge lab: every pipeline stage drawn from its own output ---------------- */
  const LAB = (B.pipeline && B.pipeline.stages) || [];
  let labI = 0, labWatch = null;
  const TINT = { ring: '#F4B860', tick: '#7FD6E8', ray: '#F08BB4', chord: '#9BE29A', text: '#FFFFFF', recon: '#FFB36B', hand: '#DADDE3', resid: '#FF7A7A' };
  const tint = (c, inner) => `<g class="tint" style="--c:${c}">${inner}</g>`;
  const dim = inner => `<g opacity=".28">${inner}</g>`;
  const lt = (x, y, t, a = 'start') => `<text class="lab-t" x="${x}" y="${y}" text-anchor="${a}">${t}</text>`;
  const labSvg = (st, tones) => {
    const faceBase = ringsMk() + chordsMk() + raysMk() + ticksMk();
    switch (st.fig) {
      case 'calibrate': {
        const R_ = DL.rings.map(r => `<circle r="${r.r}" fill="none" stroke="${TINT.ring}" stroke-width="1.1"/>${lt(r.r + 2, -2, (r.r / 200).toFixed(3) + 'R')}`).join('');
        return ['-215 -215 430 430', `<g stroke="#fff" stroke-opacity=".5" stroke-width=".4"><path d="M-210 0H210M0 -210V210"/></g>
          <circle r="200" fill="none" stroke="#fff" stroke-dasharray="3 3" stroke-width=".7"/>${lt(4, -203, 'R = 200 (dial edge)')}
          <circle r="${BZ.r_in}" fill="none" stroke="#7FD6E8" stroke-width=".6"/><circle r="${BZ.r_out}" fill="none" stroke="#7FD6E8" stroke-width=".6"/>${lt(-BZ.r_in * .72, -BZ.r_in * .72, 'teeth')}
          <circle r="${DL.chapter_band_inner}" fill="none" stroke="#fff" stroke-opacity=".5" stroke-dasharray="1 2" stroke-width=".6"/>${R_}
          <circle r="2.2" fill="#FF5A5A"/>${lt(6, 10, 'centre = (' + B.unit.centre_px[0] + ', ' + B.unit.centre_px[1] + ') px')}`];
      }
      case 'edges':
        return ['-240 -240 480 480', `<g class="edgeview">${bezelMk('le')}${faceMk('le')}</g>`];
      case 'hands': {
        const a = P(190, POSE.hour), b = P(190, POSE.minute);
        return ['-215 -215 430 430', `${dim(faceBase)}${handsMk('lh')}
          <g stroke="#FFB36B" stroke-width=".5" stroke-dasharray="3 2" fill="none"><path d="M0 0L${P(205, POSE.hour).join(' ')}M0 0L${P(205, POSE.minute).join(' ')}M0 0V-205"/></g>
          ${lt(a[0] - 34, a[1], POSE.hour.toFixed(2) + '°')}${lt(b[0] + 4, b[1], POSE.minute.toFixed(2) + '°')}`];
      }
      case 'primitives':
        return ['-215 -215 430 430', tint(TINT.ring, ringsMk()) + tint(TINT.tick, ticksMk()) + tint(TINT.ray, raysMk())];
      case 'chords': {
        const dots = DL.chords.flatMap(c => [c.a, c.b]).map(p => `<circle cx="${p[0]}" cy="${p[1]}" r="2.1" fill="#FFB36B" stroke="none"/>`).join('');
        return ['-215 -215 430 430', dim(ringsMk()) + tint(TINT.chord, chordsMk()) + dots];
      }
      case 'residual':
        return ['-215 -215 430 430', dim(faceBase) + `<g style="--c:${TINT.resid}">${DL.text.map(t => `<path d="${t.d}" fill="${TINT.resid}" fill-rule="evenodd" transform="translate(${t.x} ${t.y}) rotate(${t.rot})"/>`).join('')}</g>${dateMk()}`];
      case 'text': {
        const mk = recon => DL.text.filter(t => !!t.reconstructed === recon).map(t => `<path d="${t.d}" fill="${recon ? TINT.recon : '#fff'}" fill-rule="evenodd" transform="translate(${t.x} ${t.y}) rotate(${t.rot})"/>`).join('');
        return ['-215 -215 430 430', dim(ringsMk() + chordsMk()) + mk(false) + mk(true) + lt(-205, 210, 'white = measured · orange = reconstructed')];
      }
      case 'details':
        return ['-215 -215 430 430', dim(faceBase + textMk(['min', 'hour'])) + textMk(['logo', 'automatic']) + dateMk()];
      case 'body': {
        const lv = BODY.levels.slice(0, tones + 1);
        return [`${f2(VX)} -520 ${f2(VW)} 1040`, `<g transform="scale(${f2(BODY_SCALE * 1e4) / 1e4})" fill-rule="evenodd">${lv.map(l => `<path d="${l.d}" fill="${l.fill}"/>`).join('')}</g>`];
      }
      case 'bezel':
        return ['-240 -240 480 480', `<circle r="${BZ.inner_ring[0]}" fill="#032557"/>${bezelMk('lb')}<circle r="${BODY.inner_radius_units}" fill="none" stroke="#fff" stroke-opacity=".3" stroke-dasharray="2 3"/>`];
      default:
        return null;
    }
  };
  function renderLab() {
    const steps = $('#steps'); if (!steps || !LAB.length) return;
    steps.innerHTML = LAB.map((st, i) => `<li><button type="button" data-i="${i}" ${i === labI ? 'aria-current="true"' : ''}>${st[lang][0]}</button></li>`).join('');
    $$('button', steps).forEach(b => b.addEventListener('click', () => { labI = +b.dataset.i; renderLab(); }));
    const st = LAB[labI], tx = st[lang];
    $('#lab-info').innerHTML = `<h3>${tx[0]}</h3><p>${tx[1]}</p><dl>${st.facts.map(f => `<div><dt>${f[lang]}</dt><dd>${f.v}</dd></div>`).join('')}</dl>
      <div class="file">${T[lang].lab_file}: pipeline/${st.file}</div><p class="lab-note">${T[lang].lab_note}</p>`;
    const fig = $('#lab-fig'), tones = +$('#lab-slider').value;
    $('#lab-slider-wrap').hidden = st.fig !== 'body';
    const out = labSvg(st, tones);
    const holder = fig.parentElement;
    if (!out) {                                   // "build" / "verify": show the live watch itself
      fig.style.display = 'none';
      if (!labWatch) { const slot = document.createElement('div'); slot.className = 'watch-slot'; slot.style.width = 'min(100%, 300px)'; holder.appendChild(slot); labWatch = mountWatch(slot, { E: 330 }); labWatch.slot = slot; }
      labWatch.slot.style.display = '';
    } else {
      fig.style.display = '';
      if (labWatch) labWatch.slot.style.display = 'none';
      fig.setAttribute('viewBox', out[0]);
      fig.innerHTML = `<defs>${dateDefs()}${handDefs('lh')}${handDefs('le')}</defs>${out[1]}`;
      if (st.fig === 'hands' || st.fig === 'edges') {
        poseHands(fig); setFacets({ el: fig, fq: {} }, 'hour', POSE.hour); setFacets({ el: fig, fq: {} }, 'minute', POSE.minute);
      }
      const d = $('.date-txt', fig); if (d) setDate(d, 28);
    }
  }
  $('#lab-slider').addEventListener('input', e => { $('#lab-slider-out').textContent = e.target.value; renderLab(); });
  labReady = true;

  /* ---------------- pointer + animation loop ---------------- */
  let px = innerWidth / 2, py = innerHeight / 2;
  addEventListener('pointermove', e => { px = e.clientX; py = e.clientY; lastPointer = performance.now(); }, { passive: true });
  let la = 40, tx = 0, ty = 0;

  function frame(now) {
    const idle = now - lastPointer > 2600;
    const heroVisible = hero.getBoundingClientRect().bottom > 0;
    if (heroVisible) {
      const r = heroW.el.getBoundingClientRect();
      const cx = r.left + r.width * (-VX / VW), cy = r.top + r.height / 2;
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
