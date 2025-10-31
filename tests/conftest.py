import os, pytest
from erp import create_app
@pytest.fixture
def app():
    cfg = {'TESTING': True,'WTF_CSRF_ENABLED': False,'ERP_AUTO_REGISTER': '0',
           'SQLALCHEMY_DATABASE_URI': os.environ.get('TEST_DATABASE_URI', 'sqlite://')}
    app = create_app(cfg); yield app
@pytest.fixture
def client(app): return app.test_client()