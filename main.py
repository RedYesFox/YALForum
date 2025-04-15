import datetime
import logging
from flask import Flask, render_template, redirect, request
from flask_login import current_user, login_required, LoginManager, login_user, logout_user
from flask_restful import abort

from data import db_session
from data.add_article import ArticlesForm
from data.articles import Articles
from data.login_form import LoginForm
from data.registration_form import RegisterForm
from data.users import User

application = Flask(__name__)
application.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
application.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=10
)

login_manager = LoginManager()
login_manager.init_app(application)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

sections = [
    {'title': 'Главная', 'url': '/'},
    {'title': 'О нас', 'url': '/about'},
    {'title': 'Контакты', 'url': '/contacts'},
    {'title': 'Регистрация', 'url': '/registration'},
    {'title': 'Авторизация', 'url': '/login'},
    {'title': 'Форум', 'url': '/forum'},
    {'title': 'Добавить статью', 'url': '/forum/articles/add'},
    {'title': 'Редактирование статьи', 'url': '/forum/articles/edit'},
    {'title': 'Удалить статью', 'url': '/forum/articles/delete'},
    {'title': 'Войти', 'url': '/login'},
    {'title': 'Выход', 'url': '/logout'}
]


@application.route('/')
def redirect_main():
    breadcrumbs = get_breadcrumbs(request.path)
    return render_template('main_page.html',
                           title='Главная',
                           breadcrumbs=breadcrumbs,
                           sections=sections)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@application.route('/about')
def about():
    breadcrumbs = get_breadcrumbs(request.path)
    return render_template('about.html',
                           title='О нас',
                           breadcrumbs=breadcrumbs)


@application.route('/contacts')
def contacts():
    breadcrumbs = get_breadcrumbs(request.path)
    return render_template('contacts.html',
                           title='Контакты',
                           breadcrumbs=breadcrumbs)


@application.route('/forum')
def forum_main():
    db_sess = db_session.create_session()
    articles = db_sess.query(Articles).all()
    breadcrumbs = get_breadcrumbs(request.path)
    return render_template("forum.html",
                           news=articles,
                           breadcrumbs=breadcrumbs,
                           sections=sections,
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
                           breadcrumbs=breadcrumbs)
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
                           form=form)


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
                           breadcrumbs=get_breadcrumbs(request.path)
                           )


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


@application.route('/forum/<forum_name>')
def forum(forum_name):
    breadcrumbs = get_breadcrumbs(request.path)
    return render_template('base.html',
                           title=f'Форум {forum_name.capitalize()}',
                           breadcrumbs=breadcrumbs,
                           sections=sections)


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
                                   form=form)

        return render_template('login.html',
                               message="Неправильный пароль",
                               breadcrumbs=breadcrumbs,
                               form=form)

    return render_template('login.html',
                           title='Авторизация',
                           breadcrumbs=breadcrumbs,
                           form=form)


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

        if form.age.data < 12 or form.age.data > 120:
            form.age.errors.append('Возраст должен быть в диапазоне от 12 до 120 лет.')
            return render_template('registration.html',
                                   title='Регистрация',
                                   form=form,
                                   breadcrumbs=breadcrumbs,
                                   message="Пожалуйста, введите корректный возраст.")
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
                surname=form.surname.data,
                name=form.name.data,
                age=form.age.data,
                position=form.position.data,
                speciality=form.speciality.data,
                address=form.address.data
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
                           form=form)


@application.errorhandler(Exception)
def handle_all_exceptions(e):
    return render_template('error.html', title='Ошибка', message=e), 500


@application.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', title='Ошибка', message='Страница не найдена'), 404


def get_breadcrumbs(path):
    parts = path.strip('/').split('/')
    breadcrumbs = [{'title': 'Главная', 'url': '/'}]
    temp_url = ""
    path_s = path.strip('/').split('/')
    for part in parts:
        temp_url += f'/{part}'
        section = next((s for s in sections if s['url'] == temp_url), None)
        if section:
            if breadcrumbs[-1]['title'] != section['title']:
                breadcrumbs.append({'title': section['title'], 'url': section['url']})
        else:
            breadcrumbs.append({'title': part.capitalize(), 'url': temp_url})

        l1 = [s for s in sections if s['url'] == f"/{'/'.join(path_s)}"]
        if l1:
            if breadcrumbs[-1]['title'] != l1[0]['title']:
                breadcrumbs.append({'title': l1[0]['title'], 'url': l1[0]['url']})
            break
        path_s.pop(-1)

    return breadcrumbs


def main():
    db_session.global_init("db/yforum.db")
    # db_sess = db_session.create_session()
    application.run(host='0.0.0.0')


if __name__ == '__main__':
    main()
