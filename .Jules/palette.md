## 2025-05-15 - [Dynamic Content Accessibility]
**Learning:** For dynamic content like transcriptions that appear after an async operation, using `aria-live="polite"` on the container ensures screen readers announce the new content without interrupting the user.
**Action:** Always wrap dynamically loaded results or status messages in a container with `aria-live="polite"` or `aria-live="assertive"` depending on urgency.

## 2025-05-15 - [Persona Constraints]
**Learning:** "Palette" persona has strict rules against adding new CSS classes or exceeding line limits. Micro-UX improvements should prioritize inline styles or existing utility classes if possible, or very minimal additions to existing classes.
**Action:** Check project CSS for existing layout classes before adding new ones. Keep changes focused and under 50 lines.
