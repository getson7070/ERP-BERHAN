from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired
from datetime import datetime

from db import get_db
from erp.utils import login_required, has_permission

bp = Blueprint('tenders', __name__)

# ordered states reflecting the full tender lifecycle
WORKFLOW_STATES = [
    'advert_registered',
    'decided_to_register',
    'documents_secured',
    'preparing_documentation',
    'documentation_prepared',
    'document_submitted',
    'opening_minute',
    'evaluated',
    'awarded',
]


@bp.route('/add_tender', methods=['GET', 'POST'])
@login_required
def add_tender():
    if not has_permission('add_tender'):
        return redirect(url_for('main.dashboard'))
    class TenderForm(FlaskForm):
        tender_type_id = SelectField('Tender Type', coerce=int, validators=[DataRequired()])
        description = StringField('Description', validators=[DataRequired()])
        due_date = DateField('Due Date', validators=[DataRequired()])
        institution = StringField('Institution')
        envelope_type = SelectField('Envelope Type', choices=[('One Envelope', 'One Envelope'), ('Two Envelope', 'Two Envelope')], validators=[DataRequired()])
        private_key = StringField('Private Key')
        tech_key = StringField('Technical Key')
        fin_key = StringField('Financial Key')
        submit = SubmitField('Submit')
    conn = get_db()
    form = TenderForm()
    form.tender_type_id.choices = [(t['id'], t['type_name']) for t in conn.execute('SELECT id, type_name FROM tender_types').fetchall()]
    if form.validate_on_submit():
        tender_type_id = form.tender_type_id.data
        description = form.description.data
        due_date = form.due_date.data
        institution = form.institution.data
        envelope_type = form.envelope_type.data
        private_key = form.private_key.data if envelope_type == 'One Envelope' else None
        tech_key = form.tech_key.data if envelope_type == 'Two Envelope' else None
        fin_key = form.fin_key.data if envelope_type == 'Two Envelope' else None
        user = session.get('username') if session.get('role') != 'Client' else session['tin']
        conn.execute(
            '''INSERT INTO tenders (tender_type_id, description, due_date, workflow_state, user, institution, envelope_type, private_key, tech_key, fin_key)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                tender_type_id,
                description,
                due_date,
                'advert_registered',
                user,
                institution,
                envelope_type,
                private_key,
                tech_key,
                fin_key,
            ),
        )
        conn.commit()
        conn.close()
        return redirect(url_for('main.dashboard'))
    conn.close()
    return render_template('add_tender.html', form=form)


@bp.route('/tenders_list')
@login_required
def tenders_list():
    if not has_permission('tenders_list'):
        return redirect(url_for('main.dashboard'))
    conn = get_db()
    tenders = conn.execute('SELECT t.id, tt.type_name, t.description, t.due_date, t.workflow_state, t.result, t.awarded_to, t.award_date, t.user, t.institution, t.envelope_type FROM tenders t JOIN tender_types tt ON t.tender_type_id = tt.id ORDER BY t.due_date ASC').fetchall()
    conn.close()
    return render_template('tenders_list.html', tenders=tenders, states=WORKFLOW_STATES)


@bp.route('/tenders_report')
@login_required
def tenders_report():
    if not has_permission('tenders_report'):
        return redirect(url_for('main.dashboard'))
    conn = get_db()
    tenders = conn.execute('SELECT t.id, tt.type_name, t.description, t.due_date, t.workflow_state, t.result, t.awarded_to, t.award_date, t.user, t.institution, t.envelope_type FROM tenders t JOIN tender_types tt ON t.tender_type_id = tt.id ORDER BY t.due_date ASC').fetchall()
    conn.close()
    return render_template('tenders_report.html', tenders=tenders, states=WORKFLOW_STATES)


@bp.route('/tenders/<int:tender_id>/advance', methods=['POST'])
@login_required
def advance_tender(tender_id):
    if not has_permission('tenders_list'):
        return redirect(url_for('main.dashboard'))

    conn = get_db()
    tender = conn.execute('SELECT workflow_state FROM tenders WHERE id = ?', (tender_id,)).fetchone()
    if not tender:
        conn.close()
        flash('Tender not found.', 'danger')
        return redirect(url_for('tenders.tenders_list'))

    current = tender['workflow_state']
    idx = WORKFLOW_STATES.index(current)

    if current not in ['opening_minute', 'evaluated', 'awarded'] and idx < len(WORKFLOW_STATES) - 1:
        next_state = WORKFLOW_STATES[idx + 1]
        conn.execute('UPDATE tenders SET workflow_state = ? WHERE id = ?', (next_state, tender_id))
        flash(f"Tender advanced to {next_state.replace('_', ' ').title()}.", 'info')
    elif current == 'opening_minute':
        if request.form.get('evaluation_complete'):
            conn.execute('UPDATE tenders SET workflow_state = ? WHERE id = ?', ('evaluated', tender_id))
            flash('Tender marked as Evaluated.', 'info')
        else:
            flash('Evaluation not complete.', 'danger')
    elif current == 'evaluated':
        result = request.form.get('result')
        awarded_to = request.form.get('awarded_to')
        award_date = request.form.get('award_date')
        if result == 'won' and awarded_to and award_date:
            conn.execute(
                'UPDATE tenders SET workflow_state = ?, result = ?, awarded_to = ?, award_date = ? WHERE id = ?',
                ('awarded', result, awarded_to, award_date, tender_id),
            )
            flash('Tender awarded.', 'success')
        elif result and result in ['defeat', 'rejected', 'cancelled']:
            conn.execute('UPDATE tenders SET result = ? WHERE id = ?', (result, tender_id))
            flash('Tender result recorded.', 'warning')
        else:
            flash('Result and award details required.', 'danger')
    else:
        flash('Tender already awarded.', 'info')

    conn.commit()
    conn.close()
    return redirect(url_for('tenders.tenders_list'))
