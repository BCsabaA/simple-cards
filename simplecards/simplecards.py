from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from simplecards.auth import login_required
from simplecards.db import get_db

bp = Blueprint('simplecards', __name__)

@bp.route('/')
def index():
    db = get_db()
    groups = db.execute(
        'SELECT g.id, owner_id, name, username'
        ' FROM groups g JOIN user u ON g.owner_id = u.id'
        ' WHERE g.public=1'
        ' ORDER BY name'
    ).fetchall()
    return render_template('simplecards/index.html', groups=groups)

@bp.route('/owned')
@login_required
def owned():
    return render_template('simplecards/owned.html')

@bp.route('/import')
@login_required
def import_csv():
    return render_template('simplecards/import.html')

@bp.route('/export')
@login_required
def export():
    return render_template('simplecards/export.html')

@bp.route('/settings')
@login_required
def settings():
    return render_template('simplecards/settings.html')

@bp.route('/statistics')
@login_required
def statistics():
    return render_template('simplecards/statistics.html')

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        public = 1 if request.form['public'] else 0
        error = None
        deleted = 0

        if not name:
            error = 'Name is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO groups (owner_id, name, public, deleted)'
                ' VALUES (?, ?, ?, ?)',
                (g.user['id'], name, public, deleted)
            )
            db.commit()
            return redirect(url_for('simplecards.index'))

    return render_template('simplecards/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('simplecards/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('simplecards.index'))