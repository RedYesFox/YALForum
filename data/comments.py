import sqlalchemy
import datetime
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Comment(SqlAlchemyBase):
    __tablename__ = 'comments'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    content = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    article_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('articles.id'))

    user = orm.relationship('User')
    article = orm.relationship('Articles')
