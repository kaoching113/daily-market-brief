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

TEMPLATE_PATH = Path(__file__).parent / "template.html"

LIGHT_VARS = {
    "bg": "#f5f4f1",
    "surface": "#ffffff",
    "border": "#e4e1da",
    "ink": "#1c2230",
    "muted": "#62697a",
    "accent": "#1f3d63",
    "accent-soft": "#e8edf3",
    "rise": "#c23b3b",
    "rise-soft": "#fbeaea",
    "fall": "#1f8a5f",
    "fall-soft": "#e8f5ee",
    "overlay": "rgba(20, 22, 28, 0.5)",
}

DARK_VARS = {
    "bg": "#12151c",
    "surface": "#1a1e28",
    "border": "#2b303c",
    "ink": "#eef0f4",
    "muted": "#98a0b3",
    "accent": "#7da5d8",
    "accent-soft": "rgba(125,165,216,0.12)",
    "rise": "#e2726d",
    "rise-soft": "rgba(226,114,109,0.14)",
    "fall": "#4fc08d",
    "fall-soft": "rgba(79,192,141,0.14)",
    "overlay": "rgba(0, 0, 0, 0.65)",
}

def render_css_vars(vars_dict):
    return "".join(f"  --{key}: {value};\n" for key, value in vars_dict.items())

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

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = template.format(
        light_vars=render_css_vars(LIGHT_VARS),
        dark_vars=render_css_vars(DARK_VARS),
        updated_at=data["updatedAt"],
        sections=sections,
        news_section=news_section,
        history_json=history_json,
    )
    out_path.write_text(html, encoding="utf-8")
    print(f"wrote {out_path}")

if __name__ == "__main__":
    main()
