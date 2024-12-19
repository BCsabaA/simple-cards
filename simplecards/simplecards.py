from flask import (
    Blueprint, flash, g, session, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from simplecards.auth import login_required
from simplecards.db import get_db

bp = Blueprint('simplecards', __name__)

@bp.route('/')
@login_required
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
    if not deck:
        selected_deck_name = ""
    else:
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

    print(group['name'] for group in groups)
    
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

@bp.route('/<int:id>/update-group', methods=('GET', 'POST'))
@login_required
def update_group(id):
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        public = 1 if request.form['public'] else 0
        print(request.form['public'])
        print(public)
        error = None
        deleted = 0

        if not name:
            error = 'Name is required.'

        if error is not None:
            flash(error)
        else:
            db.execute(
                'UPDATE groups SET'
                ' name=?,'
                ' public=?'
                ' WHERE id=?',
                (name, public, id)
            )
            db.commit()
            return redirect(url_for('simplecards.index'))

    group = db.execute(
        'SELECT * FROM groups'
        ' WHERE id=?;',
        (id, )
        ).fetchone()
    group_name = group['name']
    group_public = True if group['public']==1 else False

    print('UPDATE GROUP NAME', group_name)
    print('UPDATE GROUP PUBLIC', group_public)

    return render_template('simplecards/update-group.html', name=group_name, public=group_public)

@bp.route('/<int:id>/delete-group')
@login_required
def delete_group(id):
    db = get_db()
    
    db.execute(
        'DELETE FROM groups'
        ' WHERE id=?;',
        (str(id), )
    )
    db.commit()
    print(f'Object with id {id} from table "groups" is deleted')
    return redirect(url_for('simplecards.index'))



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

@bp.route('/<int:id>/update-deck', methods=('GET', 'POST'))
@login_required
def update_deck(id):
    db = get_db()

    if request.method == 'POST':
        name = request.form['name']
        public = 1 if request.form['public'] else 0
        print(request.form['public'])
        print(public)
        error = None
        deleted = 0

        if not name:
            error = 'Name is required.'

        if error is not None:
            flash(error)
        else:
            db.execute(
                'UPDATE deck SET'
                ' name=?,'
                ' public=?'
                ' WHERE id=?',
                (name, public, id)
            )
            db.commit()
            return redirect(url_for('simplecards.index'))
    
    deck = db.execute(
        'SELECT *, groups.name AS g_name, groups.id AS g_id'
        ' FROM deck'
        ' JOIN groups ON deck.group_id=groups.id'
        ' WHERE deck.id=?;',
        (id, )
        ).fetchone()

    deck_name = deck['name']
    deck_public = deck['public']
    group_name = deck['g_name']
    

    print('UPDATE DECK deck:', deck_name)
    print('UPDATE DECK group:', group_name)

    for key in deck.keys():
        print(key)

    return render_template(
        'simplecards/update-deck.html',
        deck_id=id,
        deck_name=deck_name,
        deck_public=deck_public,
        group_name=group_name
        )

@bp.route('/<int:id>/update-card', methods=('GET', 'POST'))
@login_required
def update_card(id):
    db = get_db()

    if request.method == 'POST':
        question = request.form['question']
        answer = request.form['answer']
        public = 1 if request.form['public'] else 0
        print(request.form['public'])
        print(public)
        error = None
        deleted = 0

        if not question or not answer:
            error = 'Question and answer both are are required.'

        if error is not None:
            flash(error)
        else:
            db.execute(
                'UPDATE card SET'
                ' question=?,'
                ' answer=?,'
                ' public=?'
                ' WHERE id=?',
                (question, answer, public, id)
            )
            db.commit()
            return redirect(url_for('simplecards.index'))
    
    card = db.execute(
        'SELECT *, deck.name AS d_name, deck.id AS d_id'
        ' FROM card'
        ' JOIN deck ON card.deck_id=deck.id'
        ' WHERE card.id=?;',
        (id, )
        ).fetchone()
    
    deck = db.execute(
        'SELECT *, groups.name AS g_name, groups.id AS g_id'
        ' FROM deck'
        ' JOIN groups ON deck.group_id=groups.id'
        ' WHERE deck.id=?;',
        (card['deck_id'], )
        ).fetchone()

    card_question = card['question']
    card_answer = card['answer']
    card_public = card['public']
    deck_name = card['d_name']
    group_name = deck['g_name']
    

    print('UPDATE CARD question:', card_question)
    print('UPDATE CARD answer:', card_answer)
    print('UPDATE CARD deck:', deck_name)

    for key in card.keys():
        print(key)

    return render_template(
        'simplecards/update-card.html',
        card_id=id,
        card_question=card_question,
        card_answer=card_answer,
        card_public=card_public,
        deck_name=deck_name,
        group_name=group_name
        )

@bp.route('/<int:id>/select-group', methods=('GET', 'POST'))
#@login_required
def select_group(id):
    db = get_db()
    user_id = str(session.get('user_id'))
    print('select-group user id:', user_id)
    print('select-group group id:', id)
    first_deck_id = db.execute(
        'SELECT id FROM deck'
        ' WHERE group_id=?;',
        (id, )
    ).fetchone()

    if not first_deck_id:
        first_deck_id = 0
    else:
        first_deck_id = first_deck_id['id']

    db.execute(
        'UPDATE user_selections'
        ' SET'
        ' selected_group_id=?,'
        ' selected_deck_id=?'
        ' WHERE user_id=?;',
        (id, first_deck_id, user_id, )
    )
    db.commit()
    return redirect(url_for('simplecards.index'))

@bp.route('/<int:id>/select-deck', methods=('GET', 'POST'))
#@login_required
def select_deck(id):
    db = get_db()
    user_id = str(session.get('user_id'))
    print('select-deck user id:', user_id)
    print('select-deck deck id:', id)
  

    db.execute(
        'UPDATE user_selections'
        ' SET'
        ' selected_deck_id=?'
        ' WHERE user_id=?;',
        (id, user_id, )
    )
    db.commit()
    return redirect(url_for('simplecards.index'))
