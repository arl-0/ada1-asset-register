from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from .forms import LoginForm, RegisterForm, AssetForm, EditUserForm
from .models import User, ADAEntry, ChangeLog
from . import db, login_manager
from datetime import datetime, timezone

main = Blueprint('main', __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ================================================================
# STARTUP GATE
# ================================================================

@main.route('/')
def index():
    if current_app.config.get('DEBUG_BYPASS_STARTUP'):
        return redirect(url_for('main.login'))
    return redirect(url_for('main.startup'))


@main.route('/startup', methods=['GET', 'POST'])
def startup():
    if request.method == 'POST':
        answer = request.form.get('answer', '').strip().lower()
        if answer == 'only at the blind':
            return redirect(url_for('main.login'))
        flash('ACCESS DENIED: Authorisation phrase invalid.')
        return redirect(url_for('main.startup'))
    return render_template('startup.html')


# ================================================================
# AUTHENTICATION
# Passwords are hashed with Werkzeug's PBKDF2-HMAC-SHA256 before
# storage, mitigating OWASP A02 (Cryptographic Failures).
# Flask-WTF CSRF tokens on every form mitigate OWASP A01 / A05.
# ================================================================

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        # check_password_hash compares the submitted password against the
        # stored hash — the plaintext password is never retained (OWASP A02)
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Invalid username or password.')
    return render_template('login.html', form=form)


@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.')
            return redirect(url_for('main.register'))

        hashed_pw = generate_password_hash(form.password.data)
        new_user = User(
            username=form.username.data,
            password=hashed_pw,   # Only the hash is persisted (OWASP A02)
            clearance=form.clearance.data,
            role='regular'
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Account created. You may now log in.')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


# ================================================================
# DASHBOARD + ASSET VIEW
# ================================================================

@main.route('/dashboard')
@login_required
def dashboard():
    # Only return entries the current user's clearance permits (OWASP A01)
    entries = ADAEntry.query.filter(
        ADAEntry.clearance_level <= current_user.clearance
    ).order_by(ADAEntry.created_at.desc()).all()
    return render_template('dashboard.html', user=current_user, entries=entries)


@main.route('/asset/<int:asset_id>')
@login_required
def view_asset(asset_id):
    asset = ADAEntry.query.get_or_404(asset_id)
    # Enforce object-level authorisation — clearance check on every request
    if current_user.clearance < asset.clearance_level:
        flash('Insufficient clearance to view this asset.')
        return redirect(url_for('main.dashboard'))
    return render_template('asset_detail.html', asset=asset)


# ================================================================
# ASSET CRUD — admin only
# ================================================================

@main.route('/add-asset', methods=['GET', 'POST'])
@login_required
def add_asset():
    if current_user.role != 'admin':
        flash('Only admins can create entries.')
        return redirect(url_for('main.dashboard'))

    form = AssetForm()
    if form.validate_on_submit():
        new_entry = ADAEntry(
            asset_number=form.asset_number.data,
            title=form.title.data,
            content=form.content.data,
            redacted_text=form.redacted_text.data,
            clearance_level=form.clearance_level.data,
            created_by=current_user.id
        )
        db.session.add(new_entry)
        db.session.commit()
        flash('New ADA entry created successfully.')
        return redirect(url_for('main.dashboard'))

    return render_template('add_asset.html', form=form, edit=False)


@main.route('/edit-asset/<int:asset_id>', methods=['GET', 'POST'])
@login_required
def edit_asset(asset_id):
    if current_user.role != 'admin':
        flash('Admins only.')
        return redirect(url_for('main.dashboard'))

    asset = ADAEntry.query.get_or_404(asset_id)
    form = AssetForm(obj=asset)

    if form.validate_on_submit():
        asset.asset_number = form.asset_number.data
        asset.title = form.title.data
        asset.content = form.content.data
        asset.redacted_text = form.redacted_text.data
        asset.clearance_level = form.clearance_level.data
        db.session.commit()

        log = ChangeLog(asset_id=asset.id, edited_by=current_user.id, note='Entry updated')
        db.session.add(log)
        db.session.commit()

        flash('Asset updated successfully.')
        return redirect(url_for('main.dashboard'))

    return render_template('add_asset.html', form=form, edit=True)


@main.route('/delete-asset/<int:asset_id>', methods=['POST'])
@login_required
def delete_asset(asset_id):
    """
    DELETE uses POST (not GET) so it:
    - Requires a valid CSRF token from Flask-WTF (mitigates OWASP A01 CSRF)
    - Cannot be triggered by a passive GET request (e.g. an <img> tag attack)
    """
    if current_user.role != 'admin':
        flash('Admins only.')
        return redirect(url_for('main.dashboard'))

    asset = ADAEntry.query.get_or_404(asset_id)
    db.session.delete(asset)
    db.session.commit()
    flash('Asset deleted.')
    return redirect(url_for('main.dashboard'))


# ================================================================
# ADMIN PANEL — user management
# ================================================================

@main.route('/admin-panel')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('Admins only.')
        return redirect(url_for('main.dashboard'))

    users = User.query.all()
    return render_template('admin_panel.html', users=users)


@main.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        flash('Admins only.')
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)
    # EditUserForm pre-populates with current values and provides CSRF protection
    form = EditUserForm(obj=user)

    if form.validate_on_submit():
        user.username = form.username.data
        user.clearance = form.clearance.data
        user.role = form.role.data
        db.session.commit()
        flash('User updated.')
        return redirect(url_for('main.admin_panel'))

    return render_template('edit_user.html', user=user, form=form)


@main.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """POST-only delete mitigates CSRF (OWASP A01)."""
    if current_user.role != 'admin':
        flash('Admins only.')
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.')
        return redirect(url_for('main.admin_panel'))

    db.session.delete(user)
    db.session.commit()
    flash('User deleted.')
    return redirect(url_for('main.admin_panel'))
