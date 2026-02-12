import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app_with_cookies import app as application

# Optional cPanel env overrides
application.config['ENV'] = os.environ.get('FLASK_ENV', 'production')
