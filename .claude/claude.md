# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Immodash is a property tracking SaaS platform that automatically scrapes real estate listings from Leboncoin, detecting new listings, price changes, and sold properties. Built with Django 5.1, Celery for async tasks, and modern frontend (TailwindCSS, HTMX, Alpine.js).

## Development Setup

### Docker (Recommended)
```bash
# Start all services (web, celery_worker, celery_beat, redis)
docker-compose up -d

# Execute Django commands
docker-compose exec web python manage.py <command>

# View logs
docker-compose logs -f web
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

### Local Development
Requires 3 terminals:
```bash
# Terminal 1: Django dev server
python manage.py runserver

# Terminal 2: Celery worker
celery -A config worker -l info

# Terminal 3: Celery beat (periodic tasks)
celery -A config beat -l info
```

## Common Commands

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Testing
```bash
# Run all tests
python manage.py test

# Specific app
python manage.py test property_tracker

# With coverage
coverage run --source='.' manage.py test
coverage report
```

### Manual Scraping
```python
# In Django shell
from property_tracker.tasks import scrape_all_search_zones
scrape_all_search_zones()

# Or for a single zone
from property_tracker.tasks import scrape_single_zone
scrape_single_zone(zone_id=1)
```

## Architecture

### Core Models (`property_tracker/models.py`)

**UserSearchPreferences** (OneToOne with User)
- Single search zone per user with city, radius, property_type
- Auto-created for new users via signal

**SearchZone** (ForeignKey to User)
- Multiple zones per user possible
- Fields: city, radius_km, property_type, is_active
- Users can create/manage multiple search zones

**Listing** (ForeignKey to SearchZone)
- Unique by `external_id` (e.g., "lbc_12345")
- Tracks: current_price, surface, price_per_sqm, rooms, city, coordinates
- Status fields: is_active, first_seen_at, last_seen_at, sold_at
- Price change tracking: has_price_changed, last_price_change_date, last_price_change_percent

**PriceHistory** (ForeignKey to Listing)
- Historical record of all price changes
- Fields: price, price_per_sqm, change_percent, detected_at

### Scraping Architecture (`property_tracker/scrapers.py`)

**BaseScraper** abstract class:
- `save_or_update_listing()`: Core logic for new listings vs. price changes
  - New listing → Create Listing + initial PriceHistory entry
  - Existing listing with price change → Update Listing + add PriceHistory entry
  - Existing listing without change → Update last_seen_at only

**LeboncoinScraper(BaseScraper)**:
- Uses `lbc` library (v1.0.10)
- `scrape()`: Search with city/radius, returns list of Listing objects
- `_parse_leboncoin_item()`: Extracts data from API response

**mark_inactive_listings()**: Marks listings as sold if not seen for >24h

### Celery Tasks (`property_tracker/tasks.py`)

All tasks are `@shared_task` decorated:

- `scrape_all_search_zones()`: Scrapes all active SearchZones
- `scrape_single_zone(zone_id)`: Scrapes one zone
- `check_inactive_listings()`: Marks old listings as sold
- `periodic_scraping_task()`: Combines scraping + inactive check (runs every 30 min)

**Celery Beat Schedule** (`config/celery.py`):
```python
'scrape-every-30-minutes': {
    'task': 'property_tracker.tasks.periodic_scraping_task',
    'schedule': crontab(minute='*/30'),
}
```

### Frontend Pattern

- **TailwindCSS** for styling
- **HTMX** for dynamic interactions (filters, sorting, pagination)
- **Alpine.js** for client-side interactions (modals, dropdowns)
- **Plotly** for price history charts

### Django Conventions

- Class-based views preferred
- Use `select_related()` and `prefetch_related()` for query optimization
- Forms for validation
- `get_object_or_404()` for single object retrieval

## Custom Slash Commands

- `/stats` - Display database statistics
- `/docker-restart` - Restart all Docker services
- `/migrate` - Create and apply migrations
- `/scrape` - Manual scraping of all zones
- `/check` - Django health check
- `/docker-logs` - View Docker logs
- `/test` - Run tests with coverage
- `/shell` - Open Django shell in Docker

## Key Implementation Details

### Price Change Detection
When scraping finds an existing listing:
1. Compare `current_price` with new price
2. If different: calculate `change_percent`, update listing fields, create PriceHistory entry
3. If same: only update `last_seen_at` (via auto_now on save)

### Automatic Listing Status
- Listings marked as sold (`is_active=False`, `sold_at=now()`) if `last_seen_at < now() - 24h`
- Handled by `mark_inactive_listings()` called in periodic task

### User Search Flow
1. User creates SearchZone (city, radius, property_type)
2. Zone automatically picked up by periodic scraping (every 30 min)
3. Or trigger manual scraping via `/scrape` or shell command

## Troubleshooting

### Scraping Issues
1. Check Celery worker/beat are running: `docker-compose ps`
2. Check logs: `docker-compose logs -f celery_worker celery_beat`
3. Test manually in Django shell (see Manual Scraping above)

### Migration Errors
```bash
python manage.py migrate --fake-initial
```

### Database Statistics (Stats Command Issue)
Note: The `/stats` command references old model fields (`status='active'`/`status='sold'` and `price` instead of `current_price`). Current model uses `is_active` boolean and `current_price`.

## Production Considerations

- Switch to PostgreSQL (SQLite not recommended for production)
- Set `DEBUG=False`
- Configure strong `SECRET_KEY`
- Set proper `ALLOWED_HOSTS`
- Use proper WSGI server (Gunicorn included in requirements)
- Consider adding Nginx/Traefik for HTTPS and static files