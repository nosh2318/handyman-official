import json,urllib.request,urllib.error,sys,uuid
def pid(s):
    h=s[-32:]; return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"
def post(ep,b):
    req=urllib.request.Request("https://plump-cap-ebe.notion.site/api/v3/"+ep,data=json.dumps(b).encode(),headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"})
    import time
    for i in range(8):
        try: return json.loads(urllib.request.urlopen(req,timeout=60).read())
        except urllib.error.HTTPError as e:
            if e.code==429 and i<7: time.sleep(10*(i+1)); continue
            print("FAIL",ep,e.code,str(b)[:200],file=sys.stderr); return {"recordMap":{},"cursor":{"stack":[]}}
def load(page):
    blocks={}; cursor={"stack":[]}; chunk=0
    while True:
        r=post("loadPageChunk",{"pageId":page,"limit":300,"cursor":cursor,"chunkNumber":chunk,"verticalColumns":False})
        for k,v in r["recordMap"].get("block",{}).items(): blocks[k]=v
        cursor=r.get("cursor",{"stack":[]})
        if not cursor.get("stack"): break
        chunk+=1
    # fetch missing children
    for _ in range(10):
        missing=set()
        for b in list(blocks.values()):
            val=b.get("value",{}); val=val.get("value",val)
            for c in val.get("content",[]) or []:
                if c not in blocks: missing.add(c)
        if not missing: break
        r=post("syncRecordValues",{"requests":[{"pointer":{"table":"block","id":m},"version":-1} for m in list(missing)[:200]]})
        for k,v in r["recordMap"].get("block",{}).items(): blocks[k]=v
    return blocks
name,slug=sys.argv[1],sys.argv[2]
b=load(pid(slug))
json.dump({"root":pid(slug),"blocks":b},open(name+".json","w"),ensure_ascii=False)
print(name,len(b))
