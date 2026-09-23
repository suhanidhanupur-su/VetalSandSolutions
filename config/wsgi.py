"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

# When running on Vercel/serverless, ensure pending migrations are applied and catalog is seeded
if os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV') or os.environ.get('VERCEL_URL'):
    try:
        from django.core.management import call_command
        call_command('migrate', interactive=False)

        from products.models import Product, ProductImage
        if Product.objects.count() < 10:
            from pathlib import Path
            fixture_path = Path(__file__).resolve().parent.parent / 'initial_catalog.json'
            if fixture_path.exists():
                call_command('loaddata', str(fixture_path))

        # Ensure each product has a designated primary image
        for p in Product.objects.prefetch_related('images'):
            if not p.images.filter(is_primary=True).exists():
                first_img = p.images.first()
                if first_img:
                    first_img.is_primary = True
                    first_img.save(update_fields=['is_primary'])
    except Exception as exc:
        import logging
        logging.getLogger('config.wsgi').error("Vercel startup migration/initialization error: %s", exc)

app = application

