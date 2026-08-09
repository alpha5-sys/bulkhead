# Launch checklist — Bulkhead

The account and payment steps are identical to Conduit's, so they are not repeated
here: follow `../conduit/docs/LAUNCH.md` §0–§2 once, and both products sell through
the same Gumroad account and the same PayPal payout.

**Stripe does not support Fiji** — that constraint drives everything, and it is
explained there.

## What is different for this product

### Ship it second, not simultaneously

Conduit goes first. Two reasons:

1. **r/blender tolerates one self-promotion post at a time.** Two launches in the
   same week from the same account reads as marketing and gets both throttled. Leave
   two to three weeks between them.
2. **The first launch is the experiment.** Conduit tests an *unserved* category, where
   the risk is that nobody wants it. Bulkhead tests a *proven* one, where the risk is
   the incumbent. Whichever converts better tells you where product #3 goes — but only
   if they are not confounded by launching together.

### The pitch is comparative, not explanatory

For Conduit the listing has to argue that the problem exists. Here it must not: with
a 615-review incumbent, buyers know what a greebler is. The copy in
`marketing/LISTING.md` therefore leads with *why this output looks right* — hierarchy,
running seams, bounded proportion, machined heights — and never explains the category.

### Price

**$26**, launch week **$18**. Slightly above Conduit's $24: this category has
demonstrated willingness to pay, and pricing under the incumbent invites the read
that it is the lesser tool.

## Steps

1. **Gumroad** — new product in the existing account. Upload
   `build/dist/bulkhead-1.0.0.zip`, copy from `marketing/LISTING.md`, cover from
   `build/demo/cover.png`, gallery from `build/verify/`.
2. **GitHub** — `gh` is authenticated as **alpha5-sys**. I have not run this;
   creating a public repo is publishing.
   ```bash
   cd bulkhead
   gh repo create bulkhead --public --source=. --push
   gh release create v1.0.0 build/dist/bulkhead_free-1.0.0.zip \
     --title "Bulkhead 1.0.0" --notes "Free edition. Drag the zip into Blender 4.2+."
   ```
   Then put the real URL into `addon/bulkhead/blender_manifest.toml` and the Gumroad
   link into `README.md`, and rebuild.
3. **extensions.blender.org** — upload `bulkhead_free-1.0.0.zip`. Review takes days.
   There are only ~972 add-ons on that platform and it is browsable from inside every
   Blender install; the free listing is the asset that compounds.
4. **Social** — only once the free listing is approved, so the link works when the
   traffic lands. r/blender first, Tue–Thu 14:00–17:00 UTC, and answer every comment
   for the first three hours.
5. **Superhive** — once Gumroad has a sale to point at.

## What is already done

| | |
|---|---|
| Layout algorithm, add-on, both editions | ✅ 35 unit tests, 19 headless integration checks |
| Packaged | ✅ both pass `blender --command extension validate` |
| Free edition gating proved on the built zip | ✅ `tools/verify_dist.py` |
| Store copy, all channels | ✅ `marketing/LISTING.md` |
| Renders and demo loop | ✅ `build/verify/`, `build/demo/` |

## Honest read

Better odds than Conduit on demand, worse on competition.

The category is **proven** — Sci-Fi Panel Generator sits at 4.9 with 615 reviews, and
at a 1–5% review rate that is somewhere in the low tens of thousands of units. Nobody
has to be convinced the problem is real.

The flip side is that a good incumbent exists, and "mine looks better" is a much
weaker wedge than "nothing else does this at all." The comparison table is doing the
selling here, so it has to survive contact with someone who owns the incumbent and
will check. Everything claimed in it is demonstrable from the renders.

Judge this one on **conversion rate**, not downloads — unlike Conduit, traffic is not
the question, preference is. If the free edition gets installs but the paid does not
convert, the fittings are not worth $26 to this audience and the split should move
(collision-style, put something structural behind the paywall instead of accessories).
