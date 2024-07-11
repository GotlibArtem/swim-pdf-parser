"""ASGI config for swim_graph project."""
import os
from django.core.asgi import get_asgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'swim_graph.settings')

application = get_asgi_application()
