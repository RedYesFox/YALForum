import datetime
import logging
import os
import uuid
from flask import Flask, render_template, redirect, request, url_for, abort
from flask_login import current_user, login_required, LoginManager, login_user, logout_user
# from flask_restful import abort
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from data import db_session
from data.add_article import ArticlesForm
from data.articles import Articles
from data.edit_profil_form import EditProfileForm
from data.login_form import LoginForm
from data.registration_form import RegisterForm
from data.users import User
from data.comment_form import CommentForm
from data.comments import Comment
from data.feedback_form import FeedbackForm
from data.feedbacks import Feedback

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
    {'title': 'Профиль', 'url': '/profile'},
    {'title': 'Форум', 'url': '/forum'},
    {'title': 'Друзья', 'url': '/friends'},
    {'title': 'Подписки', 'url': '/subscriptions'},
    {'title': 'О нас', 'url': '/about'},
    {'title': 'Обратная связь', 'url': '/feedback'},
    {'title': 'Главная', 'url': '/'},
    {'title': 'Добавить тему', 'url': '/forum/articles/add'},
    {'title': 'Регистрация', 'url': '/registration'},
    {'title': 'Авторизация', 'url': '/login'},
    {'title': 'Профиль пользователя', 'url': '/profile'},
    {'title': 'Редактирование темы', 'url': '/forum/articles/edit'},
    {'title': 'Удалить тему', 'url': '/forum/articles/delete'}
]

sections_limiter = -7


@application.route('/')
def redirect_main():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    return render_template('main_page.html',
                           title='Главная',
                           users=users,
                           sections=sections[:sections_limiter])


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@application.route('/about')
def about():
    return render_template('about.html',
                           title='О нас',
                           sections=sections[:sections_limiter])


@application.route('/feedback',  methods=['GET', 'POST'])
def feedback():
    db_sess = db_session.create_session()

    form = FeedbackForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        feedback = Feedback(
            content=form.content.data,
            user_id=current_user.id
        )
        db_sess.add(feedback)
        db_sess.commit()
        return redirect('/feedback')

    return render_template('feedback.html',
                           title='Feedback',
                           sections=sections[:sections_limiter],
                           form=form)


@application.route('/forum')
def forum_main():
    db_sess = db_session.create_session()
    query = request.args.get('q', '').strip()
    author = request.args.get('author')
    sort = request.args.get('sort', 'newest')
    category = request.args.get('category', '').strip()

    all_categories = sorted({a.category for a in db_sess.query(Articles).all() if a.category})

    articles_query = db_sess.query(Articles)

    if query:
        articles_query = articles_query.filter(
            (Articles.title.ilike(f'%{query}%')) |
            (Articles.content.ilike(f'%{query}%')) |
            (Articles.category.ilike(f'%{query}%'))
        )

    if category:
        articles_query = articles_query.filter(Articles.category == category)

    if author:
        articles_query = articles_query.join(Articles.user).filter(User.username == author)
    if sort == 'oldest':
        articles_query = articles_query.order_by(Articles.created_date.asc())
    else:
        articles_query = articles_query.order_by(Articles.created_date.desc())
    articles = articles_query.all()
    all_users = db_sess.query(User).order_by(User.username).all()

    return render_template("forum.html",
                           articles=articles,
                           sections=sections[:sections_limiter],
                           users=all_users,
                           all_categories=all_categories,
                           title='Forum')


@application.route('/forum/articles/<int:id>', methods=['GET', 'POST'])
def article(id):
    db_sess = db_session.create_session()
    article = db_sess.query(Articles).filter(Articles.id == id).first()
    if not article:
        abort(404)

    comments = db_sess.query(Comment).filter(
        Comment.article_id == article.id).order_by(Comment.created_date.desc()).all()

    form = CommentForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        new_comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            article_id=article.id
        )
        db_sess.add(new_comment)
        db_sess.commit()
        return redirect(f'/forum/articles/{id}')

    return render_template('article.html',
                           article=article,
                           form=form,
                           comments=comments,
                           title=article.title,
                           sections=sections[:sections_limiter])


@application.route('/forum/articles/add', methods=['GET', 'POST'])
@login_required
def add_articles():
    db_sess = db_session.create_session()
    form = ArticlesForm()

    all_categories = sorted({a.category for a in db_sess.query(Articles).all() if a.category})

    if form.validate_on_submit():
        articles = Articles()
        articles.title = form.title.data
        articles.content = form.content.data
        articles.category = form.category.data
        articles.user_id = current_user.id
        db_sess.add(articles)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/forum')

    return render_template('add_article.html',
                           title='Добавление темы',
                           form=form,
                           sections=sections[:sections_limiter],
                           all_categories=all_categories)


@application.route('/forum/articles/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_articles(id):
    form = ArticlesForm()
    db_sess = db_session.create_session()

    # собираем все уникальные категории
    all_categories = sorted({a.category for a in db_sess.query(Articles).all() if a.category})

    if request.method == "GET":
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

    return render_template('add_article.html',
                           title='Редактирование темы',
                           form=form,
                           sections=sections[:sections_limiter],
                           all_categories=all_categories)


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


@application.route('/profile')
def self_profile():
    if current_user.is_authenticated:
        return redirect(f'/profile/{current_user.username}')
    return redirect('/login')


@application.route('/profile/<username>', methods=['GET', 'POST'])
def profile(username):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.username == username).first()
    if not user:
        abort(404)

    form = EditProfileForm(obj=user)
    friends = get_mutual_friends(user)
    edit_mode = request.args.get('edit') == '1'

    if form.validate_on_submit() and user.id == current_user.id:
        if form.age.data <= 10 or form.age.data >= 100:
            form.age.errors.append('Возраст должен быть в диапазоне от 10 до 100 лет.')
            return render_template('profile.html',
                                   form=form,
                                   edit_mode=edit_mode,
                                   title=user.username,
                                   user=user,
                                   message="Пожалуйста, введите корректный возраст.")
        file = form.photo.data
        if isinstance(file, FileStorage) and file.filename:
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
        user.about = form.about.data
        user.position = form.position.data
        user.speciality = form.speciality.data
        user.address = form.address.data

        db_sess.commit()
        return redirect(f'/profile/{username}')

    return render_template("profile.html",
                           user=user,
                           form=form,
                           edit_mode=edit_mode,
                           title=user.username,
                           sections=sections[:sections_limiter],
                           friends=friends)


@application.route('/subscribe/<int:user_id>', methods=['POST'])
@login_required
def subscribe(user_id):
    db_sess = db_session.create_session()
    target = db_sess.query(User).get(user_id)
    me = db_sess.query(User).get(current_user.id)

    if not target or target.id == current_user.id:
        abort(404)

    if target not in me.subscriptions:
        me.subscriptions.append(target)
        db_sess.commit()

    return redirect(url_for('profile', username=target.username))


@application.route('/unsubscribe/<int:user_id>', methods=['POST'])
@login_required
def unsubscribe(user_id):
    db_sess = db_session.create_session()
    target = db_sess.query(User).get(user_id)
    me = db_sess.query(User).get(current_user.id)

    if not target or target.id == current_user.id:
        abort(404)

    if target in me.subscriptions:
        me.subscriptions.remove(target)
        db_sess.commit()

    return redirect(url_for('profile', username=target.username))


@application.route('/login', methods=['GET', 'POST'])
def login():
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
                                   form=form,
                                   sections=sections[:sections_limiter])

        return render_template('login.html',
                               message="Неправильный пароль",
                               form=form,
                               sections=sections[:sections_limiter])

    return render_template('login.html',
                           title='Авторизация',
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


@application.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = current_user
    db_sess = db_session.create_session()
    user = db_sess.merge(user)

    user.subscriptions.clear()
    user.subscribers.clear()

    db_sess.delete(user)
    db_sess.commit()
    logout_user()
    return redirect('/')


@application.route('/registration', methods=['GET', 'POST'])
def registration():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            form.confirm_password.errors.append('Пароли не совпадают')
            return render_template('registration.html',
                                   title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")

        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('registration.html',
                                   title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")

        if db_sess.query(User).filter(User.username == form.username.data).first():
            return render_template('registration.html',
                                   title='Регистрация',
                                   form=form,
                                   message="Логин занят")
        try:
            user = User(
                email=form.email.data,
                username=form.username.data
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
                                   message="Произошла ошибка при регистрации. Попробуйте еще раз.")
    return render_template('registration.html',
                           title='Регистрация',
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


@application.template_filter('time_ago')
def time_ago(dt):
    now = datetime.datetime.now()
    diff = now - dt

    if diff.days >= 1:
        return f"{diff.days} дн. назад"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours} ч. назад"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes} мин. назад"
    else:
        return "только что"


def get_mutual_friends(user: User) -> list[User]:
    following_ids = {u.id for u in user.subscriptions}
    follower_ids = {u.id for u in user.subscribers}
    mutual_ids = following_ids & follower_ids
    return [u for u in user.subscriptions if u.id in mutual_ids]


def main():
    db_session.global_init("db/yforum.db")
    # db_sess = db_session.create_session()
    application.run(host='0.0.0.0')


if __name__ == '__main__':
    main()
