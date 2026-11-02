# UI/UX Design Specification — Vybora Business Suite

## 1. Principles
Bengali-first, light-only, restrained premium business look. Correctness over
decoration. Every control is functional. Fast counter operations (POS) get
keyboard-first design; management screens get clear tables + forms.

## 2. Design tokens
- Primary: #0F6B4F (deep green — trust, commerce); Primary-dark #0B523D.
- Secondary/accent: #C9A227 (gold, sparingly).
- Neutrals: bg #F6F8F7, surface #FFFFFF, border #E2E8E4, text #1A2421, muted #5C6B66.
- Status: success #1B7F4D, warning #B7791F, danger #B3372F, info #2B6CB0.
- Radius: 8px cards/inputs, 6px buttons. Spacing scale: 4/8/12/16/24/32.
- Typography: Noto Sans Bengali (OFL) everywhere; sizes 12/13/14/16/20/24/30;
  body 14, table 13, headings 20–24. Line height 1.5 for Bengali.
- Inputs height 38px; buttons 38px (POS action buttons 48px); table row 36px.
- Icons: simple line icons (original SVGs), 18–20px, stroke 1.75.

## 3. Layout
- QMainWindow min 1100×700; sidebar 220px fixed (collapsible to 64px), header 56px.
- Sidebar items (Bengali): ড্যাশবোর্ড, বিক্রয় (POS), পণ্য, মজুত, ক্রয়, গ্রাহক,
  সরবরাহকারী, বাকি হিসাব, আয় ও ব্যয়, ক্যাশবুক, প্রতিবেদন, ব্যবহারকারী, ব্যাকআপ, সেটিংস.
- Content: QStackedWidget, lazy pages, vertical scroll where needed.
- Dashboard: responsive card grid (2/3/4 columns by width), charts below, recent
  transactions table; balanced rows (no orphan card).
- Tables: QTableView + model, sortable headers, sticky totals row where applicable,
  zebra rows, right-aligned numbers, Bengali headers.
- Dialogs: modal, centered on parent, min width 420px, destructive actions require
  typed confirmation or double-confirm; Bengali buttons (সংরক্ষণ করুন / বাতিল).

## 4. Interaction states
Default/hover/focus/disabled/loading/success/error for buttons, inputs, rows.
Focus ring 2px primary @ 40%. Loading: inline spinner + disabled submit. Empty states
with Bengali guidance + primary action. Errors: inline field text + toast (Bengali).

## 5. POS specifics
Left: search box (F2) + product results; right: cart table; bottom: totals panel +
payment panel. Shortcuts: F2 search, Enter add, F4 qty, F6 discount, F9 pay, Esc clear,
Ctrl+Enter complete. Barcode scanner input goes to search box (auto-add on exact
match + Enter). Touch targets ≥ 44px. Customer selector with quick-add dialog.

## 6. Localization rules
All strings from i18n/bn.py. Technical terms kept where clearer (SKU, Barcode, PDF,
Excel, USB). Numbers/currency/dates via core/formatting with user prefs. No English
leakage in customer-facing screens (audit: tests scan widget texts).

## 7. Verification
pytest-qt offscreen: instantiate every page/dialog, check no overlap via geometry
asserts, Bengali font applied, tab order, resize to 1100×700 and 1600×900, scaling
simulation via devicePixelRatio. Screenshots captured as evidence (docs/testing/evidence).
Windows display scaling (100/125/150%) verified on Windows CI + owner hardware checklist.
