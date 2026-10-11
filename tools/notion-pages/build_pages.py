import json,html,re,os,shutil,subprocess,sys
OUT=os.path.expanduser("~/handyman-official")
IMGDIR="official-assets/notion"
PAGES=[
 # key, slug-id, out file, store label, kd page id, description
 ("faq_nha","2a4c8329c12680258f48ebb7e6d30234","official-nha-faq.html","那覇空港店","off_nha_faq","HANDYMAN RENTCAR 那覇空港店のよくある質問（予約・変更・キャンセル・お支払い・ご利用・補償など）。"),
 ("guide_nha","298c8329c12680858251f1755e436e72","official-nha-guide.html","那覇空港店","off_nha_guide","HANDYMAN RENTCAR 那覇空港店のご利用方法（ご予約から貸出・返却までの流れ）。"),
 ("faq_spk","234c8329c1268021b0c6e86b86dde0ac","official-spk-faq.html","札幌店","off_spk_faq","HANDYMAN RENTCAR 札幌店（デリバリー専門）のよくある質問（予約・キャンセル・デリバリー・貸出・返却・車両・オプション・補償・トラブル）。"),
 ("guide_spk","2a1c8329c12681729aebf8c3b3ea4466","official-spk-guide.html","札幌店","off_spk_guide","HANDYMAN RENTCAR 札幌店（デリバリー専門）のご利用方法（ご予約からお届け・回収までの流れ）。"),
]
PAGEMAP={p[1]:p[2] for p in PAGES}
PAGEMAP["10ec8329c12680208d3bf1352ff96452"]="official-clause.html"  # Notion「ご利用約款」→サイト内 貸渡約款
imgmap=json.load(open("imgmap.json"))
unresolved=[]
pagekey_pid={p[0]:p[1] for p in PAGES}
def nid(x): return x.replace("-","")
def V(B,i):
    b=B.get(i,{}).get("value",{}); return b.get("value",b)
COLORS={"red":"#d44c47","orange":"#d9730d","yellow":"#cb912f","green":"#448361","blue":"#337ea9","purple":"#9065b0","pink":"#c14c8a","brown":"#9f6b53","gray":"#787774"}
BGS={"red":"#fdebec","orange":"#fbecdd","yellow":"#fbf3db","green":"#edf3ec","blue":"#e7f3f8","purple":"#f4f0f7","pink":"#f9eef3","brown":"#f4eeee","gray":"#f1f1ef"}
def color_style(c):
    if not c or c=="default": return ""
    if c.endswith("_background"):
        k=c[:-11]; return f"background:{BGS.get(k,'#f1f1ef')};border-radius:3px;padding:0 2px"
    return f"color:{COLORS.get(c,'inherit')}"
def link_target(href,blockset,pagekey):
    h=href
    m=re.search(r"([0-9a-f]{32})(?:\?[^#]*)?(?:#([0-9a-f]{32}))?",h.replace("-",""))
    if h.startswith("http") and "notion" not in h: return h
    if m:
        pid,bid=m.group(1),m.group(2)
        if bid and bid in blockset: return "#b-"+bid
        if pid in PAGEMAP and pid!=pagekey_pid.get(pagekey): return PAGEMAP[pid]+(("#b-"+bid) if bid else "")
        if pid==pagekey_pid.get(pagekey): return "#"
        if pid in blockset: return "#b-"+pid
        unresolved.append((pagekey,href)); return h
    if h.startswith("/"):
        unresolved.append((pagekey,href)); return "https://plump-cap-ebe.notion.site"+h
    return h
def rich(prop,B,blockset,pagekey):
    out=""
    for seg in prop or []:
        t=seg[0]; anns=seg[1] if len(seg)>1 else []
        s=html.escape(t).replace("\n","<br>")
        if t=="‣":
            for a in anns:
                if a[0]=="p":
                    pid=nid(a[1]); title="".join(x[0] for x in (V(B,a[1]).get("properties",{}).get("title") or [])) or "リンク"
                    s=f'<a href="{link_target("/"+pid,blockset,pagekey)}">{html.escape(title)}</a>'
                elif a[0]=="lm":
                    hr=a[1].get("href",""); tt=a[1].get("title") or hr
                    s=f'<a href="{html.escape(hr)}" target="_blank" rel="noopener">{html.escape(tt)}</a>'
                elif a[0]=="d":
                    s=html.escape(a[1].get("start_date",""))
            out+=s; continue
        for a in anns:
            k=a[0]
            if k=="b": s=f"<b>{s}</b>"
            elif k=="i": s=f"<i>{s}</i>"
            elif k=="s": s=f"<s>{s}</s>"
            elif k=="_": s=f"<u>{s}</u>"
            elif k=="c": s=f"<code>{s}</code>"
            elif k=="h":
                st=color_style(a[1])
                if st: s=f'<span style="{st}">{s}</span>'
            elif k=="a":
                tgt=link_target(a[1],blockset,pagekey)
                ext=' target="_blank" rel="noopener"' if tgt.startswith("http") and "rent-handyman.com" not in tgt else ""
                s=f'<a href="{html.escape(tgt)}"{ext}>{s}</a>'
        out+=s
    return out
def build(key,root,pagekey,rng=None):
    d=json.load(open(key+".json")); B=d["blocks"]
    blockset={nid(k) for k in B}
    headers=[]
    def title_of(v): return rich(v.get("properties",{}).get("title"),B,blockset,pagekey)
    def children(v):
        return render_list(v.get("content",[]) or [])
    def render_list(ids):
        out=[]; i=0
        while i<len(ids):
            v=V(B,ids[i]); t=v.get("type")
            if not v or v.get("alive") is False: i+=1; continue
            if t in("bulleted_list","numbered_list"):
                tag="ul" if t=="bulleted_list" else "ol"; items=[]
                while i<len(ids) and V(B,ids[i]).get("type")==t:
                    vv=V(B,ids[i]); items.append(f'<li id="b-{nid(ids[i])}">{title_of(vv)}{children(vv)}</li>'); i+=1
                out.append(f"<{tag}>"+"".join(items)+f"</{tag}>"); continue
            out.append(render(ids[i],v)); i+=1
        return "".join(out)
    def render(i,v):
        t=v.get("type"); a=f'id="b-{nid(i)}"'; fmt=v.get("format",{}) or {}
        col=color_style(fmt.get("block_color"))
        sty=f' style="{col}"' if col else ""
        if t=="text":
            tt=title_of(v); return f'<p {a}{sty}>{tt or "&nbsp;"}</p>'+(f'<div class="ind">{children(v)}</div>' if v.get("content") else "")
        if t in("header","sub_header","sub_sub_header"):
            lv={"header":"h2","sub_header":"h2","sub_sub_header":"h3"}[t]
            txt=title_of(v); headers.append((lv,nid(i),re.sub("<[^>]+>","",txt)))
            if fmt.get("toggleable"):
                return f'<details class="tg" {a}><summary><{lv} class="{t}">{txt}</{lv}></summary>{children(v)}</details>'
            return f'<{lv} class="{t}" {a}{sty}>{txt}</{lv}>'+children(v)
        if t=="callout":
            icon=fmt.get("page_icon","")
            if icon and not re.match(r"^[^a-z/]{1,4}$",icon): icon=""
            bg=BGS.get((fmt.get("block_color") or "gray_background").replace("_background",""),"#f1f1ef")
            return f'<div class="callout" {a} style="background:{bg}"><span class="ci">{html.escape(icon)}</span><div>{title_of(v)}{children(v)}</div></div>'
        if t=="quote": return f'<blockquote {a}>{title_of(v)}{children(v)}</blockquote>'
        if t=="toggle": return f'<details class="tg" {a}><summary>{title_of(v)}</summary>{children(v)}</details>'
        if t=="divider": return '<hr>'
        if t=="image":
            src=imgmap.get(i); 
            if not src: return ""
            fn=os.path.basename(src); 
            w=fmt.get("block_width"); ws=f"max-width:{int(float(w))}px;" if w else ""
            cap=rich(v.get("properties",{}).get("caption"),B,blockset,pagekey)
            return f'<figure {a}><img src="{IMGDIR}/{fn}" alt="{re.sub("<[^>]+>","",cap) or "画像"}" loading="lazy" style="{ws}">'+(f"<figcaption>{cap}</figcaption>" if cap else "")+'</figure>'
        if t=="column_list":
            cols=[]
            for c in v.get("content",[]) or []:
                cv=V(B,c); cols.append(f'<div class="col">{children(cv)}</div>')
            return f'<div class="cols" {a}>'+"".join(cols)+'</div>'
        if t=="column": return children(v)
        if t=="table":
            order=fmt.get("table_block_column_order",[]); hdr=fmt.get("table_block_column_header")
            rows=[]
            for ri,r in enumerate(v.get("content",[]) or []):
                rv=V(B,r); props=rv.get("properties",{})
                tag="th" if (hdr and ri==0) else "td"
                rows.append("<tr>"+"".join(f"<{tag}>{rich(props.get(c),B,blockset,pagekey)}</{tag}>" for c in order)+"</tr>")
            return f'<div class="tblw" {a}><table>'+"".join(rows)+'</table></div>'
        if t=="table_of_contents": return "<!--TOC-->"
        if t=="page":
            return f'<p {a}><a href="{link_target("/"+nid(i),blockset,pagekey)}">{title_of(v)}</a></p>'
        if t in("bookmark","embed","video"):
            src=(v.get("properties",{}).get("source") or [[""]])[0][0]
            return f'<p {a}><a href="{html.escape(src)}" target="_blank" rel="noopener">{html.escape(src)}</a></p>' if src else ""
        if t=="transclusion_container" or t=="transclusion_reference": return children(v)
        print("UNHANDLED",key,t,file=sys.stderr); return children(v)
    rv=V(B,root)
    title=re.sub("<[^>]+>","","".join(x[0] for x in rv["properties"]["title"]))
    ids=rv.get("content",[]) or []
    if rng: ids=ids[rng[0]:rng[1]]
    body=render_list(ids)
    toc="".join(f'<li class="{lv}"><a href="#b-{bid}">{html.escape(tx)}</a></li>' for lv,bid,tx in headers if tx.strip())
    body=body.replace("<!--TOC-->",f'<nav class="toc"><ul>{toc}</ul></nav>')
    # FAQ JSON-LD (Japanese Q/A from sub_sub_header or text "Q.")
    return title,body
TPL=open("template.html").read()
LANGS=["ja","en","zh","ko"]
TITLES={
 "faq":{"ja":"よくある質問","en":"Frequently Asked Questions","zh":"常見問題","ko":"자주 묻는 질문"},
 "guide":{"ja":"ご利用方法","en":"How to Use","zh":"使用方式","ko":"이용 방법"},
}
STORE_L={"那覇空港店":{"ja":"那覇空港店","en":"Naha Airport Store","zh":"那霸機場店","ko":"나하공항점"},
         "札幌店":{"ja":"札幌店（デリバリー専門）","en":"Sapporo Store (Delivery only)","zh":"札幌店（專門配送）","ko":"삿포로점 (딜리버리 전문)"}}
def lang_ranges(key,root):
    d=json.load(open(key+".json")); B=d["blocks"]; rv=V(B,root); ids=[nid(x) for x in rv["content"]]
    starts=[]
    for i in ids[:8]:
        v=V(B,[x for x in rv["content"] if nid(x)==i][0])
        if v.get("type")!="callout": continue
        def links(v):
            o=[]
            for seg in v.get("properties",{}).get("title") or []:
                for a in (seg[1] if len(seg)>1 else []):
                    if a[0]=="a": o.append(a[1])
            for c in v.get("content",[]) or []: o+=links(V(B,c))
            return o
        for l in links(v):
            m=re.search(r"#([0-9a-f]{32})",l.replace("-",""))
            if m and m.group(1) in ids: starts.append(ids.index(m.group(1)))
    starts=sorted(starts)
    if len(starts)!=4: return None
    return [(starts[k], starts[k+1] if k<3 else None) for k in range(4)]
for key,slug,fn,store,kd,desc in PAGES:
    root=f"{slug[:8]}-{slug[8:12]}-{slug[12:16]}-{slug[16:20]}-{slug[20:]}"
    kind="faq" if key.startswith("faq") else "guide"
    rngs=lang_ranges(key,root)
    secs=[]
    for li,L in enumerate(LANGS):
        if rngs:
            _,body=build(key,root,key,rngs[li])
        elif L=="ja":
            _,body=build(key,root,key)
            open(f"trans/{key}_ja.html","w").write(body)
        else:
            p=f"trans/{key}_{L}.html"
            if not os.path.exists(p): print("MISSING translation",p); body="<p>(translation pending)</p>"
            else: body=open(p).read()
        h=f'<h1>{TITLES[kind][L]}</h1><div class="sub">HANDYMAN RENTCAR {STORE_L[store][L]}</div>'
        secs.append(f'<section class="lg" data-lang="{L}" lang="{ {"zh":"zh-Hant"}.get(L,L) }">{h}{body}</section>')
    title=TITLES[kind]["ja"]
    page=TPL.replace("{{TITLE}}",html.escape(title)).replace("{{STORE}}",store).replace("{{FILE}}",fn).replace("{{KD}}",kd).replace("{{DESC}}",html.escape(desc)).replace("{{BODY}}","".join(secs))
    open(os.path.join(OUT,fn),"w",encoding="utf-8").write(page)
    print(fn,len(page),"langs-from-notion" if rngs else "ja+translations")
print("UNRESOLVED",len(unresolved)); 
for u in sorted(set(unresolved)): print(" ",u)
