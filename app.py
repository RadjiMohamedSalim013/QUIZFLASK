from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash
from flask_babel import Babel
import secrets


import json

app = Flask(__name__)


secret_key = secrets.token_hex(32)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SECRET_KEY'] = secret_key



# Génération de la clé secrète hexadécimale

# Affectation de la clé secrète à la configuration de l'application




db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    score = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"User('{self.username}', '{self.score}')"
    

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    option_1 = db.Column(db.String(200), nullable=False)
    option_2 = db.Column(db.String(200), nullable=False)
    option_3 = db.Column(db.String(200), nullable=False)
    option_4 = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Question('{self.question_text}', '{self.option_1}', '{self.option_2}', '{self.option_3}', '{self.option_4}', '{self.correct_option}')"
    


@app.route('/')
def index():
    questions = Question.query.all()
    return render_template('index.html', questions=questions)

@app.route('/submit', methods=['POST'])
def submit():
    score = 0
    questions = Question.query.all()
    feedback = {}

    for question in questions:
        user_answer = request.form.get(str(question.id))
        if user_answer and int(user_answer) == question.correct_option:
            score += 1
            feedback[question.id] = 'Correct'
        else:
            feedback[question.id] = 'Incorrect'

    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()

    if user:
        user.score = score
        db.session.commit()
    else:
        new_user = User(username=username, score=score)
        db.session.add(new_user)
        db.session.commit()

    flash(f'Votre score est {score}', 'success')
    return render_template('feedback.html', feedback=feedback, score=score)






@app.route('/scores')
def scores():
    users = User.query.order_by(User.score.desc()).all()
    return render_template('scores.html', users=users)


@app.cli.command("load_questions")
def load_questions():
    with open('questions.json', 'r') as file:
        questions_data = json.load(file)
        
        for question_data in questions_data:
            question = Question(
                question_text=question_data['question_text'],
                option_1=question_data['option_1'],
                option_2=question_data['option_2'],
                option_3=question_data['option_3'],
                option_4=question_data['option_4'],
                correct_option=question_data['correct_option']
            )
            db.session.add(question)
        
        db.session.commit()




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Nom d\'utilisateur incorrect', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('Ce nom d\'utilisateur est déjà pris. Veuillez en choisir un autre.', 'danger')
        else:
            new_user = User(username=username)
            db.session.add(new_user)
            db.session.commit()
            flash('Inscription réussie ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')




@app.route('/admin/add_question', methods=['GET', 'POST'])
def add_questions():
    if request.method == 'POST':
        question_text = request.form['question_text']
        option_1 = request.form['option_1']
        option_2 = request.form['option_2']
        option_3 = request.form['option_3']
        option_4 = request.form['option_4']
        correct_option = int(request.form['correct_option'])

        new_question = Question(
            question_text=question_text,
            option_1=option_1,
            option_2=option_2,
            option_3=option_3,
            option_4=option_4,
            correct_option=correct_option
        )

        db.session.add(new_question)
        db.session.commit()
        
        flash('La question a été ajoutée avec succès.', 'success')
        return redirect(url_for('add_questions'))
    return render_template('add_question.html')


@app.route('/admin/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)

    if request.method == 'POST':
        question.question_text = request.form['question_text']
        question.option_1 = request.form['option_1']
        question.option_2 = request.form['option_2']
        question.option_3 = request.form['option_3']
        question.option_4 = request.form['option_4']
        question.correct_option = int(request.form['correct_option'])
        
        db.session.commit()
        
        flash('La question a été modifiée avec succès.', 'success')
        return redirect(url_for('edit_question', question_id=question.id))
    
    return render_template('edit_question.html', question=question)


@app.route('/admin/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    
    db.session.delete(question)
    db.session.commit()
    
    flash('La question a été supprimée avec succès.', 'success')
    return redirect(url_for('index'))



@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500






with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        admin.score = 0
        db.session.commit()
    else:
        # Si l'utilisateur 'admin' n'existe pas, vous pouvez créer un nouvel administrateur
        new_admin = User(username='admin', score=0)
        db.session.add(new_admin)
        db.session.commit()




@app.cli.command("init-db")
def init_db():
    db.create_all()
    print('Base de données initialisée.')






if __name__ == '__main__':
    app.run(debug=True)
