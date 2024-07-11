"""WSGI config for swim_graph project."""
import os
from django.core.wsgi import get_wsgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'swim_graph.settings')

application = get_wsgi_application()
