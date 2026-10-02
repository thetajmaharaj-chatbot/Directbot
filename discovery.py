#!/usr/bin/env python3
import json, re, time
from pathlib import Path
from urllib.parse import quote, urlparse
import requests
from bs4 import BeautifulSoup

UA="Mozilla/5.0 (compatible; Directbot/2.0; +https://impilodrilling.co.za)"
TOWNS=["Port Shepstone","Shelly Beach","Margate","Uvongo","Ramsgate","Hibberdene","Scottburgh","Port Edward","Harding","Kokstad","Ugu","KwaZulu-Natal"]
SERVICES=["borehole drilling","drilling contractor","water services","pump installation","water purification"]
PHRASES=['"add your business"','"submit listing"','"free business listing"','"business directory"']

def host(u): return urlparse(u).netloc.lower().removeprefix("www.")
def google_html(q):
    u="https://www.google.com/search?q="+quote(q)+"&num=20"
    r=requests.get(u,headers={"User-Agent":UA},timeout=20); r.raise_for_status()
    return r.text

def extract(html):
    soup=BeautifulSoup(html,"html.parser"); out=[]
    for a in soup.select("a[href]"):
        href=a.get("href","")
        m=re.search(r"/url\?q=(https?://[^&]+)",href)
        if m: href=m.group(1)
        if href.startswith("http") and "google." not in host(href):
            out.append(href)
    return out

def main():
    state=Path("data/discovered.json"); state.parent.mkdir(exist_ok=True)
    old=json.loads(state.read_text()) if state.exists() else []
    byhost={host(x["url"]):x for x in old}
    for town in TOWNS:
        for phrase in PHRASES:
            q=f'{phrase} "{town}" South Africa'
            try:
                for u in extract(google_html(q)):
                    h=host(u)
                    if h and h not in byhost:
                        byhost[h]={"url":u,"host":h,"query":q,"status":"NEW"}
                time.sleep(3)
            except Exception as e: print("discovery error",q,e)
    rows=sorted(byhost.values(),key=lambda x:x["host"])
    state.write_text(json.dumps(rows,indent=2))
    print("Known candidate directory domains:",len(rows))
if __name__=="__main__": main()
