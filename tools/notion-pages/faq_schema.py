"""FAQページ(official-*-faq.html)へ FAQPage 構造化データ(JSON-LD, 日本語)を注入する。冪等(マーカー間を置換)。
build_pages.py の最後で自動実行。単体: python3 faq_schema.py"""
import json, os, re, sys
from bs4 import BeautifulSoup
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
S, E_ = "<!-- FAQPAGE_LD -->", "<!-- /FAQPAGE_LD -->"
def run(files=("official-nha-faq.html", "official-spk-faq.html")):
    for fn in files:
        p = os.path.join(OUT, fn); src = open(p, encoding="utf-8").read()
        sec = BeautifulSoup(src, "html.parser").select_one('section.lg[data-lang="ja"]')
        items = []
        for q in sec.select(".qa"):
            qt = q.select_one(".qt").get_text(" ", strip=True); ab = q.select_one(".ab").get_text(" ", strip=True)
            if qt and ab: items.append({"@type": "Question", "name": qt, "acceptedAnswer": {"@type": "Answer", "text": ab}})
        ld = {"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": "ja", "url": "https://rent-handyman.com/" + fn, "mainEntity": items}
        blk = S + '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>" + E_
        src = re.sub(re.escape(S) + ".*?" + re.escape(E_), lambda m: blk, src, flags=re.S) if S in src else src.replace("</head>", blk + "\n</head>", 1)
        open(p, "w", encoding="utf-8").write(src); print(fn, "FAQPage", len(items))
if __name__ == "__main__": run()
