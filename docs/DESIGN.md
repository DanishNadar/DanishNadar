# Design notes: the Intelligent Systems Lab

## Intent

A hiring manager should know within 30 seconds who Danish is, which systems he has built, and where the evidence lives. Everything visual exists to get them to the evidence faster.

| Time on page | What they should take away | Where it comes from |
|---|---|---|
| 10 s | Name, role, "perceive · reason · act", a memorable vehicle | Hero |
| 30 s | Disciplines, three flagship systems, leadership, links to resume and portfolio | Buttons, *At a glance* table, flagship cards |
| 5 min | Architecture, design decisions, honest limits, capability evidence | Diagrams, `<details>` panels, capability matrix, design-decision log |

## Visual system

- **Palette.** Navy `#050B18` and midnight `#08162C` panels. Blue (`#35A7FF`, ice `#BFE1FF`) stands for perception, computation and research. Red (`#EF314B`, `#FF4B57`) stands for action, autonomy and real-world impact. Text is white `#F3F8FF` and steel `#9EB3CD`.
- **Type.** Inter Display ExtraBold for the name and titles, Inter for body text, JetBrains Mono for technical labels. These echo the Inter and JetBrains Mono used on danishnadar.com. The fonts are subset per SVG and embedded as WOFF data URIs (OFL licenses are in `fonts/`).
- **Panels.** Every graphic is a self-contained dark panel with a hairline border, so it reads the same on GitHub's light and dark themes. A single variant per asset keeps maintenance simple.
- **Motion.** All motion is CSS `@keyframes`: LiDAR waves, wheel spin, lane dashes, data-flow dashes and node pulses. SMIL and JavaScript are not used. The rule is that **the un-animated frame is the complete design**, because some renderers (mobile apps, social previews, reduced motion) show only that frame. Every SVG disables animation under `prefers-reduced-motion`, and the README also serves `hero-static.svg` through a `<picture>` source for that media query.
- **Vehicle.** An original fastback silhouette with a full-width light bar, flush glass and aero wheels. It has no manufacturer logo or copied body lines. The Chicago skyline (Willis, Hancock, Trump, Marina City) is abstracted and kept at low contrast.

## Information architecture

1. Hero → link buttons → one-paragraph positioning → *At a glance* table → anchor navigation
2. **Engineering Snapshot.** Projects are mapped onto Perception → Representation → Reasoning → Decision → Action, and each appears only under the stages it implements.
3. **Flagship Systems.** TalonCV, Morph and OBSERV-E each get a card, a problem / what-I-built / depth paragraph, links and an architecture diagram. TalonCV's diagram is shown open; the others sit in `<details>` panels.
4. **Work by discipline.** Autonomy, Applied AI and Infrastructure, with no project repeated across categories.
5. **Capability matrix.** Every skill names the project that demonstrates it, with no self-rating bars.
6. **Beyond the Code.** Leadership cards, an experience table and education.
7. **Trajectory.** A timeline using dates from danishnadar.com, Illinois Tech and the repos.
8. **Live Engineering Signal.** The weekly design decision, the contribution map and recently active repos, all automated.

## Accessibility

- Every SVG has `role="img"`, a `<title>` and a `<desc>`. Every README image has descriptive alt text that carries the same information as the graphic.
- The hero meta text is 12 px at a 1200 px viewBox. It is decorative; the same facts appear as real text directly below the hero.
- Nothing flashes, and the fastest loop (wheel spin) only changes rotation.
