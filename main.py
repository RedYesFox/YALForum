import datetime
import os
import uuid
from flask import Flask, render_template, redirect, request, url_for, abort
from flask_login import current_user, login_required, LoginManager, login_user, logout_user
from sqlalchemy import func
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
from data.votes import ArticleVote

application = Flask(__name__)  # создаем приложение
application.config['SECRET_KEY'] = 'yandexlyceum_secret_key'  # ключ для шифрования
application.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=10)  # установка срока действия сессии
application.config['UPLOAD_FOLDER'] = os.path.join(
    'static', 'uploads')  # папка для загрузки файлов

login_manager = LoginManager()  # создаем экземпляр класса LoginManager
login_manager.init_app(application)

sections = [
    {'title': 'Профиль', 'url': '/profile', 'icon': 'icons/account_icon.svg'},
    {'title': 'Форум', 'url': '/forum', 'icon': 'icons/forum_icon.svg'},
    {'title': 'Друзья', 'url': '/friends', 'icon': 'icons/friends_icon.svg'},
    {'title': 'Подписки', 'url': '/subscriptions', 'icon': 'icons/subscriptions_icon.svg'},
    {'title': 'О нас', 'url': '/about', 'icon': 'icons/info_about_icon.svg'},
    {'title': 'Обратная связь', 'url': '/feedback', 'icon': 'icons/feedback_icon.svg'},
    {'title': 'Главная', 'url': '/', 'icon': 'icons/home.svg'},
    {'title': 'Добавить тему', 'url': '/forum/articles/add', 'icon': 'icons/plus.svg'},
    {'title': 'Регистрация', 'url': '/registration', 'icon': 'icons/register.svg'},
    {'title': 'Авторизация', 'url': '/login', 'icon': 'icons/login.svg'},
    {'title': 'Профиль пользователя', 'url': '/profile', 'icon': 'icons/user.svg'},
    {'title': 'Редактирование темы', 'url': '/forum/articles/edit', 'icon': 'icons/edit.svg'},
    {'title': 'Удалить тему', 'url': '/forum/articles/delete', 'icon': 'icons/delete.svg'},
]  # список секций сайта

sections_limiter = -7


@application.route('/')  # основная страница
def redirect_main():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    return render_template('main_page.html',
                           title='Главная',
                           users=users,
                           sections=sections[:sections_limiter])


@login_manager.user_loader  # функция загрузки пользователя
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@application.route('/about')  # страница о нас
def about():
    return render_template('about.html',
                           title='О нас',
                           sections=sections[:sections_limiter])


@application.route('/feedback',  methods=['GET', 'POST'])  # страница обратная связь
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


@application.route('/forum')  # основная страница форум
def forum_main():
    db_sess = db_session.create_session()
    query = request.args.get('q', '').strip()
    author = request.args.get('author')
    sort = request.args.get('sort', 'popular')
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
    elif sort == 'popular':
        vote_subquery = db_sess.query(
            ArticleVote.article_id,
            func.sum(ArticleVote.vote).label('score')
        ).group_by(ArticleVote.article_id).subquery()

        articles_query = articles_query.outerjoin(
            vote_subquery, Articles.id == vote_subquery.c.article_id
        ).order_by(func.coalesce(vote_subquery.c.score, 0).desc())
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


@application.route('/forum/articles/<int:id>', methods=['GET', 'POST'])  # страница с темой
def article(id):
    db_sess = db_session.create_session()
    article = db_sess.query(Articles).filter(Articles.id == id).first()
    if not article:
        abort(404)

    comments = db_sess.query(Comment).filter(
        Comment.article_id == article.id).order_by(Comment.created_date.desc()).all()
    all_users = db_sess.query(User).all()
    likes = sum(v.vote == 1 for v in article.votes)
    dislikes = sum(v.vote == -1 for v in article.votes)

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
                           users=all_users,
                           sections=sections[:sections_limiter],
                           likes=likes,
                           dislikes=dislikes)


@application.route('/article/<int:id>/like', methods=['POST'])  # лайк теме
@login_required
def like_article(id):
    db_sess = db_session.create_session()
    article = db_sess.query(Articles).get(id)
    if not article:
        abort(404)
    existing_vote = db_sess.query(ArticleVote).filter_by(user_id=current_user.id,
                                                         article_id=id).first()
    if existing_vote:
        if existing_vote.vote == 1:
            db_sess.delete(existing_vote)
        else:
            existing_vote.vote = 1
    else:
        db_sess.add(ArticleVote(user_id=current_user.id, article_id=id, vote=1))
    db_sess.commit()
    return redirect(f'/forum/articles/{id}')


@application.route('/article/<int:id>/dislike', methods=['POST'])  # дизлайк теме
@login_required
def dislike_article(id):
    db_sess = db_session.create_session()
    article = db_sess.query(Articles).get(id)
    if not article:
        abort(404)
    existing_vote = db_sess.query(ArticleVote).filter_by(user_id=current_user.id,
                                                         article_id=id).first()
    if existing_vote:
        if existing_vote.vote == -1:
            db_sess.delete(existing_vote)
        else:
            existing_vote.vote = -1
    else:
        db_sess.add(ArticleVote(user_id=current_user.id, article_id=id, vote=-1))
    db_sess.commit()
    return redirect(f'/forum/articles/{id}')


@application.route('/forum/articles/<int:article_id>/comment_delete/<int:comment_id>',
                   methods=['GET', 'POST'])  # удаление комментария
@login_required
def delete_comment(article_id, comment_id):
    db_sess = db_session.create_session()
    comment = db_sess.query(Comment).filter(Comment.id == comment_id,
                                            Comment.article_id == article_id).first()
    if comment and (comment.user == current_user or current_user.is_admin):
        db_sess.delete(comment)
        db_sess.commit()
    return redirect(f'/forum/articles/{article_id}')


@application.route('/forum/articles/add', methods=['GET', 'POST'])  # добавление темы
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


@application.route('/forum/articles/edit/<int:id>', methods=['GET', 'POST'])  # редактирование темы
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


@application.route('/forum/articles/delete/<int:id>', methods=['GET', 'POST'])  # удаление темы
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


@application.route('/profile')  # профиль пользователя
def self_profile():
    if current_user.is_authenticated:
        return redirect(f'/profile/{current_user.username}')
    return redirect('/login')


@application.route('/friends', defaults={'username': None})  # друзья пользователя
@application.route('/friends/<username>')
@login_required
def self_friends(username):
    db_sess = db_session.create_session()
    query = request.args.get('q', '').strip().lower()

    if not username:
        user = current_user
    elif username == current_user.username:
        return redirect('/friends')
    else:
        user = db_sess.query(User).filter(User.username == username).first()
        if not user:
            abort(404)

    friends = get_mutual_friends(user)
    if query:
        friends = [
            f for f in friends
            if query in (f.username or '').lower()
            or query in (f.name or '').lower()
            or query in (f.surname or '').lower()
        ]

    return render_template(
        'friends_list.html',
        title=f'Друзья {user.username} — {len(friends)} друзей',
        user=user,
        friends=friends,
        sections=sections[:sections_limiter]
    )


@application.route('/subscriptions', defaults={'username': None})  # подписки пользователя
@application.route('/subscriptions/<username>')
@login_required
def self_subscriptions(username):
    db_sess = db_session.create_session()
    query = request.args.get('q', '').strip().lower()

    if not username:
        user = current_user
    elif username == current_user.username:
        return redirect('/sbscriptions')
    else:
        user = db_sess.query(User).filter(User.username == username).first()
        if not user:
            abort(404)

    subscriptions = get_user_subscriptions(user)

    if query:
        subscriptions = [
            f for f in subscriptions
            if query in (f.username or '').lower()
            or query in (f.name or '').lower()
            or query in (f.surname or '').lower()
        ]

    return render_template(
        'subscriptions_list.html',
        title=f'Подписки {user.username} — {len(subscriptions)} подписок',
        user=user,
        subscriptions=subscriptions,
        sections=sections[:sections_limiter]
    )


@application.route('/profile/<username>', methods=['GET', 'POST'])  # профиль пользователя
def profile(username):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.username == username).first()
    if not user:
        abort(404)

    form = EditProfileForm(obj=user)
    friends = get_mutual_friends(user)
    edit_mode = request.args.get('edit') == '1'

    if form.validate_on_submit() and user.id == current_user.id:
        if form.submit.data:
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
                    old_path = os.path.join(application.static_folder,
                                            user.photo.replace('/', os.sep))

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
        else:
            return redirect(f'/profile/{username}')

    return render_template("profile.html",
                           user=user,
                           form=form,
                           edit_mode=edit_mode,
                           title=user.username,
                           sections=sections[:sections_limiter],
                           friends=friends)


@application.route('/subscribe/<int:user_id>', methods=['POST'])  # подписка на пользователя
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


@application.route('/unsubscribe/<int:user_id>', methods=['POST'])  # отписка от пользователя
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


@application.route('/logout')  # выход из аккаунта
@login_required
def logout():
    logout_user()
    return redirect("/")


@application.route('/change_account')  # смена аккаунта
@login_required
def change_profile():
    logout_user()
    return redirect('/login')


@application.route('/delete_account', methods=['POST'])  # удаление аккаунта
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


@application.route('/registration', methods=['GET', 'POST'])  # регистрация пользователя
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
        except Exception:
            return render_template('registration.html',
                                   title='Регистрация',
                                   form=form,
                                   message="Произошла ошибка при регистрации. Попробуйте еще раз.")
    return render_template('registration.html',
                           title='Регистрация',
                           form=form,
                           sections=sections[:sections_limiter])


@application.errorhandler(Exception)  # обработка ошибок
def handle_all_exceptions(e):
    return render_template('error.html',
                           title='Ошибка',
                           message=e,
                           sections=sections[:sections_limiter]), 500


@application.errorhandler(401)  # обработка ошибок доступа пользователя к странице
def unauthorized(e):
    return redirect('/login')


@application.errorhandler(404)
def page_not_found(e):
    return render_template('error.html',
                           title='Ошибка',
                           message='Страница не найдена',
                           sections=sections[:sections_limiter]), 404


@application.template_filter('time_ago')  # отображение времени назад
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


def get_mutual_friends(user: User) -> list[User]:  # получение друзей (подписчиков и подписок)
    following_ids = {u.id for u in user.subscriptions}
    follower_ids = {u.id for u in user.subscribers}
    mutual_ids = following_ids & follower_ids
    return [u for u in user.subscriptions if u.id in mutual_ids]


def get_user_subscriptions(user: User) -> list[User]:  # получение подписок
    following_ids = {u.id for u in user.subscriptions}
    return [u for u in user.subscriptions if u.id in following_ids]


def main():  # запуск приложения
    db_session.global_init("db/yforum.db")
    application.run(host='0.0.0.0')


if __name__ == '__main__':
    main()
