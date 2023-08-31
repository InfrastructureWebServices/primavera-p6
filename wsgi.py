from os import path, environ
import sys
import logging
from dotenv import load_dotenv
logging.basicConfig(stream=sys.stderr)
load_dotenv(path.join(path.dirname(__file__), '.env'))
sys.path.insert(0, environ.get('IMPORT_FLASK'))

from flask_server import app as application
application.secret_key = environ.get('FLASK_SECRET_KEY')
