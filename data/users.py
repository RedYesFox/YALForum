import datetime
import sqlalchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Логин
    email = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True, nullable=True)  # Почта
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Пароль хэшированный

    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Фамилия
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Имя
    age = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)  # Возраст
    position = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Должность
    speciality = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Специализация
    address = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Адрес
    about = sqlalchemy.Column(sqlalchemy.Text, nullable=True)  # О себе

    photo = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Фото
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)  # Дата создания аккаута

    # subscribers = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # новая колонка, которая вызывает ошибку

    def __repr__(self):
        return f'<User> with id:{self.id} - {self.surname} {self.name} {self.position}-{self.speciality}'

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
