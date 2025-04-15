from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField, IntegerField, \
    StringField, RadioField
from wtforms.validators import DataRequired, Email


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Повторите пароль', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    age = IntegerField('Возраст', validators=[DataRequired()])
    position = RadioField('Должность', validators=[DataRequired()],
                          choices=[('student', 'Ученик'), ('teacher', 'Учитель')])
    speciality = StringField('Специализация', validators=[DataRequired()])
    address = StringField('Адрес', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')
