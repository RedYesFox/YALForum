import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy.orm import relationship


class ArticleVote(SqlAlchemyBase):
    __tablename__ = 'article_votes'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'),
                                nullable=False)
    article_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('articles.id'),
                                   nullable=False)
    vote = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

    article = relationship("Articles", back_populates="votes")
    user = relationship("User")
    article = relationship("Articles")
