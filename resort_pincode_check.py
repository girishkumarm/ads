#!/usr/bin/env python3
"""Resort campaign — full pincode performance audit (April 2026 + last 30d).
Identifies new pincodes wasting money since the Apr 26 optimization."""
import os
if os.path.exists(os.path.expanduser("~/Library")):
    import ssl, urllib3, requests
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _o = requests.Session.request
    def _n(self, m, u, **k): k["verify"]=False; return _o(self, m, u, **k)
    requests.Session.request = _n
    os.environ["REQUESTS_CA_BUNDLE"] = ""

from ads_api import load_config, google_gaql

CAMP_ID = "21740834372"
cfg = load_config()


def fetch_pincode_perf(date_clause):
    """Pull user_location_view by pincode."""
    q = f"""SELECT campaign.id, segments.geo_target_postal_code,
                   metrics.clicks, metrics.impressions, metrics.cost_micros,
                   metrics.conversions, metrics.conversions_value
            FROM user_location_view
            WHERE campaign.id = {CAMP_ID}
              AND {date_clause}"""
    rows = []
    for r in google_gaql(cfg, q):
        m = r.get("metrics", {})
        clk = int(m.get("clicks",0))
        impr = int(m.get("impressions",0))
        cost = int(m.get("costMicros",0))/1e6
        conv = float(m.get("conversions",0))
        gid_full = r.get("segments",{}).get("geoTargetPostalCode","")
        if not gid_full or impr == 0: continue
        rows.append({
            "gid": gid_full.split("/")[-1],
            "clicks": clk, "impr": impr, "cost": cost, "conv": conv,
            "ctr": clk/impr*100 if impr else 0,
            "cvr": conv/clk*100 if clk else 0,
            "cpa": cost/conv if conv else 0,
        })
    return rows


def lookup_pincodes(gids):
    """gid -> pincode name lookup via geo_target_constant."""
    lookup = {}
    ids = list(set(gids))
    for i in range(0, len(ids), 50):
        chunk = ids[i:i+50]
        in_clause = ",".join(f"'geoTargetConstants/{g}'" for g in chunk)
        rq = f"""SELECT geo_target_constant.id, geo_target_constant.name,
                       geo_target_constant.canonical_name
                 FROM geo_target_constant
                 WHERE geo_target_constant.resource_name IN ({in_clause})"""
        for r in google_gaql(cfg, rq):
            gtc = r["geoTargetConstant"]
            lookup[str(gtc["id"])] = {
                "pin": gtc.get("name",""),
                "canonical": gtc.get("canonicalName",""),
            }
    return lookup


def get_existing_pincode_status():
    """Pull existing campaign-level location criteria — see what's excluded / has bid mod."""
    q = f"""SELECT campaign_criterion.location.geo_target_constant,
                   campaign_criterion.negative,
                   campaign_criterion.bid_modifier,
                   campaign_criterion.status
            FROM campaign_criterion
            WHERE campaign.id = {CAMP_ID}
              AND campaign_criterion.type = 'LOCATION'
              AND campaign_criterion.status != 'REMOVED'"""
    out = {}
    for r in google_gaql(cfg, q):
        c = r["campaignCriterion"]
        gtc = c.get("location",{}).get("geoTargetConstant","")
        if not gtc: continue
        gid = gtc.split("/")[-1]
        out[gid] = {"negative": c.get("negative", False),
                    "bm": c.get("bidModifier", 1.0),
                    "status": c.get("status","")}
    return out


def print_report(label, date_clause):
    rows = fetch_pincode_perf(date_clause)
    lookup = lookup_pincodes([r["gid"] for r in rows])
    existing = get_existing_pincode_status()
    for r in rows:
        info = lookup.get(r["gid"], {})
        r["pin"] = info.get("pin", r["gid"])
        r["canonical"] = info.get("canonical", "")
        e = existing.get(r["gid"], {})
        r["status"] = ("EXCLUDED" if e.get("negative") else
                       (f"BM ×{e['bm']:.2f}" if e.get("bm") and abs(e["bm"]-1.0)>0.01 else
                        ("targeted" if e else "untargeted")))

    rows.sort(key=lambda x: x["cost"], reverse=True)

    print(f"\n{'='*85}")
    print(f"PINCODE-LEVEL — {label}")
    print(f"{'='*85}")
    print(f"Total pincodes seen: {len(rows)}")
    tot_clk  = sum(r["clicks"] for r in rows)
    tot_impr = sum(r["impr"] for r in rows)
    tot_cost = sum(r["cost"] for r in rows)
    tot_conv = sum(r["conv"] for r in rows)
    print(f"Total: {tot_impr:,} impr, {tot_clk:,} clk, {tot_conv:.0f} conv, ₹{tot_cost:,.0f} cost")

    print(f"\n--- TOP 30 PINCODES BY SPEND ---")
    print(f"{'Pin':<8} {'Impr':>6} {'Clk':>5} {'Conv':>5} {'Cost ₹':>8} {'CPA ₹':>8} {'CVR':>6} {'Status':<14} {'Verdict'}")
    for r in rows[:30]:
        cpa = f"{r['cpa']:.0f}" if r["conv"] else "—"
        v = ""
        if r["clicks"] >= 5 and r["conv"] == 0 and r["status"] == "targeted":
            v = "🚨 NEW WASTE — exclude/bid down"
        elif r["clicks"] >= 5 and r["conv"] == 0 and r["status"] == "EXCLUDED":
            v = "✅ already excluded"
        elif r["clicks"] >= 5 and r["conv"] == 0:
            v = "🟡 0 conv"
        elif r["cvr"] >= 15 and r["clicks"] >= 5 and r["status"] == "targeted":
            v = "🟢 STRONG — boost bid"
        print(f"{r['pin']:<8} {r['impr']:>6} {r['clicks']:>5} {r['conv']:>5.0f} "
              f"{r['cost']:>8.0f} {cpa:>8} {r['cvr']:>5.1f}% {r['status']:<14} {v}")

    # waste analysis
    wasters = [r for r in rows if r["conv"] == 0 and r["clicks"] >= 3 and r["status"] != "EXCLUDED"]
    wasters.sort(key=lambda x: x["cost"], reverse=True)
    waste_total = sum(r["cost"] for r in wasters)
    print(f"\n--- ZERO-CONV PINCODES (≥3 clicks, NOT yet excluded) ---")
    print(f"  {len(wasters)} pincodes wasting ₹{waste_total:,.0f}")
    for r in wasters[:25]:
        print(f"    {r['pin']:<8} {r['canonical'][:50]:<50}  "
              f"{r['clicks']:>3} clk  ₹{r['cost']:>5.0f}  status={r['status']}")

    return wasters


# Run for both windows
w_apr = print_report("APRIL 2026 (full month)", "segments.date BETWEEN '2026-04-01' AND '2026-04-30'")
w_30  = print_report("LAST 30 DAYS",            "segments.date DURING LAST_30_DAYS")
w_7   = print_report("LAST 7 DAYS",             "segments.date DURING LAST_7_DAYS")
