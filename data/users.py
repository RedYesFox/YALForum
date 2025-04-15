import datetime
import sqlalchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Фамилия
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Имя
    age = sqlalchemy.Column(sqlalchemy.Integer)  # Возраст
    position = sqlalchemy.Column(sqlalchemy.String, nullable=False)  # Должность
    speciality = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Специализация
    address = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Адрес
    email = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True, nullable=True)  # Почта
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Пароль хэшированный
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)  # Дата создания аккаута

    def __repr__(self):
        return f'<User> with id:{self.id} - {self.surname} {self.name} {self.position}-{self.speciality}'

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
