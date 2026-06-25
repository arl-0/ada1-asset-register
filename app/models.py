from . import db
from flask_login import UserMixin
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """Represents an authenticated user of the ADA-1 system."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    # Password is stored as a bcrypt hash — never in plaintext (OWASP A02)
    password = db.Column(db.String(256), nullable=False)
    clearance = db.Column(db.Integer, nullable=False)
    role = db.Column(db.String(10), nullable=False, default='regular')


class ADAEntry(db.Model):
    """A classified document / asset entry in the ADA-1 database."""
    id = db.Column(db.Integer, primary_key=True)
    asset_number = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    redacted_text = db.Column(db.Text, nullable=False)
    clearance_level = db.Column(db.Integer, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=_now, nullable=False)


class ChangeLog(db.Model):
    """Audit trail for edits made to ADA entries."""
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('ada_entry.id'))
    edited_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=_now, nullable=False)
    note = db.Column(db.String(200))

    asset = db.relationship('ADAEntry', backref='changelog')
    editor = db.relationship('User')
