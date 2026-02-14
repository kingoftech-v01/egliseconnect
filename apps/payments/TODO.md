# TODO - Payments App

## P1 — Critical

### Giving Statements

- [ ] Add quarterly and annual giving statement generation
- [ ] Add PDF statement template with church branding (name, address, charitable registration number)
- [ ] Add bulk statement generation for all donors in a period
- [ ] Add email delivery of statements (individual or batch with PDF attachment)
- [ ] Add statement download from member's payment history page

### Giving Goal Tracking

- [ ] Add per-member giving goal (annual target, visible to member on their giving page)
- [ ] Add giving goal progress bar display
- [ ] Add goal completion notification/congratulations
- [ ] Add giving goal summary for finance staff (total pledged vs. total received)

### Apple Pay / Google Pay Support

- [ ] Add Stripe Payment Request API integration (Apple Pay, Google Pay buttons)
- [ ] Add payment method detection (show Apple Pay on iOS, Google Pay on Android)
- [ ] Add one-tap donation flow (pre-filled amount, single confirmation)

### Frontend Refinements

- [ ] Payment history: add pagination (currently limited to last 100 for admin)
- [ ] Recurring donations: add edit amount/frequency functionality
- [ ] Recurring donations: add cancel confirmation dialog
- [ ] Donate page: add suggested amount buttons (e.g., $25, $50, $100, custom)

## P2 — Important

### Text-to-Give (SMS)

- [ ] Add SMS shortcode registration for giving (e.g., text "GIVE 100" to church number)
- [ ] Add SMS donor registration flow (first-time SMS donors enter card info via link)
- [ ] Add SMS donation confirmation and receipt
- [ ] Add SMS recurring donation setup commands

### ACH / Bank Transfer Direct Debit

- [ ] Add Stripe ACH integration for direct bank debit
- [ ] Add bank account verification flow (micro-deposits or instant verification)
- [ ] Add ACH recurring debit setup
- [ ] Add ACH-specific processing time notice (3-5 business days)

### Multi-Currency Support

- [ ] Add currency selection on donation form (CAD, USD, EUR)
- [ ] Add exchange rate display at time of donation
- [ ] Add multi-currency reporting (amounts in original currency + CAD equivalent)

### Giving Kiosk

- [ ] Add in-church giving kiosk UI (touch-screen card tap, large buttons)
- [ ] Add Stripe Terminal integration for in-person card payments
- [ ] Add kiosk receipt printing (thermal printer support)
- [ ] Add kiosk session tracking and daily reconciliation

### Sidebar / Navigation

- [ ] Add "Historique paiements" link in sidebar under Dons section
- [ ] Add "Dons recurrents" link in sidebar for members
- [ ] Add "Faire un don" quick action link visible to all members

## P3 — Nice-to-Have

### Cryptocurrency Donations

- [ ] Add crypto payment gateway integration (BitPay, Coinbase Commerce)
- [ ] Add crypto-to-CAD conversion at time of donation
- [ ] Add crypto donation tax receipt generation
- [ ] Add supported crypto display (Bitcoin, Ethereum, USDC)

### Payment Plan Support

- [ ] Add payment plan model (total_amount, installment_amount, frequency, remaining)
- [ ] Add payment plan setup for large gifts (split into monthly installments)
- [ ] Add payment plan progress tracking and reminders
- [ ] Add early completion option

### Employer Matching Integration

- [ ] Add employer matching program model (employer_name, match_ratio, annual_cap)
- [ ] Add matching request submission (member submits matching form to employer)
- [ ] Add matching receipt tracking (record when employer match is received)

### Year-End Campaign Tools

- [ ] Add year-end giving campaign page (goal, progress, countdown timer)
- [ ] Add tax-deadline reminder emails (last chance for tax-deductible giving)
- [ ] Add year-end giving summary email to all donors
- [ ] Add campaign thermometer widget for homepage

### Existing Small Fixes

- [ ] Add payment confirmation page with receipt details
- [ ] Connect Stripe webhook error handling UI for admin
- [ ] Add recurring donation summary on member's profile page
- [ ] Donate page: pre-select campaign when navigating from campaign detail
- [ ] Add monthly giving summary notification to recurring donors
