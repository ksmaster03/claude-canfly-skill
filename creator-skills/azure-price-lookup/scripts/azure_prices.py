# Query the public Azure Retail Prices API (no auth) and print price rows.
# usage:
#   python -I azure_prices.py vm   <region> <armSkuName...>     Linux VM: pay-as-you-go + 1y/3y reservation (per-month equivalent)
#   python -I azure_prices.py disk <region> <skuName...>        managed disks, e.g. "P10 LRS" "E10 LRS"
#   python -I azure_prices.py filter "<OData $filter>"           raw rows, e.g. "armRegionName eq 'southeastasia' and serviceName eq 'Backup'"
import sys, json, urllib.request, urllib.parse

BASE = "https://prices.azure.com/api/retail/prices?"


def query(flt):
    url, out = BASE + urllib.parse.urlencode({"$filter": flt}), []
    while url:
        d = json.load(urllib.request.urlopen(url, timeout=60))
        out += d["Items"]
        url = d.get("NextPageLink")
    return out


def show(it):
    term = it.get("reservationTerm") or ""
    extra = ""
    if it["type"] == "Reservation":  # retailPrice is the total for the whole term even though unitOfMeasure says "1 Hour"
        months = 12 if term.startswith("1") else 36
        extra = f" (= {it['retailPrice'] / months:.2f}/month)"
    print(f"{it['armRegionName']} | {it['skuName']} | {it['meterName']} | {it['type']} {term} | "
          f"{it['retailPrice']} {it['unitOfMeasure']}{extra} | {it['productName']} | serviceName={it['serviceName']}")


cmd = sys.argv[1]
if cmd == "vm":
    region = sys.argv[2]
    for sku in sys.argv[3:]:
        rows = query(f"armRegionName eq '{region}' and armSkuName eq '{sku}' and serviceName eq 'Virtual Machines'")
        rows = [r for r in rows if r["productName"].startswith("Virtual Machines")      # drops "... Cloud Services" rows
                and "Windows" not in r["productName"]
                and "Spot" not in r["skuName"] and "Low Priority" not in r["skuName"]]
        if not rows:
            print(f"{region} | {sku} | NOT FOUND")
        for r in rows:
            show(r)
elif cmd == "disk":
    region = sys.argv[2]
    names = " or ".join(f"skuName eq '{n}'" for n in sys.argv[3:])
    for r in query(f"armRegionName eq '{region}' and serviceName eq 'Storage' and ({names})"):
        if "Managed Disks" in r["productName"]:                                       # drops "Premium Page Blob" duplicates
            show(r)
elif cmd == "filter":
    rows = query(sys.argv[2])
    print(f"{len(rows)} rows")
    for r in rows:
        show(r)
else:
    sys.exit("commands: vm | disk | filter")
