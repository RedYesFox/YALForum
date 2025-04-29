from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired


class FeedbackForm(FlaskForm):
    content = TextAreaField("Сообщение", validators=[DataRequired()])
    submit = SubmitField("Оставить сообщение")
