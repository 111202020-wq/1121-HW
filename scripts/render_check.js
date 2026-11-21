// 關卡 5：渲染檢查（在瀏覽器開 deck/index.html 後執行）
// 只量「文字元素」是否超出自己的框，以及每頁內容區是否超出高度；
// 第 1 版連方塊外的裝飾箭頭也算進去，造成第 3 頁誤報，已修正。
(async () => {
  await document.fonts.ready;
  const res = [];
  document.querySelectorAll('.slide').forEach((s, i) => {
    s.style.display = 'block';
    const b = s.querySelector('.body');
    const over = [];
    if (b.scrollHeight > b.clientHeight + 1) over.push(`內容高度溢出 ${b.scrollHeight - b.clientHeight}px`);
    s.querySelectorAll('h2, .lead, .kpi b, .kpi span, .flow b, .flow span, .card h3, .card p, td, th, .steps b, .checks b, .timeline span, .analogy p, .formula')
      .forEach(el => { if (el.scrollWidth > el.clientWidth + 1) over.push(`${el.tagName.toLowerCase()}「${el.textContent.slice(0, 12)}」橫向溢出 ${el.scrollWidth - el.clientWidth}px`); });
    res.push({ slide: i + 1, ok: over.length === 0, over });
    s.style.display = '';
  });
  return JSON.stringify({ pass: res.filter(r => r.ok).length, fail: res.filter(r => !r.ok) });
})();
