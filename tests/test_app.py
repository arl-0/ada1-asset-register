"""
Unit and integration tests for ADA-1.

Run with:  pytest tests/ -v
Coverage:  pytest tests/ --cov=app --cov-report=term-missing
"""

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app import db as _db
from app.models import User, ADAEntry


# ------------------------------------------------------------------ #
# Fixtures                                                             #
# ------------------------------------------------------------------ #

@pytest.fixture(scope='session')
def app():
    """Create one app instance for the whole test session."""
    test_app = create_app()
    test_app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'DEBUG_BYPASS_STARTUP': True,
        'SECRET_KEY': 'test-secret-key',
    })
    with test_app.app_context():
        _db.drop_all()   # Ensure no stale schema from previous runs
        _db.create_all()
        yield test_app
        _db.drop_all()


@pytest.fixture(autouse=True)
def reset_db(app):
    """Wipe and re-seed the database before every single test."""
    with app.app_context():
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()
        _seed_db()
    yield
    with app.app_context():
        _db.session.remove()


def _seed_db():
    """Insert a standard admin and regular user plus two sample assets."""
    admin = User(
        username='admin',
        password=generate_password_hash('admin123'),
        clearance=5,
        role='admin'
    )
    regular = User(
        username='user1',
        password=generate_password_hash('user1pass1'),
        clearance=2,
        role='regular'
    )
    _db.session.add_all([admin, regular])
    _db.session.flush()   # Populate IDs before referencing them

    asset = ADAEntry(
        asset_number='ADA-001',
        title='Test Document',
        content='Full classified content here.',
        redacted_text='[REDACTED]',
        clearance_level=2,
        created_by=admin.id
    )
    restricted = ADAEntry(
        asset_number='ADA-002',
        title='Top Secret Document',
        content='Eyes only.',
        redacted_text='[REDACTED]',
        clearance_level=5,
        created_by=admin.id
    )
    _db.session.add_all([asset, restricted])
    _db.session.commit()


@pytest.fixture
def client(app):
    return app.test_client()


def _login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password},
                       follow_redirects=True)


# ------------------------------------------------------------------ #
# Authentication tests                                                 #
# ------------------------------------------------------------------ #

class TestAuth:
    def test_login_valid_credentials(self, client):
        """Valid credentials redirect to dashboard."""
        resp = _login(client, 'admin', 'admin123')
        assert resp.status_code == 200
        assert b'Asset Register' in resp.data

    def test_login_wrong_password(self, client):
        """Wrong password stays on login page with error."""
        resp = _login(client, 'admin', 'wrongpassword')
        assert b'Invalid username or password' in resp.data

    def test_login_unknown_user(self, client):
        """Unknown username shows same generic error (no user enumeration)."""
        resp = _login(client, 'nobody', 'password123')
        assert b'Invalid username or password' in resp.data

    def test_register_creates_user(self, client, app):
        """Registering a new user stores a hashed password, not plaintext."""
        client.post('/register', data={
            'username': 'newuser',
            'password': 'securepass9',
            'clearance': 1
        })
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            assert user is not None
            # The stored value must NOT equal the raw password
            assert user.password != 'securepass9'
            # Must start with a Werkzeug hash prefix
            assert user.password.startswith('pbkdf2:') or user.password.startswith('scrypt:')

    def test_register_weak_password_rejected(self, client):
        """Password without a digit is rejected by the form validator."""
        resp = client.post('/register', data={
            'username': 'weakuser',
            'password': 'nodigitshere',
            'clearance': 1
        }, follow_redirects=True)
        assert b'must contain at least one number' in resp.data

    def test_logout_redirects_to_login(self, client):
        _login(client, 'admin', 'admin123')
        resp = client.get('/logout', follow_redirects=True)
        assert b'Log in' in resp.data


# ------------------------------------------------------------------ #
# Access control tests (OWASP A01)                                     #
# ------------------------------------------------------------------ #

class TestAccessControl:
    def test_dashboard_requires_login(self, client):
        """Unauthenticated request to dashboard is redirected to login."""
        resp = client.get('/dashboard', follow_redirects=True)
        assert b'Log in' in resp.data

    def test_regular_user_cannot_add_asset(self, client):
        """Regular user is blocked from the add-asset route."""
        _login(client, 'user1', 'user1pass1')
        resp = client.post('/add-asset', data={
            'asset_number': 'X-001',
            'title': 'Hacked',
            'content': 'injected',
            'redacted_text': 'injected',
            'clearance_level': 1
        }, follow_redirects=True)
        assert b'Only admins' in resp.data

    def test_regular_user_cannot_delete_asset(self, client):
        """Regular user cannot delete an asset."""
        _login(client, 'user1', 'user1pass1')
        resp = client.post('/delete-asset/1', follow_redirects=True)
        assert b'Admins only' in resp.data

    def test_user_cannot_view_asset_above_clearance(self, client):
        """User with clearance 2 cannot view a clearance-5 asset."""
        _login(client, 'user1', 'user1pass1')
        # ADA-002 is clearance 5; user1 is clearance 2
        resp = client.get('/asset/2', follow_redirects=True)
        assert b'Insufficient clearance' in resp.data

    def test_admin_can_access_admin_panel(self, client):
        """Admin can reach the admin panel."""
        _login(client, 'admin', 'admin123')
        resp = client.get('/admin-panel')
        assert resp.status_code == 200
        assert b'Admin panel' in resp.data

    def test_regular_user_blocked_from_admin_panel(self, client):
        """Regular user is blocked from admin panel."""
        _login(client, 'user1', 'user1pass1')
        resp = client.get('/admin-panel', follow_redirects=True)
        assert b'Admins only' in resp.data


# ------------------------------------------------------------------ #
# CSRF / delete-method tests (OWASP A01)                              #
# ------------------------------------------------------------------ #

class TestDeleteSecurity:
    def test_delete_asset_via_get_not_allowed(self, client):
        """GET request to delete route returns 405 — only POST is accepted."""
        _login(client, 'admin', 'admin123')
        resp = client.get('/delete-asset/1')
        assert resp.status_code == 405

    def test_delete_user_via_get_not_allowed(self, client):
        """GET request to delete-user returns 405."""
        _login(client, 'admin', 'admin123')
        resp = client.get('/delete-user/2')
        assert resp.status_code == 405


# ------------------------------------------------------------------ #
# SQL injection resistance (OWASP A03)                                 #
# ------------------------------------------------------------------ #

class TestSQLInjection:
    def test_login_sql_injection_payload_fails(self, client):
        """Classic SQL injection in username field does not authenticate."""
        resp = _login(client, "' OR '1'='1", 'anything')
        assert b'Invalid username or password' in resp.data

    def test_login_second_order_injection_fails(self, client):
        """Second-order injection attempt in username does not bypass login."""
        resp = _login(client, 'admin --', 'admin123')
        assert b'Invalid username or password' in resp.data
