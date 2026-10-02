#!/usr/bin/env python3
import yaml
REQUIRED=["name","phone","email","website","city","province","country","description"]
OPTIONAL_FOR_ADVANCED=["street_address","postal_code","latitude","longitude","contact_person","business_hours"]
with open("impilo.yaml",encoding="utf-8") as f:p=yaml.safe_load(f)["business"]
missing=[k for k in REQUIRED if not p.get(k)]
advanced=[k for k in OPTIONAL_FOR_ADVANCED if not p.get(k)]
print("Core profile:", "OK" if not missing else "MISSING "+", ".join(missing))
print("Advanced directory fields still needed:", ", ".join(advanced) if advanced else "none")
raise SystemExit(1 if missing else 0)
