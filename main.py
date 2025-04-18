import datetime
import logging
import os
import uuid
from flask import Flask, render_template, redirect, request
from flask_login import current_user, login_required, LoginManager, login_user, logout_user
from flask_restful import abort
from werkzeug.utils import secure_filename

from data import db_session
from data.add_article import ArticlesForm
from data.articles import Articles
from data.edit_profil_form import EditProfileForm
from data.login_form import LoginForm
from data.registration_form import RegisterForm
from data.users import User

application = Flask(__name__)
application.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
application.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=10
)
application.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

login_manager = LoginManager()
login_manager.init_app(application)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

sections = [
    {'title': 'Главная', 'url': '/'},
    {'title': 'Форум', 'url': '/forum'},
    {'title': 'Добавить статью', 'url': '/forum/articles/add'},
    {'title': 'О нас', 'url': '/about'},
    {'title': 'Контакты', 'url': '/contacts'},
    {'title': 'Регистрация', 'url': '/registration'},
    {'title': 'Авторизация', 'url': '/login'},
    {'title': 'Профиль пользователя', 'url': '/profile'},
    {'title': 'Редактирование статьи', 'url': '/forum/articles/edit'},
    {'title': 'Удалить статью', 'url': '/forum/articles/delete'}
]

sections_limiter = -3


@application.route('/')
def redirect_main():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    breadcrumbs = get_breadcrumbs(request.path)
    return render_template('main_page.html',
                           title='Главная',
                           breadcrumbs=breadcrumbs,
                           users=users,
                           sections=sections[:sections_limiter])


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@application.route('/about')
def about():
    breadcrumbs = get_breadcrumbs(request.path)
    return render_template('about.html',
                           title='О нас',
                           breadcrumbs=breadcrumbs,
                           sections=sections[:sections_limiter])


@application.route('/contacts')
def contacts():
    breadcrumbs = get_breadcrumbs(request.path)
    return render_template('contacts.html',
                           title='Контакты',
                           breadcrumbs=breadcrumbs,
                           sections=sections[:sections_limiter])


@application.route('/forum')
def forum_main():
    db_sess = db_session.create_session()
    articles = db_sess.query(Articles).all()
    breadcrumbs = get_breadcrumbs(request.path)
    return render_template("forum.html",
                           articles=articles,
                           breadcrumbs=breadcrumbs,
                           sections=sections[:sections_limiter],
                           title='Форум')


@application.route('/forum/articles/<int:id>')
def article(id):
    db_sess = db_session.create_session()
    article = db_sess.query(Articles).filter(Articles.id == id).first()
    if not article:
        abort(404)
    breadcrumbs = get_breadcrumbs(request.path)

    return render_template('article.html',
                           article=article,
                           breadcrumbs=breadcrumbs,
                           sections=sections[:sections_limiter])
    # if current_user.is_authenticated:
    #     articles = db_sess.query(Articles).filter(
    #         (Articles.user == current_user) | (Articles.is_private.like(0)))
    # else:
    #     articles = db_sess.query(Articles).filter(Articles.is_private.like(0))
    # breadcrumbs = get_breadcrumbs(request.path)
    # return render_template("forum.html",
    #                        news=articles,
    #                        breadcrumbs=breadcrumbs,
    #                        sections=sections,
    #                        title=)


@application.route('/forum/articles/add',  methods=['GET', 'POST'])
@login_required
def add_articles():
    breadcrumbs = get_breadcrumbs(request.path)
    form = ArticlesForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        articles = Articles()
        articles.title = form.title.data
        articles.content = form.content.data
        articles.category = form.category.data
        articles.user_id = current_user.id
        db_sess.add(articles)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/forum')
    return render_template('index.html',
                           title='Добавление статьи',
                           breadcrumbs=breadcrumbs,
                           form=form,
                           sections=sections[:sections_limiter])


@application.route('/forum/articles/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_articles(id):
    form = ArticlesForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        articles = db_sess.query(Articles).filter(Articles.id == id,
                                                  Articles.user == current_user
                                                  ).first()
        if articles:
            form.title.data = articles.title
            form.content.data = articles.content
            form.category.data = articles.category
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        articles = db_sess.query(Articles).filter(Articles.id == id,
                                                  Articles.user == current_user
                                                  ).first()
        if articles:
            articles.title = form.title.data
            articles.content = form.content.data
            articles.category = form.category.data
            db_sess.commit()
            return redirect('/forum')
        else:
            abort(404)
    return render_template('index.html',
                           title='Редактирование статьи',
                           form=form,
                           breadcrumbs=get_breadcrumbs(request.path),
                           sections=sections[:sections_limiter])


@application.route('/forum/articles/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def articles_delete(id):
    db_sess = db_session.create_session()
    articles = db_sess.query(Articles).filter(Articles.id == id,
                                              Articles.user == current_user
                                              ).first()
    if articles:
        db_sess.delete(articles)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/forum')


# @application.route('/forum/<forum_name>')
# def forum(forum_name):
#     breadcrumbs = get_breadcrumbs(request.path)
#     return render_template('base.html',
#                            title=f'Форум {forum_name.capitalize()}',
#                            breadcrumbs=breadcrumbs,
#                            sections=sections[:sections_limiter])


@application.route('/profile/<username>', methods=['GET', 'POST'])
def profile(username):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.username == username).first()
    if not user:
        abort(404)

    form = EditProfileForm(obj=user)
    edit_mode = request.args.get('edit') == '1'

    if form.validate_on_submit() and user.id == current_user.id:
        file = form.photo.data
        if file and file.filename:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(application.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

            if user.photo and isinstance(user.photo, str):
                old_path = os.path.join(application.static_folder, user.photo.replace('/', os.sep))

                print(old_path)
                if os.path.exists(old_path):
                    os.remove(old_path)

            user.photo = os.path.join('uploads', unique_filename).replace('\\', '/')
        user.name = form.name.data
        user.surname = form.surname.data
        user.age = form.age.data
        user.position = form.position.data
        user.speciality = form.speciality.data
        user.address = form.address.data

        db_sess.commit()
        return redirect(f'/profile/{username}')

    breadcrumbs = get_breadcrumbs(request.path)

    return render_template("profile.html",
                           user=user,
                           form=form,
                           edit_mode=edit_mode,
                           title=user.username,
                           breadcrumbs=breadcrumbs,
                           sections=sections[:sections_limiter])


@application.route('/login', methods=['GET', 'POST'])
def login():
    breadcrumbs = get_breadcrumbs(request.path)
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')

        if user is None:
            return render_template('login.html',
                                   message="Пользователь не найден",
                                   breadcrumbs=breadcrumbs,
                                   form=form,
                                   sections=sections[:sections_limiter])

        return render_template('login.html',
                               message="Неправильный пароль",
                               breadcrumbs=breadcrumbs,
                               form=form,
                               sections=sections[:sections_limiter])

    return render_template('login.html',
                           title='Авторизация',
                           breadcrumbs=breadcrumbs,
                           form=form,
                           sections=sections[:sections_limiter])


@application.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@application.route('/change_account')
@login_required
def change_profile():
    logout_user()
    return redirect('/login')


@application.route('/registration', methods=['GET', 'POST'])
def registration():
    breadcrumbs = get_breadcrumbs(request.path)
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            form.confirm_password.errors.append('Пароли не совпадают')
            return render_template('registration.html',
                                   title='Регистрация',
                                   form=form,
                                   breadcrumbs=breadcrumbs,
                                   message="Пароли не совпадают")

        # if form.age.data < 12 or form.age.data > 120:
        #     form.age.errors.append('Возраст должен быть в диапазоне от 12 до 120 лет.')
        #     return render_template('registration.html',
        #                            title='Регистрация',
        #                            form=form,
        #                            breadcrumbs=breadcrumbs,
        #                            message="Пожалуйста, введите корректный возраст.")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('registration.html',
                                   title='Регистрация',
                                   form=form,
                                   breadcrumbs=breadcrumbs,
                                   message="Такой пользователь уже есть")
        try:
            user = User(
                email=form.email.data,
                username=form.username.data
                # surname=form.surname.data,
                # name=form.name.data,
                # age=form.age.data,
                # position=form.position.data,
                # speciality=form.speciality.data,
                # address=form.address.data
            )

            user.set_password(form.password.data)
            db_sess.add(user)
            db_sess.commit()
            return redirect('/login')
        except Exception as e:
            logging.error(f"Ошибка при регистрации пользователя: {e}")
            return render_template('registration.html',
                                   title='Регистрация',
                                   form=form,
                                   breadcrumbs=breadcrumbs,
                                   message="Произошла ошибка при регистрации. Попробуйте еще раз.")
    return render_template('registration.html',
                           title='Регистрация',
                           breadcrumbs=breadcrumbs,
                           form=form,
                           sections=sections[:sections_limiter])


@application.errorhandler(Exception)
def handle_all_exceptions(e):
    return render_template('error.html',
                           title='Ошибка',
                           message=e,
                           sections=sections[:sections_limiter]), 500


@application.errorhandler(401)
def unauthorized(e):
    return redirect('/login')


@application.errorhandler(404)
def page_not_found(e):
    return render_template('error.html',
                           title='Ошибка',
                           message='Страница не найдена',
                           sections=sections[:sections_limiter]), 404


def get_breadcrumbs(path):
    breadcrumbs = [{'title': 'Главная', 'url': '/'}]
    path_parts = path.strip('/').split('/')
    full_url = ''

    for i in range(len(path_parts)):
        full_url = '/' + '/'.join(path_parts[:i + 1])
        match = next((s for s in sections if s['url'] == full_url), None)
        if match:
            if not any(b['url'] == match['url'] for b in breadcrumbs):
                breadcrumbs.append({'title': match['title'], 'url': match['url']})

    if not any(b['url'] == path for b in breadcrumbs):
        breadcrumbs.append({'title': path_parts[-1].capitalize(), 'url': path})
    return breadcrumbs


def main():
    db_session.global_init("db/yforum.db")
    # db_sess = db_session.create_session()
    application.run(host='0.0.0.0')


if __name__ == '__main__':
    main()
