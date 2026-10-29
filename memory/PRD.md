# Morrow Market — PRD

## Original problem statement
"An app that will make money while i sleep" → Automated digital product storefront: owner uploads digital products; customers discover, buy, and download them.

## User choices
- Owner/admin: Ysrilekha348@gmail.com (Clerk sign-in)
- Payments: Stripe isn't supported for India. Razorpay was picked, but no keys were provided. The user then asked to use GPay for now, with number 9337939011, a QR uploaded by the owner, and downloads unlocking only after the owner confirms.
- Files: Emergent object storage for real files; seed products keep sample demo files.
- Sign-in page styled to match the store.

## Architecture
- React SPA (App.js), Clerk auth, custom CSS (App.css)
- FastAPI (server.py) + MongoDB (products, orders, settings) + storage.py (Emergent object storage)

## Implemented
- 2026-06: Storefront, product detail, Clerk-protected owner space
- 2026-06: Manual GPay flow: checkout (email), then the pay page (QR, GPay number, amount, UTR), then the status page (pending, paid with download, or rejected with retry). Owner approves or rejects orders.
- 2026-06: Owner settings: edit GPay number, upload or replace QR. Per-product real file upload to object storage. Downloads are gated on paid status.
- 2026-06: Prices in INR (₹499/₹899/₹299 seeds). Not-found states, error handling, useEffect dependency fix.

- 2026-06: Percentage discount codes with an optional max-uses limit. Owner creates, pauses and resumes codes. Customers apply a code at checkout. A rejected order releases its use.

## Backlog
- P0: Owner uploads the QR and real product files
- P1: Razorpay automatic payments (needs RAZORPAY_KEY_ID/SECRET), which removes the manual approval step
- P1: Email the customer when the order is approved, with the download link
- P2: Edit/unpublish products and upload cover images from the dashboard
