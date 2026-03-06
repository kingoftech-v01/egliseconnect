# App: Reports (Rapports et analytics)

## Description
Tableaux de bord, rapports statistiques, rapports planifies, rapports sauvegardes et exports CSV. Fournit une vue d'ensemble complete de toutes les activites de l'eglise.

## Modeles (2)

| Modele | Champs cles | Relations |
|--------|------------|-----------|
| `ReportSchedule` | name, report_type, frequency, is_active, last_sent_at, next_run_at, filters_json, template_name | FK: created_by. M2M: recipients |
| `SavedReport` | name, report_type, filters_json, columns_json | FK: created_by. M2M: shared_with |

## Services (apps/reports/services.py)
- `DashboardService.get_member_stats()` - Total, actifs, nouveaux ce mois/annee, repartition par role
- `DashboardService.get_donation_stats(year)` - Totaux, ventilation mensuelle, par type, par methode
- `DashboardService.get_event_stats()` - Statistiques evenements

## API ViewSets (4+)
- `DashboardViewSet` - Stats agreges pour le dashboard principal
- `ReportViewSet` - Generation de rapports
- `ReportScheduleViewSet` - CRUD rapports planifies
- `SavedReportViewSet` - CRUD rapports sauvegardes
- `TreasurerDonationReportView` - `/api/reports/treasurer/donations/<year>/`

## Frontend Views (20 templates)
dashboard, member_stats, donation_report, attendance_report, volunteer_report, birthday_report, help_request_report, communication_report, yoy_comparison, giving_trends, pipeline_stats, predictive_dashboard, bi_api_endpoint, church_health_scorecard, report_schedule_list/create/edit/delete, saved_report_list/create/edit/delete/preview

## Exports CSV
- Membres, dons, presence, volontaires

## Forms (3)
ReportScheduleForm, SavedReportForm, DateRangeFilterForm

## Points d'attention
- Dashboard utilise ApexCharts et Chart.js pour les graphiques
- Rapports planifies: frequence daily/weekly/monthly/quarterly avec destinataires M2M
- Rapports sauvegardes: filtres et colonnes en JSON, partage avec d'autres membres
- BI API endpoint retourne des donnees brutes pour outils externes
- Church health scorecard: metriques de sante globale de l'eglise
- Dashboard predictif: modele basique, pas de vrai ML

## Fichiers cles
- `apps/reports/models.py` - 2 modeles
- `apps/reports/services.py` - DashboardService
- `apps/reports/views_api.py` - ViewSets + rapport tresorier
- `apps/reports/views_frontend.py` - 20 vues template
