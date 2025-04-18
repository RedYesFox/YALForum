from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import Optional
from flask_wtf.file import FileField, FileAllowed


class EditProfileForm(FlaskForm):
    name = StringField('Имя', validators=[Optional()])
    surname = StringField('Фамилия', validators=[Optional()])
    age = IntegerField('Возраст', validators=[Optional()])
    position = StringField('Должность', validators=[Optional()])
    speciality = StringField('Специальность', validators=[Optional()])
    address = StringField('Адрес', validators=[Optional()])
    photo = FileField('Новое фото профиля', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Только изображения')
    ])
    submit = SubmitField('Сохранить')
