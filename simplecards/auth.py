import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from simplecards.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        repeat_password = request.form['repeat_password']
        db = get_db()
        cursor = db.cursor()
        error = None

        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif not repeat_password:
            error = 'Repeat password is required.'
        elif not password == repeat_password:
            error = 'Password and repeat password are not equal.' 
        print(error)

        if error is None:
            try:
                sql = "INSERT INTO user (username, email, password, role_id) VALUES (?, ?, ?, ?)"
                cursor.execute(
                    sql,
                    (username, email, generate_password_hash(password), "normal"),
                )
                last_row_id = cursor.lastrowid
                print('LAST ROW IS:', last_row_id)
                sql_user_settings = 'INSERT INTO user_settings (user_id) VALUES (?);'
                cursor.execute(
                    sql_user_settings,
                    (last_row_id, )
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username or password.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect username or password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            print("in auth/login before selection insert")
            db.execute(
                'INSERT INTO user_selections'
                ' (user_id, selected_group_id, selected_deck_id)'
                ' VALUES'
                ' (?, 1, 1)'
                ' ON CONFLICT(user_id) DO UPDATE SET'
                ' selected_group_id=1,'
                ' selected_deck_id=1;',
                (user['id'], )
            )
            db.commit()
            print("in auth/login after selection insert")
            return redirect(url_for('index', lookup='owned'))

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
