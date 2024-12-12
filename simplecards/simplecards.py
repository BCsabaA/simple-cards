from flask import (
    Blueprint, flash, g, session, redirect, render_template, request, url_for
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

    selected_group_id = 1
    selected_deck_id = 1

    #if len(groups) > 0:
    selection = db.execute(
        'SELECT *'
        ' FROM user_selections'
        ' WHERE user_id = ?',
        (str(session.get('user_id')), )
    ).fetchone()
    if not selection:
        selected_group_id = 1
        selected_deck_id = 1
    else:
        selected_group_id = selection['selected_group_id']
        selected_deck_id =selection['selected_deck_id']
    
    group = db.execute(
        'SELECT *'
        ' FROM groups'
        ' WHERE id = ?',
        (str(selected_group_id), )
    ).fetchone()
    selected_group_name = group['name']
    selected_group_owner_id = group['owner_id']

    deck = db.execute(
        'SELECT *'
        ' FROM deck'
        ' WHERE id = ?',
        (str(selected_deck_id), )
    ).fetchone()
    selected_deck_name = deck['name']

    decks = db.execute(
        'SELECT *'
        ' FROM deck d'
        ' WHERE public=1 AND group_id=(?)'
        ' ORDER BY name',
        (str(selected_group_id), )
    ).fetchall()

    cards = db.execute(
        'SELECT *'
        ' FROM card'
        ' WHERE public=1 and deck_id=(?)',
        (str(selected_deck_id), )
    ).fetchall()

    print('Index group:',selected_group_name)
    print('Index deck:',selected_deck_name)
    
    return render_template('simplecards/index.html', 
                           groups=groups, 
                           selected_group_id = selected_group_id, selected_group_name=selected_group_name,
                           selected_group_owner_id=selected_group_owner_id, 
                           selected_deck_id = selected_deck_id, selected_deck_name=selected_deck_name, 
                           decks=decks, 
                           cards=cards
                           )

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

@bp.route('/create-group', methods=('GET', 'POST'))
@login_required
def create_group():
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

    return render_template('simplecards/create-group.html')

@bp.route('/create-deck', methods=('GET', 'POST'))
@login_required
def create_deck():
    db = get_db()
    selection = db.execute(
        'SELECT *'
        ' FROM user_selections'
        ' WHERE user_id = ?',
        (str(session.get('user_id')), )
    ).fetchone()
    selected_group_id = selection['selected_group_id']
    group = db.execute(
        'SELECT *'
        ' FROM groups'
        ' WHERE id = ?',
        (str(selected_group_id), )
    ).fetchone()
    selected_group_name = group['name']
    print('create_deck id:',selected_group_id)
    print('create_deck name:',selected_group_name)

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
            db.execute(
                'INSERT INTO deck (group_id, name, public, deleted)'
                ' VALUES (?, ?, ?, ?)',
                (selected_group_id, name, public, deleted)
            )
            db.commit()
            return redirect(url_for('simplecards.index'))

    return render_template('simplecards/create-deck.html', selected_group_id=selected_group_id, selected_group_name=selected_group_name)

@bp.route('/create-card', methods=('GET', 'POST'))
@login_required
def create_card():
    db = get_db()
    selection = db.execute(
        'SELECT *'
        ' FROM user_selections'
        ' WHERE user_id = ?',
        (str(session.get('user_id')), )
    ).fetchone()
    selected_group_id = selection['selected_group_id']
    selected_deck_id = selection['selected_deck_id']

    group = db.execute(
        'SELECT *'
        ' FROM groups'
        ' WHERE id = ?',
        (str(selected_group_id), )
    ).fetchone()
    selected_group_name = group['name']

    deck = db.execute(
        'SELECT *'
        ' FROM deck'
        ' WHERE id = ?',
        (str(selected_deck_id), )
    ).fetchone()
    selected_deck_name = deck['name']

    print('create_deck group id:',selected_group_id)
    print('create_deck group name:',selected_group_name)
    print('create_deck deck id:',selected_deck_id)
    print('create_deck deck name:',selected_deck_name)

    if request.method == 'POST':


        question = request.form['question']
        answer = request.form['answer']
        public = 1 if request.form['public'] else 0
        error = None
        deleted = 0

        if not question or not answer:
            error = 'Question and answer both are required.'

        if error is not None:
            flash(error)
        else:
            db.execute(
                'INSERT INTO card (deck_id, question, answer, public, deleted)'
                ' VALUES (?, ?, ?, ?, ?)',
                (selected_deck_id, question, answer, public, deleted)
            )
            db.commit()
            return redirect(url_for('simplecards.index'))

    return render_template(
        'simplecards/create-card.html', 
        selected_group_id=selected_group_id, 
        selected_group_name=selected_group_name,
        selected_deck_id=selected_deck_id,
        selected_deck_name=selected_deck_name
        )



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