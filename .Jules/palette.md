## 2025-05-15 - [A11y Redundancy]
**Learning:** Adding `aria-label` to form inputs that already have associated `<label>` elements via `htmlFor` is redundant and can cause screen readers to announce the label twice.
**Action:** Trust semantic `<label>` elements and only use `aria-label` for icon-only buttons or elements without visible labels.
