#!/usr/bin/env python3
import argparse, json, os, re
from pathlib import Path
from urllib.parse import urlparse
import yaml
from playwright.sync_api import sync_playwright

STATE=Path("data/account-ledger.json")
CAPTCHA=("captcha","recaptcha","hcaptcha","turnstile")
VERIFY=("verify","verification","confirm your email","activation link","check your email")

def host(u): return urlparse(u).netloc.lower().removeprefix("www.")
def load():
    return json.loads(STATE.read_text()) if STATE.exists() else {}
def save(d):
    STATE.parent.mkdir(exist_ok=True); STATE.write_text(json.dumps(d,indent=2,sort_keys=True))
def profile():
    with open("impilo.yaml",encoding="utf-8") as f:return yaml.safe_load(f)["business"]
def fill_first(page, selectors, value):
    for s in selectors:
        x=page.locator(s)
        if x.count():
            try:x.first.fill(value); return True
            except:pass
    return False

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("url"); ap.add_argument("--commit",action="store_true")
    a=ap.parse_args(); p=profile(); d=load(); h=host(a.url)
    if d.get(h,{}).get("status") in {"ACTIVE","VERIFICATION_PENDING"}:
        print("Account state:",d[h]["status"]); return
    password=os.environ.get("DIRECTBOT_ACCOUNT_PASSWORD")
    if a.commit and not password:
        raise SystemExit("DIRECTBOT_ACCOUNT_PASSWORD secret is required for registration")
    with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True); page=b.new_page()
        page.goto(a.url,wait_until="domcontentloaded",timeout=45000)
        # Insly: homepage is discovery; follow the explicit free listing CTA first.
        if h == "insly.co.za":
            moved=False
            for label in ["List Your Organization","Add business","Claim your business","Start getting customers"]:
                link=page.get_by_role("link",name=re.compile(label,re.I))
                if link.count():
                    link.first.click()
                    page.wait_for_load_state("domcontentloaded")
                    moved=True
                    break
            if not moved:
                d[h]={"status":"MANUAL_REVIEW","url":a.url,"reason":"Insly free-listing CTA not found"}
                save(d); print("MANUAL_REVIEW: Insly listing CTA not found"); raise SystemExit(2)
        body=page.locator("body").inner_text().lower()
        if any(x in body for x in CAPTCHA):
            d[h]={"status":"MANUAL_CAPTCHA","url":a.url}; save(d); print("STOP: CAPTCHA"); return
        fill_first(page,['input[type="email"]','input[name*="email" i]'],p["email"])
        fill_first(page,['input[name*="business" i]','input[name*="company" i]','input[name*="name" i]'],p["name"])
        if password:
            for x in page.locator('input[type="password"]').all():
                try:x.fill(password)
                except:pass
        Path("output").mkdir(exist_ok=True)
        page.screenshot(path="output/account-preview.png",full_page=True)
        if not a.commit:
            d[h]={"status":"REGISTRATION_PREVIEW","url":a.url}; save(d)
            print("Preview prepared; no account created."); return
        btn=None
        for label in ["Register","Sign Up","Create Account","Create an Account"]:
            x=page.get_by_role("button",name=re.compile(label,re.I))
            if x.count():btn=x.first;break
        if not btn:
            d[h]={"status":"MANUAL_REVIEW","url":a.url,"reason":"no unambiguous registration button"};save(d);print("MANUAL_REVIEW: no unambiguous registration button"); raise SystemExit(2)
        btn.click();page.wait_for_timeout(3000)
        text=page.locator("body").inner_text().lower()
        status="VERIFICATION_PENDING" if any(x in text for x in VERIFY) else "REGISTERED"
        d[h]={"status":status,"url":a.url};save(d);print(status)
        b.close()
if __name__=="__main__":main()
