# TODO - Donations App

## P1 — Critical

### CRUD Completions

- [ ] Donation detail: add edit button for finance staff (currently view-only)
- [ ] Donation: add delete view for admin (currently no delete in frontend)

### Pledge & Commitment Tracking

- [ ] Add Pledge model (member, amount, frequency, start/end date, campaign link, status)
- [ ] Add pledge CRUD views (create, list, detail, update status)
- [ ] Add pledge progress tracking (amount pledged vs. amount given)
- [ ] Add pledge reminder system (auto-notify members when pledge payment is due)
- [ ] Add pledge fulfillment report for finance staff

### Contribution Statements

- [ ] Add giving statement generation (mid-year and annual summary)
- [ ] Add PDF statement template with church branding (name, address, tax ID)
- [ ] Add bulk statement generation (all donors for a given period)
- [ ] Add email delivery of statements (individual or batch)
- [ ] Add statement download from member's "My giving" page

### Giving Goals

- [ ] Add per-member giving goal (annual target amount, visible to member)
- [ ] Add giving goal progress display on member giving page
- [ ] Add giving goal summary report for finance staff

### Export & Reporting

- [ ] Add CSV export for all donation list views (admin, member, campaign)
- [ ] Add Excel export with formatted columns and summary row
- [ ] Add PDF export for donation receipts and reports
- [ ] Add donation list filter by donation type (tithe, offering, etc.)

## P2 — Important

### Text-to-Give (SMS Donations)

- [ ] Add Twilio SMS integration for text-based donation commands
- [ ] Add SMS keyword registration (e.g., text "GIVE 50" to church number)
- [ ] Add SMS donation confirmation and receipt
- [ ] Add SMS donor lookup (match phone number to member)

### Donation Import

- [ ] Add bank statement import (CSV/OFX format) with transaction matching
- [ ] Add import from other giving platforms (Planning Center, Tithe.ly export format)
- [ ] Add import preview with duplicate detection
- [ ] Add import reconciliation report

### Giving Analytics Dashboard

- [ ] Add giving trends chart (monthly/quarterly/yearly giving totals)
- [ ] Add year-over-year comparison (same period last year vs. this year)
- [ ] Add donor retention metrics (new donors, returning donors, lapsed donors)
- [ ] Add average gift size trends
- [ ] Add first-time donor identification and follow-up triggers
- [ ] Add top donor report (configurable: top 10/20/50)

### Gift Matching Campaigns

- [ ] Add matching campaign model (matcher, match ratio, cap, campaign link)
- [ ] Add match progress display on campaign detail (matched amount vs. cap)
- [ ] Add match fulfillment notification to matcher

### Frontend Refinements

- [ ] Campaign detail: add "Faire un don" button linking to payment form with campaign pre-selected
- [ ] Tax receipt list: add batch email sending
- [ ] Monthly report: add date range picker (currently only month selection)
- [ ] Campaign list: add progress bar visual for each campaign's goal percentage
- [ ] Finance delegations: add confirmation dialog before revoking access

## P3 — Nice-to-Have

### Cryptocurrency Donations

- [ ] Add crypto wallet address display for Bitcoin/Ethereum donations
- [ ] Add crypto-to-fiat conversion tracking (record CAD equivalent at time of donation)
- [ ] Add crypto donation receipt generation

### Multi-Currency Giving

- [ ] Add currency field on donation model (default CAD)
- [ ] Add exchange rate conversion for reporting
- [ ] Add multi-currency display on giving statements

### Giving Kiosk

- [ ] Add simplified kiosk UI for in-church cash/check entry (large touch-friendly buttons)
- [ ] Add kiosk mode (no login required, staff PIN access)
- [ ] Add batch entry mode (enter multiple donations quickly)

### ACH Direct Debit

- [ ] Add bank account linking via Stripe ACH or equivalent
- [ ] Add recurring ACH debit setup and management
- [ ] Add ACH-specific confirmation and notification flow

### Existing Small Fixes

- [ ] Add donation confirmation email/notification after manual entry
- [ ] Tax receipt: add "Download PDF" button on individual receipt detail
- [ ] Campaign form: add end date validation (end > start)
- [ ] Add "Delegations" sidebar link for treasurer/admin
- [ ] Verify campaign CRUD links accessible from campaign list
