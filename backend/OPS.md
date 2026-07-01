# Backend Operations

## Database views (placement reports, analytics)

Use the management command (canonical path):

```bash
cd backend
python manage.py create_placement_views
```

Views are defined in `backend/POSTGRESQL_ANALYTICS_VIEWS.sql`. The analytics migration also loads this file on deploy.

## Django settings

All scripts and `manage.py` use **`config.dev_settings`**.

## Data reset

```bash
python manage.py reset_db --confirm
```

For a full destructive reset with backup, use `reset_database.py` (root of `backend/`).

## Seeding

- Lookup seeds: `python manage.py seed_data` (if available) or root `seed_*.py` scripts
- Active batch: `python manage.py set_active_batch <batch_name>`

## Celery

Celery is configured but **beat schedule is disabled** until `apps.analytics.tasks` is implemented.
