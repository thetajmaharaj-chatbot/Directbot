#!/usr/bin/env python3
import csv, json, os, re, time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import requests, yaml
from bs4 import BeautifulSoup

UA = "Directbot/1.0 (+https://impilodrilling.co.za; business listing assistant)"
TIMEOUT = 20

def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

def classify(html, url):
    text = norm(BeautifulSoup(html, "html.parser").get_text(" ", strip=True))
    signals = {
        "submission": ["add listing","submit listing","add your business","list your business","business listing","create listing"],
        "free": ["free listing","list for free","advertise for free","r 0 00","free advertising"],
        "captcha": ["captcha","recaptcha","hcaptcha","turnstile"],
        "login": ["login","sign in","register","create account"],
        "paid": ["premium","featured listing","paid listing","subscription"],
    }
    out = {k:any(x in text for x in v) for k,v in signals.items()}
    score = 0
    score += 45 if out["submission"] else 0
    score += 25 if out["free"] else 0
    score -= 15 if out["captcha"] else 0
    score -= 5 if out["login"] else 0
    out["score"] = max(0,min(100,score))
    out["url"] = url
    return out

def inspect(url):
    try:
        r=requests.get(url,headers={"User-Agent":UA},timeout=TIMEOUT,allow_redirects=True)
        r.raise_for_status()
        c=classify(r.text,r.url)
        c.update({"ok":True,"status_code":r.status_code})
        return c
    except Exception as e:
        return {"ok":False,"url":url,"error":str(e),"score":0}

def candidate_links(html, base):
    soup=BeautifulSoup(html,"html.parser")
    keys=("add","submit","listing","directory","business")
    seen=set()
    for a in soup.find_all("a",href=True):
        href=urljoin(base,a["href"])
        label=norm(a.get_text(" ",strip=True)+" "+href)
        if href.startswith("http") and any(k in label for k in keys):
            host=urlparse(href).netloc.lower()
            if host and href not in seen:
                seen.add(href); yield href

def discover_from_seed(url, limit=20):
    found=[]
    try:
        r=requests.get(url,headers={"User-Agent":UA},timeout=TIMEOUT)
        for link in candidate_links(r.text,r.url):
            found.append(link)
            if len(found)>=limit: break
    except Exception:
        pass
    return found

def write_csv(rows,path):
    fields=["name","region","url","priority","ok","status_code","score","submission","free","captcha","login","paid","action","error"]
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(rows)

def main():
    cfg=load_yaml("impilo.yaml")["business"]
    targets=load_yaml("targets.yaml")["targets"]
    os.makedirs("output",exist_ok=True)
    rows=[]
    for t in sorted(targets,key=lambda x:x.get("priority",0),reverse=True):
        result=inspect(t["url"])
        row={**t,**result}
        if not result.get("ok"):
            action="RETRY"
        elif result.get("captcha"):
            action="MANUAL_CAPTCHA"
        elif result.get("submission") and result.get("free"):
            action="READY_TO_SUBMIT"
        elif result.get("submission"):
            action="REVIEW_PACKAGE"
        else:
            action="MANUAL_REVIEW"
        row["action"]=action
        rows.append(row)
        print(f'{t["name"]}: {action} score={row.get("score",0)}')
        time.sleep(1)

    stamp=datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    write_csv(rows,f"output/directory-audit-{stamp}.csv")
    with open("output/latest.json","w",encoding="utf-8") as f:
        json.dump({"generated_at":stamp,"business":cfg,"targets":rows},f,indent=2)

    ready=sum(r["action"]=="READY_TO_SUBMIT" for r in rows)
    print(f"\nAudit complete: {len(rows)} targets, {ready} ready for free submission.")
    print("Directbot intentionally does not bypass CAPTCHA, email verification, login security, or paid checkout.")

if __name__=="__main__":
    main()
