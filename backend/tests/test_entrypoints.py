import unittest

from api.extract import app as extract_app
from api.health import app as health_app
from api.search import app as search_app
from backend.main import app


class Entrypoints(unittest.TestCase):
    def test_vercel_wrappers_export_the_fastapi_app(self):
        self.assertIs(health_app, app)
        self.assertIs(extract_app, app)
        self.assertIs(search_app, app)
