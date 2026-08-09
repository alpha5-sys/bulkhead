# Store listing copy

Ready to paste. Same channel order as Conduit — Gumroad is the checkout, the others
are trimmed from the same text.

**This product's position is different from Conduit's, and the copy reflects it.**
Cables were an unserved category, so that listing had to argue the problem existed.
Panelling is a *proven* category with a 615-review incumbent, so this listing must
not explain what a greebler is. It has to say why this one's output looks right.

---

## Gumroad

### Title
`Bulkhead — Panel & Greeble Generator for Blender`

### Price
**$26.** Launch week **$18** with code `FIRSTHUNDRED`, capped at 100 uses.

A little above Conduit's $24: the category has a demonstrated willingness to pay, and
pricing below the incumbent invites the read that it is the lesser tool.

### Summary line
> Hull plating that looks designed, not random. Hierarchical panels, continuous seam
> runs, machined height steps — one button, then reroll until it's right.

### Description

**Most greeblers subdivide into a grid and randomly extrude cells.**

That is why their output reads as noise. Four things are missing, and all four are
what make real plating look manufactured:

**Hierarchy.** Real plating is a few large plates, more medium ones, many small ones.
A grid gives you one size, everywhere. Bulkhead builds the layout by recursive
bisection with a per-plate chance of stopping early, so the size distribution is a
property of the algorithm — not something you fake afterwards by deleting edges.

**Seams that run.** Panel lines should travel across a surface in continuous straight
runs. Bisection gives that automatically: every seam spans its whole region, so lines
never jitter, stop halfway, or wander.

**Proportion.** No slivers, no needles. Every plate is split along its longer side, at
a position chosen from the range that satisfies the minimum-size and maximum-aspect
limits simultaneously. Elongation is bounded, not hoped for.

**Machined heights.** Give every plate a random height and you get a skyline. Bulkhead
puts plates on a few discrete levels with most sitting flush, which is what real
armour does — and chamfers every plate edge, so the seams catch the light instead of
reading as flat tiles.

---

**Fittings.** Greebles and vents bolted onto the plates, placed on a grid inset from
the plate edge — so they never overlap each other and never straddle a seam.

**Built for rerolling.** Every setting lives in the redo panel. Press F9, nudge the
seed, and the hull re-plates instantly. Finding the layout you want is the workflow,
so it is one keystroke.

**Fast.** A 64-quad mesh plates in well under a second, producing about 30,000 faces.

**Blender 4.2+.** No dependencies, nothing to configure, 23 KB.

---

*Works on four-sided faces.* Non-quads are skipped and reported, never mangled.

*Try it first:* the [free edition](https://extensions.blender.org) has the plating,
the seams, the height steps and the chamfers. This one adds the fittings and vents.

*Already running the free edition?* Remove it before installing this one — both register the same operators, so Blender errors if they sit side by side. Your scenes are unaffected.

*Licence:* GPL-3.0-or-later — a Blender add-on links Blender's Python API, so it has
to be. You are buying the build, the updates and the support.

### Tags
`blender` `blender addon` `greeble` `hard surface` `sci-fi` `panels` `kitbash` `3d`
`hull` `spaceship`

---

## extensions.blender.org (free edition)

Tagline (under 64 chars):
`Hierarchical hull plating with aligned seams`

Description — no selling, no upgrade nag; reviewers reject both:

> Plates a mesh's four-sided faces with hierarchical hull panelling. Plates are laid
> out by recursive bisection, so panel lines run in continuous aligned seams and the
> layout contains a mix of large and small plates rather than a uniform grid. Plate
> elongation is bounded, heights land on a configurable number of discrete levels,
> and plate edges are chamfered.
>
> Select faces in Edit Mode, return to Object Mode, then Object menu → Panel Surface,
> or the Bulkhead tab in the sidebar. With nothing selected, all quads are plated.
> Settings are in the redo panel (F9), including a seed for rerolling the layout.

---

## Launch posts

### r/blender

Title: `Most greeble generators look random. I worked out why, and fixed it`

> Grid-and-random-extrude is how most greeblers work, and it always looked off to me.
> I think it comes down to four things real plating has that a grid can't produce:
> hierarchy (a mix of plate sizes), seams that run in continuous lines, bounded
> proportions so nothing turns into a sliver, and heights on a few machined levels
> instead of one per plate.
>
> So I built the layout with recursive bisection instead. Hierarchy and aligned seams
> fall straight out of it. Then chamfered every plate edge, which turned out to be
> the single biggest difference between "floor tiles" and "hull".
>
> Free edition [link] — plating, seams, height steps, chamfers. Fittings and vents are
> in the paid one.
>
> Happy to go into the layout algorithm if anyone's interested.

### X

> Most Blender greeble addons subdivide into a grid and randomly extrude.
>
> That's why the output looks random — a grid can't produce hierarchy, and hierarchy
> is most of what makes plating read as designed.
>
> So I built it with recursive bisection instead. 🧵

Thread: 2/ the four properties a grid can't give you · 3/ why chamfering every plate
edge mattered more than anything else · 4/ free vs paid, with the link.

---

## Cross-selling

Bulkhead and [Conduit](../../conduit) are the same buyer: hard-surface and sci-fi
artists. Each listing should mention the other once, at the bottom, as "also by" —
not as a bundle. Bundle them only once both have reviews, or the bundle reads as two
unproven products propping each other up.
