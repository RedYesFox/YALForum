from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField
from wtforms.validators import DataRequired


class ArticlesForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField("Содержание")
    category = StringField("Категория")
    # is_private = BooleanField("Личное")
    submit = SubmitField('Применить')
