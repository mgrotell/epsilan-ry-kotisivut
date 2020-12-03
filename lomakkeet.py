from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, TextAreaField, DateField
from wtforms.validators import InputRequired, Email, Length

class kirjaudu_f(FlaskForm):
    kayttaja_nimi = StringField("Käyttäjänimi", validators=[InputRequired(), Length(min=3, max=20)])
    salasana = PasswordField("Salasana", validators=[InputRequired(), Length(min=8, max=50)])

class rekisteroidy_f(FlaskForm):
    kayttaja_nimi = StringField("Käyttäjänimi", validators=[InputRequired(), Length(min=3, max=20)])
    sahkoposti = StringField("Sähkoposti", validators=[InputRequired(), Email(message="Virheellinen sähköposti.", granular_message=False, check_deliverability=True, allow_smtputf8=True, allow_empty_local=False), Length(max=50)])
    salasana = PasswordField("Salasana", validators=[InputRequired(), Length(min=8, max=50)])

class uusi_tapahtuma_f(FlaskForm):
    nimi = StringField("Tapahtuman nimi", validators=[InputRequired(), Length(min=4, max=100)])
    kuvaus = TextAreaField("Tapahtuman kuvaus", validators=[InputRequired(), Length(min=10, max=1000)])
    aika = DateField("Päivä muotoa   (2000-12-24)", validators=[InputRequired()])

class omat_tiedot_lomake_f(FlaskForm):
    kuvaus = StringField("Kuvaus", validators=[InputRequired(), Length(min=5, max=400)])
    olut = StringField("Lempi olut", validators=[InputRequired(), Length(min=3, max=40)])

class keskustelu_f(FlaskForm):
    viesti = StringField("Viesti", validators=[InputRequired(), Length(min=2, max=150)])