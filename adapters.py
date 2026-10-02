import re
from urllib.parse import urlparse

def domain(url): return urlparse(url).netloc.lower().removeprefix("www.")

def choose(page, selector, text):
    try:
        page.locator(selector).select_option(label=re.compile(text,re.I)); return True
    except: return False

def thebusinessdirectory(page,p):
    """Free package adapter. Stops before submit if required physical-address fields are missing."""
    body=page.locator("body").inner_text().lower()
    if "free listing" not in body: return {"ready":False,"reason":"free package unavailable"}
    # Explicitly select the zero-cost package where possible.
    radios=page.locator('input[type="radio"]')
    for i in range(radios.count()):
        r=radios.nth(i)
        try:
            value=(r.get_attribute("value") or "")+" "+(r.get_attribute("id") or "")
            label=page.locator(f'label[for="{r.get_attribute("id")}"]').inner_text() if r.get_attribute("id") else ""
            if "free" in (value+" "+label).lower(): r.check(); break
        except: pass
    # This directory requires a precise street address, postal code and coordinates.
    required=("street_address","postal_code","latitude","longitude")
    missing=[x for x in required if not p.get(x)]
    if missing: return {"ready":False,"reason":"missing required profile fields: "+", ".join(missing)}
    return {"ready":True,"reason":"free package selected"}

ADAPTERS={"thebusinessdirectory.co.za":thebusinessdirectory}

def run_adapter(page,url,p):
    fn=ADAPTERS.get(domain(url))
    return fn(page,p) if fn else {"ready":True,"reason":"generic adapter"}
