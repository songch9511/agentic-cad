# GD&T Drawing Readability Contract

## Trigger

Use this rule when a CAD-to-drawing agent generates an engineering drawing, GD&T proposal, inspection drawing, or manufacturing drawing preview.

## Failure Pattern

A generated drawing should not pass if it only looks like a diagram with GD&T labels sprinkled on top. The drawing must preserve the information structure engineers expect from an ASME/ISO-style manufacturing drawing.

Common failure signals:

- Feature control frames are detached from the controlled feature or float without a leader.
- Datum symbols are shown but the datum feature or datum axis is ambiguous.
- Basic dimensions are missing for toleranced feature locations.
- Hole pattern dimensions and position tolerances are not grouped as a pattern.
- Orthographic/section/detail views overlap or are not visually aligned.
- Title block, revision/status, units, scale, standard, and notes are missing.
- Generated preview crops callouts or places text over geometry.
- Drawing claims to be production GD&T when it is only an auto-proposed review draft.

## Minimum Pass Criteria

A demo-quality CAD-to-GD&T drawing should include:

- Sheet border, zone grid, title block, revision/status, units, scale, and standard/style.
- At least one primary section or orthographic view that explains the part axis and datum structure.
- Datum feature symbols connected to real surfaces or axes.
- Basic dimensions in boxes for hole pattern location or spacing.
- Feature control frames connected by leader lines to the controlled feature or pattern.
- Pattern callouts such as `4X DIA 5 THRU` paired with a position tolerance frame.
- A datum reference table that explains A/B/C intent.
- An explicit `AUTO-PROPOSED / ENGINEERING REVIEW REQUIRED` status if design intent was inferred.
- Visual QA showing no cropped FCFs, no title/callout overlap, and readable text at full-sheet scale.

## Recommended Repair

Prefer a spec-driven drawing generator:

1. Build a drawing intent JSON with views, datums, features, basic dimensions, FCFs, notes, and title block fields.
2. Generate SVG/PDF preview from the intent JSON.
3. Run visual QA on the preview before exporting DXF/PDF.
4. Keep DXF as an exchange artifact; use SVG/PDF for the product demo preview unless the viewer fully supports dimensions and text entities.

## Benchmark Hooks

Automated checks can be shallow but useful:

- Required strings exist: `DATUM`, `BASIC`, `POS`, `DIA`, `UNITS`, `REV`, `AUTO-PROPOSED`.
- At least three datum IDs are present.
- At least three FCF table rows are present.
- Preview dimensions are landscape and large enough for readable drawing review.
- Rasterized preview has no black-only render failure and no elements outside the sheet border.
