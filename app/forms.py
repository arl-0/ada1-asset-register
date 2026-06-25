from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import InputRequired, Length, ValidationError
import re


def _strong_password(form, field):
    """Custom validator: password must be ≥8 chars and contain a digit."""
    pw = field.data
    if len(pw) < 8:
        raise ValidationError('Password must be at least 8 characters.')
    if not re.search(r'\d', pw):
        raise ValidationError('Password must contain at least one number.')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=3, max=150)])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=3, max=150)])
    password = PasswordField('Password', validators=[InputRequired(), _strong_password])
    # Clearance levels now match the 1-5 range used by ADAEntry
    clearance = SelectField(
        'Clearance Level',
        choices=[(1, 'Level 1'), (2, 'Level 2'), (3, 'Level 3'),
                 (4, 'Level 4'), (5, 'Level 5')],
        coerce=int
    )
    submit = SubmitField('Register')


class AssetForm(FlaskForm):
    asset_number = StringField('Asset Number', validators=[InputRequired(), Length(max=50)])
    title = StringField('Title', validators=[InputRequired(), Length(max=100)])
    content = TextAreaField('Full Content', validators=[InputRequired()])
    redacted_text = TextAreaField('Redacted Version', validators=[InputRequired()])
    clearance_level = SelectField(
        'Required Clearance Level',
        choices=[(1, 'Level 1'), (2, 'Level 2'), (3, 'Level 3'),
                 (4, 'Level 4'), (5, 'Level 5')],
        coerce=int
    )
    submit = SubmitField('Save Entry')


class EditUserForm(FlaskForm):
    """WTForms-based form for admin user editing — provides CSRF protection."""
    username = StringField('Username', validators=[InputRequired(), Length(min=3, max=150)])
    clearance = SelectField(
        'Clearance Level',
        choices=[(1, 'Level 1'), (2, 'Level 2'), (3, 'Level 3'),
                 (4, 'Level 4'), (5, 'Level 5')],
        coerce=int
    )
    role = SelectField('Role', choices=[('admin', 'Admin'), ('regular', 'Regular')])
    submit = SubmitField('Update User')
