import json
import secrets
from datetime import datetime, timedelta
from typing import cast, Optional

import pyotp
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from flask_wtf import FlaskForm
from sqlalchemy import text
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from wtforms import (
    DateField,
    FloatField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Length, NumberRange

from db import get_db, redis_client
from e
