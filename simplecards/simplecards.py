from flask import (
    Blueprint, flash, g, session, redirect, render_template, request, url_for, jsonify, Response
)
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

from simplecards.auth import login_required
from simplecards.db import get_db

import csv
import io
import logging

bp = Blueprint('simplecards', __name__)

@bp.route('/')
@login_required
def index():
    lookup = request.args.get('lookup')
    db = get_db()
    if lookup == 'public':
        groups = db.execute(
            'SELECT g.id, owner_id, name, username'
            ' FROM groups g JOIN user u ON g.owner_id = u.id'
            ' WHERE g.public=1'
            ' ORDER BY name'
        ).fetchall()
    else:
        groups = db.execute(
            'SELECT g.id, owner_id, name, username'
            ' FROM groups g JOIN user u ON g.owner_id = u.id'
            ' WHERE g.owner_id=?'
            ' ORDER BY name',
            (str(session.get('user_id')), )
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

    if len(groups)==0:
        selected_group_id = None
        selected_deck_id = None
    elif not selection:
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
    if not group:
        selected_group_name = ''
        selected_group_owner_id = None
    else:
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

    for i, card in enumerate(cards):
        print(i, card['answer'])

    print('Index group:',selected_group_name)
    print('Index deck:',selected_deck_name)

    print(group['name'] for group in groups)
    
    return render_template('simplecards/index.html', 
                           groups=groups, 
                           selected_group_id = selected_group_id,
                           selected_group_name=selected_group_name,
                           selected_group_owner_id=selected_group_owner_id, 
                           selected_deck_id = selected_deck_id,
                           selected_deck_name=selected_deck_name, 
                           decks=decks, 
                           cards=cards,
                           view_name=lookup
                           )

# @bp.route('/owned')
# @login_required
# def owned():
#     return render_template('simplecards/owned.html')

@bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_csv():
    if request.method == 'POST':
        # Check if the file is in the request
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Check if a file was selected
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and file.filename.endswith('.csv'):
            filename = secure_filename(file.filename)  # Sanitize filename
            
            try:
                # Decode the uploaded file to a text stream
                stream = io.TextIOWrapper(file.stream, encoding='utf-8')
                csv_reader = csv.reader(stream)
                header = next(csv_reader)  # Read the header row

                # Verify correct CSV format
                if header != ["question", "answer", "deck_id", "public"]:
                    flash('Invalid CSV format. Please check the headers.')
                    return redirect(request.url)
                
                db = get_db()
                for row in csv_reader:
                    # Ensure the row has the correct number of fields
                    if len(row) != 4:
                        flash(f"Invalid row: {row}")
                        continue
                    
                    question, answer, deck_id, public = row
                    answer = answer.replace('\\n', '\n')
                    
                    # Insert the row into the database
                    db.execute(
                        "INSERT INTO card (question, answer, deck_id, public) VALUES (?, ?, ?, ?)",
                        (question, answer, int(deck_id), int(public))
                    )
                db.commit()
                flash('Cards imported successfully!')
            except Exception as e:
                flash(f"Error processing file: {e}")
                return redirect(request.url)
            
            return redirect(url_for('index', lookup='owned'))  # Redirect to home or another route


    
    return render_template('simplecards/import.html', view_name='import')

@bp.route('/export')
@login_required
def export():
    try:
        db = get_db()
        # Query data from the database
        rows = db.execute("SELECT question, answer, deck_id, public FROM card").fetchall()

        # Create CSV data in-memory
        def generate_csv():
            
            output = csv.StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_ALL)
            writer.writerow(["question", "answer", "deck_id", "public"])  # Write header
            for row in rows:
                logging.debug(f"Exported row: {row}")
                writer.writerow(
                    [row['question'],
                     row['answer'].replace('\n','\\n'),
                     row['deck_id'],
                     row['public']])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)

        # Send the CSV as a response
        return Response(
    generate_csv(),
    mimetype='text/csv',
    headers={"Content-Disposition": "attachment; filename=exported_cards.csv"}
)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
    return render_template('simplecards/export.html', view_name='export')

@bp.route('/settings')
@login_required
def settings():
    db = get_db()
    user_setting = db.execute(
        'SELECT *,'
        ' learn_mode.name as lm_name,'
        ' read_time.name as rt_name'
        ' FROM user_settings'
        ' JOIN learn_mode ON learn_mode_id=learn_mode.id'
        ' JOIN read_time ON read_time_id=read_time.id'
        ' WHERE user_id=?;',
        (str(session.get('user_id')), )
    ).fetchone()

    learn_modes = db.execute(
        'SELECT * FROM learn_mode;'
    ).fetchall()

    read_times = db.execute(
        'SELECT * FROM read_time;'
    ).fetchall()
    
    print('SETTING:', user_setting['user_id'])
    print('SETTING:', user_setting['ms_per_char'])
    print('SETTING:', user_setting['lm_name'])
    print('SETTING:', user_setting['rt_name'])

    
    return render_template(
        'simplecards/settings.html',
        view_name='settings',
        user_setting=user_setting,
        learn_modes=learn_modes,
        read_times=read_times
    )

@bp.route('/statistics')
@login_required
def statistics():
    db = get_db()
    data = db.execute(
        'SELECT learn_time, learned_cards FROM user'
        ' WHERE id=?;',
        (str(session.get('user_id')), )
    ).fetchone()
    learn_time = data['learn_time']/1000
    learned_cards = data['learned_cards']
    return render_template(
        'simplecards/statistics.html',
        view_name='statistics',
        learn_time=learn_time,
        learned_cards=learned_cards,
    )

@bp.route('/delete-learn-data/', methods=('POST',))
@login_required
def delete_learn_data():
    db = get_db()
    db.execute(
        'UPDATE user SET'
        ' learn_time=0,'
        ' learned_cards=0'
        ' where id=?;',
        (str(session.get('user_id')), )
    )
    db.commit()
    return redirect(url_for('simplecards.statistics'))

          

@bp.route('/create-group', methods=('GET', 'POST'))
@login_required
def create_group():
    if request.method == 'POST':
        name = request.form['name']
        public = 0
        if 'public' in request.form.keys():
            public = 1
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
        public = 0
        if 'public' in request.form.keys():
            public = 1
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
    print(f'Group with id {id} from table "groups" is deleted')
    return redirect(url_for('simplecards.index'))

@bp.route('/<int:id>/delete-deck')
@login_required
def delete_deck(id):
    db = get_db()
    
    db.execute(
        'DELETE FROM deck'
        ' WHERE id=?;',
        (str(id), )
    )
    db.commit()
    print(f'Deck with id {id} from table "deck" is deleted')
    return redirect(url_for('simplecards.index'))

@bp.route('/<int:id>/delete-card')
@login_required
def delete_card(id):
    db = get_db()
    
    db.execute(
        'DELETE FROM card'
        ' WHERE id=?;',
        (str(id), )
    )
    db.commit()
    print(f'Card with id {id} from table "card" is deleted')
    return redirect(url_for('simplecards.index'))

@bp.route('/<int:id>/learn_deck')
@login_required
def learn_deck(id):
    db = get_db()

    cards = db.execute(
        'SELECT * FROM card'
        ' WHERE deck_id=?',
        (id, )
    ).fetchall()
    card_list = [dict(card) for card in cards]
    return render_template('simplecards/learn.html', cards=card_list)

@bp.route('/save-learn', methods=('POST',))
@login_required
def save_learn():
    print('in save_learn')
    print('learn time:', request.form['learn_time'])
    print('learned cards:', request.form['learned_cards'])
    db = get_db()
    old_data = db.execute(
        'SELECT learn_time, learned_cards'
        ' FROM user'
        ' WHERE id=?;',
        (str(session.get('user_id')), )
    ).fetchone()
    print('old learn time:', old_data['learn_time'])
    print('old learned cards:', old_data['learned_cards'])
    new_learn_time = old_data['learn_time'] + int(request.form['learn_time'])
    new_learned_cards = old_data['learned_cards'] + int(request.form['learned_cards'])
    print('new learn time:', new_learn_time)
    print('new learned cards:', new_learned_cards)
    db.execute(
        'UPDATE user SET'
        ' learn_time=?,'
        ' learned_cards=?'
        ' where id=?;',
        (new_learn_time, new_learned_cards, str(session.get('user_id')))
    )
    db.commit()
    return request.url

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
        public = 0
        if 'public' in request.form.keys():
            public = 1
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

    if request.method == 'POST':

        question = request.form['question']
        answer = request.form['answer']
        public = 0
        if 'public' in request.form.keys():
            public = 1
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
        public = 0
        if 'public' in request.form.keys():
            public = 1
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
        public = 0
        if 'public' in request.form.keys():
            public = 1
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

    print('UPDATE CARD', 'card_answer:', card_answer)

    card_answer = card_answer.replace('\n','\n')
    
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
    lookup = request.args.get('lookup')
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
    return redirect(url_for('simplecards.index', lookup=lookup))

@bp.route('/<int:id>/select-deck', methods=('GET', 'POST'))
#@login_required
def select_deck(id):
    lookup = request.args.get('lookup')
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
    return redirect(url_for('simplecards.index', lookup=lookup))
