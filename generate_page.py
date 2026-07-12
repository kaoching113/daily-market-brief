#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from urllib.parse import quote

GROUP_META = {
    "股市指數": {"eyebrow": "EQUITY INDICES"},
    "商品": {"eyebrow": "COMMODITIES"},
    "匯率": {"eyebrow": "CURRENCIES"},
}

CURRENCY_LABEL = {
    "TWD": "TWD", "USD": "USD", "EUR": "EUR",
    "HKD": "HKD", "CNY": "CNY",
}

def fmt_price(price, symbol):
    if price is None:
        return "—"
    if symbol in ("TWD=X", "EURTWD=X", "CNYTWD=X"):
        return f"{price:,.3f}"
    if price >= 1000:
        return f"{price:,.2f}"
    return f"{price:,.2f}"

def fmt_change(change, pct, symbol):
    if change is None or pct is None:
        return "—", "—", "flat"
    direction = "rise" if change > 0 else ("fall" if change < 0 else "flat")
    arrow = "▲" if change > 0 else ("▼" if change < 0 else "•")
    decimals = 3 if symbol in ("TWD=X", "EURTWD=X", "CNYTWD=X") else 2
    change_str = f"{arrow}{abs(change):,.{decimals}f}"
    pct_str = f"{pct:+.2f}%"
    return change_str, pct_str, direction

def esc_attr(s):
    return s.replace("&", "&amp;").replace('"', "&quot;")

def render_row(item):
    name = item["name"]
    symbol = item["symbol"]
    if "error" in item:
        return f"""
          <div class="row" data-symbol="{esc_attr(symbol)}" data-name="{esc_attr(name)}" tabindex="0" role="button">
            <div class="row-top">
              <span class="row-name">{name}</span>
              <span class="row-price muted">資料暫缺</span>
            </div>
            <div class="row-bottom">
              <span class="row-symbol">{symbol}</span>
            </div>
          </div>"""
    price = fmt_price(item["price"], symbol)
    currency = CURRENCY_LABEL.get(item.get("currency"), item.get("currency", ""))
    change_str, pct_str, direction = fmt_change(item.get("change"), item.get("changePercent"), symbol)
    return f"""
          <div class="row" data-symbol="{esc_attr(symbol)}" data-name="{esc_attr(name)}" tabindex="0" role="button">
            <div class="row-top">
              <span class="row-name">{name}</span>
              <span class="row-price">{price}<span class="row-currency">{currency}</span></span>
            </div>
            <div class="row-bottom">
              <span class="row-symbol">{symbol}</span>
              <span class="row-change {direction}">{change_str} <span class="row-pct">{pct_str}</span></span>
            </div>
          </div>"""

def render_group(group_name, items):
    meta = GROUP_META.get(group_name, {"eyebrow": group_name.upper()})
    rows = "\n".join(render_row(i) for i in items)
    return f"""
      <section class="data-group">
        <header class="group-head">
          <span class="eyebrow">{meta['eyebrow']}</span>
          <h2>{group_name}</h2>
        </header>
        <div class="data-table">
          {rows}
        </div>
      </section>"""

def translate_url(url):
    return f"https://translate.google.com/translate?sl=auto&tl=zh-TW&u={quote(url, safe='')}"

def render_news_item(item, uid):
    lang = item.get("lang", "zh")
    href = translate_url(item["url"]) if lang == "en" else item["url"]
    tag = '<span class="lang-tag">英文・自動翻譯</span>' if lang == "en" else ""
    teaser = item.get("teaser", "")
    commentary = item.get("commentary", "")
    note_html = ""
    if teaser and commentary:
        note_html = f"""
            <button class="note-toggle" data-target="note-{uid}" type="button">
              <span class="note-icon">💡</span><span class="note-teaser">{teaser}</span>
              <span class="note-arrow">看全文</span>
            </button>
            <div class="note-body" id="note-{uid}" hidden>{commentary}</div>"""
    return f"""
          <li class="news-item">
            <a class="news-title" href="{href}" target="_blank" rel="noopener">{item['title']}</a>
            <div class="news-meta">
              <span class="news-source">{item['source']}</span>
              {tag}
            </div>
            {note_html}
          </li>"""

def render_news_group(group):
    items = []
    for i, item in enumerate(group["items"]):
        uid = f"{group['category']}-{i}"
        items.append(render_news_item(item, uid))
    items_html = "\n".join(items)
    return f"""
      <section class="news-group">
        <header class="group-head">
          <span class="eyebrow">{group['eyebrow']}</span>
          <h2>{group['category']}</h2>
        </header>
        <ul class="news-list">
          {items_html}
        </ul>
      </section>"""

def render_news_section(news):
    if not news:
        return ""
    return "\n".join(render_news_group(g) for g in news["groups"])

def main():
    data_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data.json")
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("index.html")
    data = json.loads(data_path.read_text(encoding="utf-8"))

    news_path = data_path.parent / "news.json"
    news = json.loads(news_path.read_text(encoding="utf-8")) if news_path.exists() else None

    history_path = data_path.parent / "history.json"
    history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else {}

    groups = {}
    for item in data["items"]:
        groups.setdefault(item["group"], []).append(item)

    order = ["股市指數", "商品", "匯率"]
    sections = "\n".join(render_group(g, groups[g]) for g in order if g in groups)
    news_section = render_news_section(news)
    history_json = json.dumps(history, separators=(",", ":"))

    html = HTML_TEMPLATE.format(
        updated_at=data["updatedAt"],
        sections=sections,
        news_section=news_section,
        history_json=history_json,
    )
    out_path.write_text(html, encoding="utf-8")
    print(f"wrote {out_path}")

HTML_TEMPLATE = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>市場晨報</title>
<style>
:root {{
  --bg: #f5f4f1;
  --surface: #ffffff;
  --border: #e4e1da;
  --ink: #1c2230;
  --muted: #62697a;
  --accent: #1f3d63;
  --accent-soft: #e8edf3;
  --rise: #c23b3b;
  --rise-soft: #fbeaea;
  --fall: #1f8a5f;
  --fall-soft: #e8f5ee;
  --overlay: rgba(20, 22, 28, 0.5);
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #12151c;
    --surface: #1a1e28;
    --border: #2b303c;
    --ink: #eef0f4;
    --muted: #98a0b3;
    --accent: #7da5d8;
    --accent-soft: rgba(125,165,216,0.12);
    --rise: #e2726d;
    --rise-soft: rgba(226,114,109,0.14);
    --fall: #4fc08d;
    --fall-soft: rgba(79,192,141,0.14);
    --overlay: rgba(0, 0, 0, 0.65);
  }}
}}
:root[data-theme="dark"] {{
  --bg: #12151c;
  --surface: #1a1e28;
  --border: #2b303c;
  --ink: #eef0f4;
  --muted: #98a0b3;
  --accent: #7da5d8;
  --accent-soft: rgba(125,165,216,0.12);
  --rise: #e2726d;
  --rise-soft: rgba(226,114,109,0.14);
  --fall: #4fc08d;
  --fall-soft: rgba(79,192,141,0.14);
  --overlay: rgba(0, 0, 0, 0.65);
}}
:root[data-theme="light"] {{
  --bg: #f5f4f1;
  --surface: #ffffff;
  --border: #e4e1da;
  --ink: #1c2230;
  --muted: #62697a;
  --accent: #1f3d63;
  --accent-soft: #e8edf3;
  --rise: #c23b3b;
  --rise-soft: #fbeaea;
  --fall: #1f8a5f;
  --fall-soft: #e8f5ee;
  --overlay: rgba(20, 22, 28, 0.5);
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "PingFang TC", "Microsoft JhengHei", "Noto Sans TC", sans-serif;
  -webkit-font-smoothing: antialiased;
}}
.wrap {{
  max-width: 1080px;
  margin: 0 auto;
  padding: 22px 20px 28px;
}}
.masthead {{
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
  flex-wrap: wrap;
  border-bottom: 2px solid var(--ink);
  padding-bottom: 10px;
  margin-bottom: 16px;
}}
.masthead .eyebrow {{
  color: var(--accent);
}}
.masthead h1 {{
  margin: 2px 0 0;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.01em;
}}
.byline {{
  font-size: 12.5px;
  font-weight: 400;
  color: var(--muted);
  margin-left: 8px;
  letter-spacing: 0;
}}
.updated {{
  text-align: right;
  font-family: ui-monospace, "SF Mono", "Roboto Mono", monospace;
  font-size: 11px;
  color: var(--muted);
  line-height: 1.5;
}}
.updated strong {{
  display: block;
  color: var(--ink);
  font-size: 12.5px;
  font-weight: 600;
}}
.eyebrow {{
  font-family: ui-monospace, "SF Mono", "Roboto Mono", monospace;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
}}
.main-grid {{
  display: grid;
  grid-template-columns: 1fr;
  gap: 22px;
  align-items: start;
}}
.group-head {{
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 6px;
}}
.group-head h2 {{
  margin: 0;
  font-size: 13.5px;
  font-weight: 700;
}}
.data-column {{
  display: flex;
  flex-direction: column;
  gap: 12px;
}}
.data-group {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px 4px;
}}
.data-table {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  column-gap: 10px;
}}
.row {{
  padding: 6px 4px;
  margin: 0 -4px;
  border-bottom: 1px solid var(--border);
  min-width: 0;
  cursor: pointer;
  border-radius: 5px;
  transition: background-color 0.12s ease;
}}
.row:hover, .row:focus-visible {{
  background: var(--accent-soft);
  outline: none;
}}
.row:nth-last-child(-n+2) {{
  border-bottom: none;
}}
.row-top {{
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 4px;
  flex-wrap: wrap;
}}
.row-bottom {{
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 4px;
  margin-top: 1px;
}}
.row-name {{
  font-size: 11.5px;
  font-weight: 600;
  min-width: 0;
}}
.row-symbol {{
  font-family: ui-monospace, "SF Mono", "Roboto Mono", monospace;
  font-size: 8.5px;
  font-weight: 400;
  color: var(--muted);
}}
.row-price {{
  font-family: ui-monospace, "SF Mono", "Roboto Mono", monospace;
  font-variant-numeric: tabular-nums;
  font-size: 12.5px;
  font-weight: 600;
  text-align: right;
  white-space: nowrap;
  flex-shrink: 0;
}}
.row-price.muted {{
  font-size: 11px;
  font-weight: 400;
  color: var(--muted);
}}
.row-currency {{
  font-size: 9.5px;
  font-weight: 400;
  color: var(--muted);
  margin-left: 3px;
}}
.row-change {{
  font-family: ui-monospace, "SF Mono", "Roboto Mono", monospace;
  font-variant-numeric: tabular-nums;
  font-size: 11px;
  font-weight: 600;
  text-align: right;
  white-space: nowrap;
  flex-shrink: 0;
}}
.row-change.rise {{ color: var(--rise); }}
.row-change.fall {{ color: var(--fall); }}
.row-change.flat {{ color: var(--muted); }}
.row-pct {{
  font-size: 10px;
  font-weight: 600;
  opacity: 0.85;
}}
.news-column {{
  display: flex;
  flex-direction: column;
  gap: 16px;
}}
.news-group {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 14px;
}}
.news-list {{
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}}
.news-item {{
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}}
.news-item:last-child {{
  border-bottom: none;
  padding-bottom: 0;
}}
.news-title {{
  display: block;
  color: var(--ink);
  font-size: 16.5px;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: -0.005em;
  text-decoration: none;
}}
.news-title:hover {{
  color: var(--accent);
  text-decoration: underline;
}}
.news-meta {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}}
.news-source {{
  font-family: ui-monospace, "SF Mono", "Roboto Mono", monospace;
  font-size: 10.5px;
  color: var(--muted);
}}
.lang-tag {{
  font-size: 10px;
  color: var(--accent);
  background: var(--accent-soft);
  padding: 1px 6px;
  border-radius: 999px;
}}
.note-toggle {{
  display: flex;
  align-items: baseline;
  gap: 6px;
  width: 100%;
  margin-top: 8px;
  padding: 7px 9px;
  background: var(--accent-soft);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
}}
.note-icon {{
  flex-shrink: 0;
  font-size: 12px;
}}
.note-teaser {{
  flex: 1;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--accent);
  line-height: 1.4;
}}
.note-arrow {{
  flex-shrink: 0;
  font-size: 10.5px;
  color: var(--muted);
  white-space: nowrap;
}}
.note-toggle[aria-expanded="true"] .note-arrow {{
  display: none;
}}
.note-body {{
  margin-top: 6px;
  padding: 10px 12px;
  background: var(--bg);
  border-left: 3px solid var(--accent);
  border-radius: 0 6px 6px 0;
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--ink);
}}
footer {{
  border-top: 1px solid var(--border);
  padding-top: 10px;
  margin-top: 16px;
  color: var(--muted);
  font-size: 10.5px;
  line-height: 1.6;
}}
.modal-overlay {{
  position: fixed;
  inset: 0;
  background: var(--overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 100;
}}
.modal-overlay[hidden] {{ display: none; }}
.modal-box {{
  background: var(--surface);
  border-radius: 10px;
  border: 1px solid var(--border);
  width: 100%;
  max-width: 620px;
  max-height: 90vh;
  overflow: auto;
  padding: 18px 20px 20px;
}}
.modal-head {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 4px;
}}
.modal-title {{
  font-size: 16px;
  font-weight: 700;
}}
.modal-symbol {{
  font-family: ui-monospace, "SF Mono", "Roboto Mono", monospace;
  font-size: 11px;
  color: var(--muted);
  margin-top: 2px;
}}
.modal-close {{
  background: none;
  border: none;
  font-size: 20px;
  line-height: 1;
  color: var(--muted);
  cursor: pointer;
  padding: 4px;
}}
.modal-close:hover {{ color: var(--ink); }}
.modal-range {{
  font-size: 10.5px;
  color: var(--muted);
  margin: 4px 0 10px;
}}
.modal-empty {{
  padding: 40px 0;
  text-align: center;
  color: var(--muted);
  font-size: 12.5px;
}}
@media (min-width: 860px) {{
  .wrap {{ padding: 32px 28px 36px; }}
  .masthead h1 {{ font-size: 28px; }}
  .masthead {{ padding-bottom: 16px; margin-bottom: 22px; }}
  .main-grid {{ grid-template-columns: 0.86fr 1.14fr; gap: 28px; }}
  .news-title {{ font-size: 18px; }}
  .data-table {{ column-gap: 14px; }}
  .row-name {{ font-size: 12px; }}
  .row-symbol {{ font-size: 9px; }}
  .row-price {{ font-size: 14px; }}
}}
</style>
<div class="wrap">
  <div class="masthead">
    <div>
      <span class="eyebrow">DAILY MARKET BRIEF</span>
      <h1>市場晨報<span class="byline">By 高敬</span></h1>
    </div>
    <div class="updated">
      <strong>{updated_at}</strong>
      台灣時間・每日更新
    </div>
  </div>

  <div class="main-grid">
    <div class="data-column">
      {sections}
    </div>
    <div class="news-column">
      {news_section}
    </div>
  </div>

  <footer>
    市場數據來源：Yahoo Finance 公開報價；新聞來源列於各篇標題下方，每日台灣時間早上 7:00 自動更新一次。
    內容僅供市場觀察與內容參考，不構成投資建議。點擊各項數據可查看近半年走勢圖。
  </footer>
</div>

<div class="modal-overlay" id="chart-modal" hidden>
  <div class="modal-box" role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <div class="modal-head">
      <div>
        <div class="modal-title" id="modal-title">—</div>
        <div class="modal-symbol" id="modal-symbol">—</div>
      </div>
      <button class="modal-close" id="modal-close" type="button" aria-label="關閉">✕</button>
    </div>
    <div class="modal-range">近 6 個月走勢（日K）</div>
    <div id="modal-chart-area"></div>
  </div>
</div>

<script>
const HISTORY = {history_json};

(function() {{
  var overlay = document.getElementById('chart-modal');
  var closeBtn = document.getElementById('modal-close');
  var titleEl = document.getElementById('modal-title');
  var symbolEl = document.getElementById('modal-symbol');
  var chartArea = document.getElementById('modal-chart-area');

  function closeModal() {{
    overlay.hidden = true;
  }}

  function openModal(symbol, name) {{
    titleEl.textContent = name;
    symbolEl.textContent = symbol;
    var candles = HISTORY[symbol] || [];
    chartArea.innerHTML = '';
    if (candles.length < 15) {{
      var empty = document.createElement('div');
      empty.className = 'modal-empty';
      empty.textContent = '近期歷史資料不足，暫無法繪製走勢圖。';
      chartArea.appendChild(empty);
    }} else {{
      chartArea.appendChild(renderCandles(candles));
    }}
    overlay.hidden = false;
  }}

  function renderCandles(candles) {{
    var w = 580, h = 260, padL = 52, padR = 10, padT = 10, padB = 24;
    var plotW = w - padL - padR, plotH = h - padT - padB;
    var lows = candles.map(function(c) {{ return c.l; }});
    var highs = candles.map(function(c) {{ return c.h; }});
    var min = Math.min.apply(null, lows);
    var max = Math.max.apply(null, highs);
    var range = (max - min) || 1;
    var n = candles.length;
    var slot = plotW / n;
    var candleW = Math.max(1.5, Math.min(7, slot * 0.6));

    function y(v) {{
      return padT + (1 - (v - min) / range) * plotH;
    }}

    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + w + ' ' + h);
    svg.setAttribute('width', '100%');
    svg.style.display = 'block';
    var gridColor = getComputedStyle(document.body).getPropertyValue('--border').trim();
    var textColor = getComputedStyle(document.body).getPropertyValue('--muted').trim();
    var riseColor = getComputedStyle(document.body).getPropertyValue('--rise').trim();
    var fallColor = getComputedStyle(document.body).getPropertyValue('--fall').trim();

    [0, 0.25, 0.5, 0.75, 1].forEach(function(t) {{
      var yy = padT + t * plotH;
      var line = document.createElementNS(ns, 'line');
      line.setAttribute('x1', padL); line.setAttribute('x2', w - padR);
      line.setAttribute('y1', yy); line.setAttribute('y2', yy);
      line.setAttribute('stroke', gridColor);
      line.setAttribute('stroke-width', '1');
      svg.appendChild(line);
      var label = document.createElementNS(ns, 'text');
      var val = max - t * range;
      label.setAttribute('x', 4);
      label.setAttribute('y', yy + 3);
      label.setAttribute('font-size', '9');
      label.setAttribute('fill', textColor);
      label.setAttribute('font-family', 'ui-monospace, monospace');
      label.textContent = val >= 1000 ? val.toFixed(0) : val.toFixed(2);
      svg.appendChild(label);
    }});

    candles.forEach(function(c, i) {{
      var cx = padL + slot * i + slot / 2;
      var color = c.c >= c.o ? riseColor : fallColor;
      var wick = document.createElementNS(ns, 'line');
      wick.setAttribute('x1', cx); wick.setAttribute('x2', cx);
      wick.setAttribute('y1', y(c.h)); wick.setAttribute('y2', y(c.l));
      wick.setAttribute('stroke', color);
      wick.setAttribute('stroke-width', '1');
      svg.appendChild(wick);
      var bodyTop = y(Math.max(c.o, c.c));
      var bodyH = Math.max(1, Math.abs(y(c.o) - y(c.c)));
      var rect = document.createElementNS(ns, 'rect');
      rect.setAttribute('x', cx - candleW / 2);
      rect.setAttribute('y', bodyTop);
      rect.setAttribute('width', candleW);
      rect.setAttribute('height', bodyH);
      rect.setAttribute('fill', color);
      svg.appendChild(rect);
    }});

    var monthSeen = {{}};
    candles.forEach(function(c, i) {{
      var d = new Date(c.t * 1000);
      var key = d.getFullYear() + '-' + d.getMonth();
      if (!monthSeen[key]) {{
        monthSeen[key] = true;
        var cx = padL + slot * i + slot / 2;
        var label = document.createElementNS(ns, 'text');
        label.setAttribute('x', cx);
        label.setAttribute('y', h - 6);
        label.setAttribute('font-size', '9');
        label.setAttribute('fill', textColor);
        label.setAttribute('font-family', 'ui-monospace, monospace');
        label.setAttribute('text-anchor', 'middle');
        label.textContent = (d.getMonth() + 1) + '月';
        svg.appendChild(label);
      }}
    }});

    return svg;
  }}

  document.querySelectorAll('.row[data-symbol]').forEach(function(row) {{
    row.addEventListener('click', function() {{
      openModal(row.getAttribute('data-symbol'), row.getAttribute('data-name'));
    }});
    row.addEventListener('keydown', function(e) {{
      if (e.key === 'Enter' || e.key === ' ') {{
        e.preventDefault();
        openModal(row.getAttribute('data-symbol'), row.getAttribute('data-name'));
      }}
    }});
  }});

  closeBtn.addEventListener('click', closeModal);
  overlay.addEventListener('click', function(e) {{
    if (e.target === overlay) closeModal();
  }});
  document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') closeModal();
  }});

  document.querySelectorAll('.note-toggle').forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      var target = document.getElementById(btn.getAttribute('data-target'));
      var expanded = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', String(!expanded));
      target.hidden = expanded;
    }});
  }});
}})();
</script>
"""

if __name__ == "__main__":
    main()
