from flask import Flask, render_template, redirect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

sections = [
    {'title': 'Главная', 'url': '/main'},
    {'title': 'О нас', 'url': '/about'},
    {'title': 'Контакты', 'url': '/contacts'},
    {'title': 'Регистрация', 'url': '/registration'},
    {'title': 'Авторизация', 'url': '/login'},
    {'title': 'Форум', 'url': '/forum'},
    {'title': 'Форум Python', 'url': '/forum/python'},
    {'title': 'Форум Flask', 'url': '/forum/flask'},
    {'title': 'Форум Django', 'url': '/forum/django'}
]


@app.route('/<title>')
@app.route('/index/<title>')
def index(title):
    forum_title = f'{title}'
    forum_info = next((section for section in sections if section['url'] == f"/{forum_title}"),
                      None)
    return render_template('base.html', title=forum_info['title'], path_to_post=forum_info,
                           sections=sections)


@app.route('/forum/<forum_name>')
def forum(forum_name):
    forum_title = f'Форум {forum_name.capitalize()}'
    forum_info = next((section for section in sections if section['title'] == forum_title), None)

    return render_template('base.html', title=forum_title, path_to_post=forum_info,
                           sections=sections)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', title='Ошибка 404', message=e), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', title='Ошибка 500',
                           message='Internal Server Error: Something went wrong!'), 500


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
