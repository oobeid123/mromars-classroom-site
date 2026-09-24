# mromars-classroom.com

The public storefront for **Mr. Omar's Classroom**. Static: HTML plus cached
images, served by GitHub Pages, no server and no build step on this side.

⛔ **Do not edit `index.html` here.** It is generated. The source is
`~/mromars-store/toybox/template.html`, and prices come from the workshop
(`classroom-admin`, port 8777), not from this repo.

```bash
cd ~/mromars-store/toybox
python3 build.py 84 --split ~/mromars-classroom-site   # regenerate
cd ~/mromars-classroom-site && ./deploy.sh             # commit, push, live
```

`404.html` is a copy of the page, so a wrong URL still lands somewhere useful
(the app routes on the hash).

Public on purpose: GitHub Pages only serves a free site from a public repo, and
nothing sensitive is here. Prices shown are public anyway; costs, orders,
customers and filament live only in the workshop, which is not on the internet.
