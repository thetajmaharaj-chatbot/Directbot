#!/usr/bin/env python3
import argparse, re, yaml
from playwright.sync_api import sync_playwright
from ledger import seen, record

CAPTCHA=("captcha","recaptcha","hcaptcha","turnstile")
PAYMENT=("checkout","credit card","payment","pay now","subscribe")
VERIFY=("verify your email","email verification","confirmation email")

def profile():
    with open("impilo.yaml",encoding="utf-8") as f:return yaml.safe_load(f)["business"]

def fill(page,p):
    mappings=[
      (["business name","company name","listing title","title"],p["name"]),
      (["email","e-mail"],p["email"]),
      (["phone","telephone","mobile","contact number"],p["phone"]),
      (["website","web site","url"],p["website"]),
      (["city","town"],p["city"]),
      (["province","state"],p["province"]),
      (["description","about","business description"],p["description"]),
    ]
    count=0
    for el in page.locator("input, textarea").all():
        try:
            meta=" ".join([el.get_attribute("name") or "",el.get_attribute("id") or "",el.get_attribute("placeholder") or "",el.get_attribute("aria-label") or ""]).lower()
            if el.input_value(): continue
            for keys,val in mappings:
                if any(k in meta for k in keys):
                    el.fill(val); count+=1; break
        except: pass
    return count

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("url"); ap.add_argument("--commit",action="store_true")
    a=ap.parse_args()
    if seen(a.url): print("SKIP duplicate:",a.url); return
    p=profile()
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True); page=browser.new_page()
        page.goto(a.url,wait_until="domcontentloaded",timeout=45000)
        body=page.locator("body").inner_text().lower()
        if any(x in body for x in CAPTCHA):
            record(a.url,"MANUAL_CAPTCHA"); print("STOP: CAPTCHA"); return
        if any(x in body for x in PAYMENT):
            record(a.url,"PAYMENT_REVIEW"); print("STOP: payment/package choice"); return
        n=fill(page,p)
        page.screenshot(path="output/submission-preview.png",full_page=True)
        if not a.commit:
            record(a.url,"PREVIEWED",f"filled {n} fields")
            print(f"PREVIEW ONLY: filled {n} fields; use --commit only after adapter review.")
            return
        buttons=page.get_by_role("button")
        submit=None
        for label in ["Submit Listing","Submit","Add Listing","Create Listing"]:
            x=page.get_by_role("button",name=re.compile(label,re.I))
            if x.count(): submit=x.first; break
        if not submit:
            record(a.url,"MANUAL_REVIEW","no unambiguous submit button"); print("STOP: no safe submit control"); return
        submit.click(); page.wait_for_timeout(3000)
        body=page.locator("body").inner_text().lower()
        status="PENDING_APPROVAL" if any(x in body for x in VERIFY) else "SUBMITTED"
        record(a.url,status,"automated self-service submission")
        print(status)
        browser.close()
if __name__=="__main__": main()
