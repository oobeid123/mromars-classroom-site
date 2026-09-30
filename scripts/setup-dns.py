#!/usr/bin/env python3
"""Point mromars-classroom.com at GitHub Pages. Idempotent: run it as often as you like.

    scripts/setup-dns.py --dry-run     # say what would change
    scripts/setup-dns.py               # make it so

Token: ~/.config/cloudflare/dns-token (Zone:DNS:Edit + Zone:Zone:Read on this zone).

Two things this gets right, both learned the hard way on haanasewing.com:

  * Every record stays DNS-only (grey cloud). Proxying through Cloudflare stops
    GitHub issuing the certificate, and HTTPS then silently never comes up.
  * /user/tokens/verify rejects a zone-scoped token with "Invalid API Token" even
    when the token is perfectly good. Do not use it as a health check -- ask for
    the zone instead, which is what this script does.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

ZONE_NAME = "mromars-classroom.com"
TOKEN_PATH = os.path.expanduser("~/.config/cloudflare/dns-token")
API = "https://api.cloudflare.com/client/v4"

# GitHub Pages' apex addresses; www is a CNAME at the user's github.io host.
WANT = [("A", "@", ip) for ip in ("185.199.108.153", "185.199.109.153",
                                  "185.199.110.153", "185.199.111.153")] + \
       [("AAAA", "@", ip) for ip in ("2606:50c0:8000::153", "2606:50c0:8001::153",
                                     "2606:50c0:8002::153", "2606:50c0:8003::153")] + \
       [("CNAME", "www", "oobeid123.github.io")]


def call(path, method="GET", body=None):
    token = open(TOKEN_PATH).read().strip()
    req = urllib.request.Request(
        API + path, method=method,
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        out = json.loads(urllib.request.urlopen(req, timeout=20).read())
    except urllib.error.HTTPError as e:
        out = json.loads(e.read() or "{}")
    if not out.get("success"):
        sys.exit(f"cloudflare: {json.dumps(out.get('errors'))}")
    return out["result"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    zones = call(f"/zones?name={ZONE_NAME}")
    if not zones:
        sys.exit(f"no zone {ZONE_NAME} on this token")
    zone = zones[0]["id"]
    have = call(f"/zones/{zone}/dns_records?per_page=100")

    for rtype, name, content in WANT:
        fqdn = ZONE_NAME if name == "@" else f"{name}.{ZONE_NAME}"
        match = [r for r in have if r["type"] == rtype and r["name"] == fqdn
                 and r["content"].rstrip(".") == content]
        if match:
            r = match[0]
            if r["proxied"]:
                print(f"  un-proxy {rtype:5s} {fqdn} -> {content}   (grey cloud, or no certificate)")
                if not a.dry_run:
                    call(f"/zones/{zone}/dns_records/{r['id']}", "PATCH", {"proxied": False})
            else:
                print(f"  ok       {rtype:5s} {fqdn} -> {content}")
            continue
        print(f"  create   {rtype:5s} {fqdn} -> {content}")
        if not a.dry_run:
            call(f"/zones/{zone}/dns_records", "POST",
                 {"type": rtype, "name": fqdn, "content": content,
                  "ttl": 1, "proxied": False,
                  "comment": "GitHub Pages - must stay DNS-only"})

    wanted = {(t, ZONE_NAME if n == "@" else f"{n}.{ZONE_NAME}", c) for t, n, c in WANT}
    for r in have:
        if r["type"] in ("A", "AAAA", "CNAME") and \
           (r["type"], r["name"], r["content"].rstrip(".")) not in wanted:
            print(f"  ! extra  {r['type']:5s} {r['name']} -> {r['content']}  (left alone; remove by hand if wrong)")
    print("done" + (" (dry run, nothing changed)" if a.dry_run else ""))


if __name__ == "__main__":
    main()
