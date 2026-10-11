import json,sys,collections
d=json.load(open(sys.argv[1]+".json")); B=d["blocks"]
def V(i):
    b=B.get(i,{}).get("value",{}); return b.get("value",b)
def txt(prop):
    out=""
    for seg in prop or []:
        out+=seg[0]
    return out
types=collections.Counter()
def walk(i,depth=0):
    v=V(i); t=v.get("type"); types[t]+=1
    title=txt(v.get("properties",{}).get("title"))
    print("  "*depth+f"[{t}] {title[:110]}")
    for c in v.get("content",[]) or []: walk(c,depth+1)
walk(d["root"])
print(types,file=sys.stderr)
