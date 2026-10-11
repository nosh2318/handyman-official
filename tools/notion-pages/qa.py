import re, copy
from bs4 import BeautifulSoup, NavigableString, Tag
QRE=re.compile(r"^\s*Q\s*[\.．:：]?\s*")
ARE=re.compile(r"^\s*A\s*[\.．:：]\s*")
def is_q(el):
    return isinstance(el,Tag) and el.name in("p","h3") and QRE.match(el.get_text()) is not None and re.match(r"^\s*Q\s*[\.．:：\s]",el.get_text()+" ")
def strip_prefix(el,rx):
    # remove prefix from first non-empty text node
    for s in el.descendants:
        if isinstance(s,NavigableString) and s.strip():
            new=rx.sub("",str(s),count=1)
            s.replace_with(new); return
def is_empty(el):
    return isinstance(el,Tag) and el.name=="p" and not el.get_text().strip().replace("\xa0","") and not el.find("img")
def transform(html):
    soup=BeautifulSoup(f"<div id='root'>{html}</div>","html.parser")
    root=soup.find(id="root")
    kids=[k for k in root.contents if not (isinstance(k,NavigableString) and not k.strip())]
    out=[]; i=0
    while i<len(kids):
        el=kids[i]
        if not is_q(el): out.append(el); i+=1; continue
        qel=copy.copy(el); qid=qel.get("id")
        ans=[]
        # split "Q...<br>A..." inside one paragraph
        if qel.name=="p":
            parts=[]; cur=[]
            for c in list(qel.contents):
                if isinstance(c,Tag) and c.name=="br":
                    parts.append(cur); cur=[]
                else: cur.append(c)
            parts.append(cur)
            qi=None
            for pi,pt in enumerate(parts):
                txt="".join(x.get_text() if isinstance(x,Tag) else str(x) for x in pt)
                if pi>0 and ARE.match(txt): qi=pi; break
            if qi:
                qp=soup.new_tag("span")
                for k,pt in enumerate(parts[:qi]):
                    if k: qp.append(soup.new_tag("br"))
                    for x in pt: qp.append(x)
                ap=soup.new_tag("p")
                for k,pt in enumerate(parts[qi:]):
                    if k: ap.append(soup.new_tag("br"))
                    for x in pt: ap.append(x)
                qinner=qp; ans.append(ap)
            else:
                qinner=soup.new_tag("span")
                for x in list(qel.contents): qinner.append(x)
        else:
            qinner=soup.new_tag("span")
            for x in list(qel.contents): qinner.append(x)
        strip_prefix(qinner,QRE)
        i+=1
        while i<len(kids):
            n=kids[i]
            if is_q(n) or (isinstance(n,Tag) and (n.name in("h2","hr","nav") or (n.name=="h3" and not is_q(n)))): break
            ans.append(n); i+=1
        while ans and is_empty(ans[-1]): ans.pop()
        while ans and is_empty(ans[0]): ans.pop(0)
        if ans: strip_prefix(ans[0],ARE)
        card=soup.new_tag("div",attrs={"class":"qa"})
        if qid: card["id"]=qid
        q=soup.new_tag("div",attrs={"class":"q"}); mk=soup.new_tag("span",attrs={"class":"mk"}); mk.string="Q"; q.append(mk)
        qt=soup.new_tag("div",attrs={"class":"qt"}); qt.append(qinner); q.append(qt); card.append(q)
        if ans:
            a=soup.new_tag("div",attrs={"class":"a"}); mk=soup.new_tag("span",attrs={"class":"mk"}); mk.string="A"; a.append(mk)
            ab=soup.new_tag("div",attrs={"class":"ab"})
            for x in ans: ab.append(x)
            a.append(ab); card.append(a)
        out.append(card)
    return "".join(str(x) for x in out)
