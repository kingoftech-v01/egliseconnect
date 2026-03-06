# TODO - Reports App

## P1 — Critical

### Chart.js Visualizations

- [ ] Add Chart.js integration for all report pages
- [ ] Add member growth line chart (new members per month)
- [ ] Add donation bar chart (monthly/quarterly giving totals)
- [ ] Add attendance trend chart (weekly attendance over time)
- [ ] Add event participation chart (RSVP vs. actual attendance)
- [ ] Add volunteer hours chart (hours by position/month)

### Scheduled Email Reports

- [ ] Add report scheduling model (report_type, frequency, recipients, next_run)
- [ ] Add weekly/monthly summary email to pastors (key metrics: attendance, giving, new members)
- [ ] Add Celery task for automated report generation and delivery
- [ ] Add report schedule management UI for admin

### Export on Every Report Page

- [ ] Add CSV export button on all report pages
- [ ] Add PDF export with charts and formatting
- [ ] Add Excel export with formatted tables and summary rows
- [ ] Add print-friendly stylesheet for all report pages

### Frontend Refinements

- [ ] Dashboard: add date range selector for quick filtering across all stats
- [ ] Member stats: add chart for member growth trend over time
- [ ] Donation report: add comparison with previous year/period
- [ ] Attendance report: integrate with AttendanceSession data for richer analytics
- [ ] Birthday report: add "Send wishes" button/link for each member

## P2 — Important

### Custom Report Builder

- [ ] Add report builder UI (select data source, metrics, filters, date range)
- [ ] Add saved report templates (save configuration for reuse)
- [ ] Add report sharing (share saved reports with other staff members)
- [ ] Add multi-data-source reports (combine members + donations + attendance in one report)
- [ ] Add grouping/aggregation options (group by month, quarter, year, group, position)

### Year-Over-Year Comparison

- [ ] Add YOY comparison toggle on all numeric reports
- [ ] Add percentage change indicators (up/down arrows with delta)
- [ ] Add comparison period selector (vs. last year, vs. last quarter, vs. custom period)
- [ ] Add trend direction indicators (improving, declining, stable)

### Giving Trend Analysis

- [ ] Add donor retention rate calculation (% of donors who gave again this year)
- [ ] Add average gift size tracking over time
- [ ] Add first-time donor identification and count per period
- [ ] Add lapsed donor report (gave last year but not this year)
- [ ] Add giving projection based on current trends

### Small Complementary Features

- [ ] Add onboarding pipeline statistics to dashboard (members in each stage)
- [ ] Add volunteer report: top volunteers ranking
- [ ] Add dashboard: quick action buttons (create event, create session, send newsletter)
- [ ] Add financial summary widget to dashboard (monthly giving trend)

## P3 — Nice-to-Have

### Predictive Analytics

- [ ] Add attendance prediction model (expected vs. actual for upcoming Sundays)
- [ ] Add churn risk scoring (members likely to become inactive based on engagement patterns)
- [ ] Add giving forecast (projected annual giving based on current trajectory)
- [ ] Add seasonal adjustment in predictions (account for summer dips, holiday spikes)

### BI Tool Integration

- [ ] Add Metabase embed support (embed Metabase dashboards within EgliseConnect)
- [ ] Add Grafana integration for real-time metrics
- [ ] Add data warehouse export (nightly ETL to analytics database)
- [ ] Add API endpoint for external BI tools to query

### Church Health Scorecard

- [ ] Add composite health score (weighted average of attendance + giving + volunteering + groups)
- [ ] Add health score trend over time (is the church growing healthier?)
- [ ] Add benchmark comparison (compare metrics against similar-sized churches)
- [ ] Add health score breakdown by category with improvement suggestions
- [ ] Add monthly health report email to senior pastor
