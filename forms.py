from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange

class RegistrationForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=25)])
    name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=50)])
    age = IntegerField('Edad', validators=[DataRequired(), NumberRange(min=1, max=120)])
    email = StringField('Correo', validators=[DataRequired(), Email()])
    gender = SelectField('Género', choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')], validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')