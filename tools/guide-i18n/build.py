"""ご利用案内・FAQ を4言語で書き出す。
使い方: python3 tools/guide-i18n/build.py （リポジトリの一番上で）
元の日本語: tools/guide-i18n/ja/*.html ／ 訳: tools/guide-i18n/trans.py
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from trans import T
LANGS = ['ja', 'en', 'zh', 'ko']
JP = re.compile(r'[぀-ヿ一-鿿]')
missing = set()

def tr_text(seg, i):
    s = seg.strip()
    if not s or not JP.search(s):
        return seg
    if s not in T:
        missing.add(s); return seg
    lead = seg[:len(seg) - len(seg.lstrip())]; tail = seg[len(seg.rstrip()):]
    return lead + T[s][i] + tail

def translate(block, lang):
    if lang == 'ja':
        return block
    i = LANGS.index(lang) - 1
    out = []
    for part in re.split(r'(<[^>]+>)', block):
        if part.startswith('<'):
            part = re.sub(r'alt="([^"]*)"', lambda m: 'alt="%s"' % tr_text(m.group(1), i).replace('"', '&quot;'), part)
            part = re.sub(r'\bid="(s\d)"', r'id="\1-%s"' % lang, part)
            part = re.sub(r'href="#(s\d)"', r'href="#\1-%s"' % lang, part)
            out.append(part)
        else:
            out.append(tr_text(part, i))
    return ''.join(out)

for name in ['official-guide.html', 'official-faq.html']:
    src = open(os.path.join(os.path.dirname(__file__), 'ja', name), encoding='utf-8').read()
    a = src.index('<div class="hero">'); b = src.index('<script src="kd-track.js">')
    block = src[a:b]
    blocks = ''.join('<div class="L L-%s" lang="%s">\n%s</div>\n' % (l, l, translate(block, l)) for l in LANGS)
    head = src[:a].replace('<a class="back" href="index.html">← トップへ戻る</a>',
                           '<div id="hdmlang-slot"></div><a class="back" href="index.html" data-i18n="mg_back">← トップへ戻る</a>')
    tail = src[b:].replace('<script src="kd-track.js">', '<script src="official-i18n.js"></script>\n<script src="kd-track.js">', 1)
    note = '<!-- このファイルは tools/guide-i18n/build.py で作っています。直すときは tools/guide-i18n/ja/ と trans.py を直してから build.py を実行してください -->\n'
    head = head.replace('<html lang="ja"><head>\n', '<html lang="ja"><head>\n' + note, 1)
    open(name, 'w', encoding='utf-8').write(head + blocks + tail)
if missing:
    print('訳がない文:'); [print(' ', m) for m in sorted(missing)]; sys.exit(1)
print('ok')
