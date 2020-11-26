from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, TextAreaField, DateField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from os import getenv
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
app.config["SECRET_KEY"] = getenv("SECRET_KEY")

db = SQLAlchemy(app)

Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "kirjaudu"

@login_manager.user_loader
def load_user(user_id):
    return Kayttajat.query.get(int(user_id))

class Kayttajat(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nimi = db.Column(db.String(15), unique=True)
    sahkoposti = db.Column(db.String(50), unique=True)
    salasana = db.Column(db.String(80))
    isadmin = db.Column(db.Boolean)
    isbanned = db.Column(db.Boolean)

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

@app.errorhandler(404)
def olematon_sivu(e):
    flash("Sivua ei löydy.")
    if current_user.is_authenticated:
        return redirect(url_for("kirjauduttu"))
    return redirect(url_for("kirjaudu"))

@app.route("/")
def index():
    if current_user.is_authenticated:
        flash("Olet jo kirjautunut.")
        return redirect(url_for("kirjauduttu"))
    return render_template("index.html")

@app.route("/kirjaudu", methods=["GET", "POST"])
def kirjaudu():
    form = kirjaudu_f()
    if current_user.is_authenticated:
        flash("Olet jo kirjautunut.")
        return redirect(url_for("kirjauduttu"))
    if form.validate_on_submit():
        user = Kayttajat.query.filter_by(nimi=form.kayttaja_nimi.data).first()
        if user:
            sql = "SELECT isbanned FROM Kayttajat WHERE id =:kayttaja"
            porttikielto_haku = db.session.execute(sql, {"kayttaja":user.id})
            onko_porttikielto = porttikielto_haku.fetchone()
            if onko_porttikielto[0]:
                flash("Sinulla on porttikielto.")
                return render_template("kirjaudu.html", form=form)
            if check_password_hash(user.salasana, form.salasana.data):
                login_user(user)
                return redirect(url_for("kirjauduttu"))
        flash("Väärä käyttäjänimi tai salasana.")
        return render_template("kirjaudu.html", form=form)
    return render_template("kirjaudu.html", form=form)

@app.route("/rekisteroidy", methods=["GET", "POST"])
def rekisteroidy():
    form = rekisteroidy_f()
    if current_user.is_authenticated:
        flash("Olet jo kirjautunut.")
        return redirect(url_for("kirjauduttu"))
    if form.validate_on_submit():
        user = Kayttajat.query.filter_by(nimi=form.kayttaja_nimi.data).first()
        sahkoposti = Kayttajat.query.filter_by(sahkoposti=form.sahkoposti.data).first()
        if user:
            flash("Käyttäjä on jo olemassa.")
            return redirect(url_for("kirjaudu"))
        if sahkoposti:
            flash("Kyseinen sähköposti on jo käytössä.")
            return render_template("rekisteroidy.html", form=form)
        hash = generate_password_hash(form.salasana.data, method="sha256")
        uusi_kayttaja = Kayttajat(nimi=form.kayttaja_nimi.data, sahkoposti=form.sahkoposti.data, salasana=hash, isadmin=False, isbanned=False)
        db.session.add(uusi_kayttaja)
        db.session.commit()
        flash("Käyttäjä luotiin onnistuneesti.")
        return redirect(url_for("kirjaudu"))
    return render_template("rekisteroidy.html", form=form)

@app.route("/kirjauduttu")
@login_required
def kirjauduttu():
    return render_template("kirjauduttu.html", isadmin=current_user.isadmin)

@app.route("/kirjauduulos")
@login_required
def kirjaudu_ulos():
    logout_user()
    return redirect(url_for("index"))

@app.route("/kalenteri")
@login_required
def kalenteri():
    sql = "SELECT T.nimi, T.tekstiaika, T.id FROM Tapahtumat T ORDER BY oikeaaika"
    result = db.session.execute(sql)
    tapahtumat = result.fetchall()
    return render_template("kirjauduttu.html", tapahtumat=tapahtumat, isadmin=current_user.isadmin)

@app.route("/uusitapahtuma", methods=["GET", "POST"])
@login_required
def uusi_tapahtuma():
    form = uusi_tapahtuma_f()
    isadmin = current_user.isadmin
    if isadmin:
        if form.validate_on_submit():
            sql = "INSERT INTO Tapahtumat (nimi, kuvaus, tekstiaika, oikeaaika, omistaja_id) VALUES (:nimi, :kuvaus, :tekstiaika, :oikeaaika, :omistaja_id)"
            db.session.execute(sql, {"nimi":form.nimi.data, "kuvaus":form.kuvaus.data, "tekstiaika":form.aika.data, "oikeaaika":form.aika.data, "omistaja_id":current_user.id})
            db.session.commit()
            flash("Uusi tapahtuma luotiin onnistuneesti.")
            return redirect(url_for("kalenteri"))
        return render_template("kirjauduttu.html", form=form, uusitapahtuma=True, isadmin=isadmin)
    flash("Ei käyttöoikeutta!")
    return redirect(url_for("kirjauduttu"))

@app.route("/kayttajat", methods=["GET"])
@login_required
def kayttajat():
    isadmin = current_user.isadmin
    if isadmin is False:
        flash("Ei käyttöoikeutta!")
        return redirect(url_for("kirjauduttu"))
    sql = "SELECT nimi, id FROM Kayttajat GROUP BY id"
    haku = db.session.execute(sql)
    db.session.commit()
    nimet = haku.fetchall()
    return render_template("kirjauduttu.html", nimet=nimet, isadmin=isadmin)

@app.route("/ilmoittaudu", methods=["POST"])
@login_required
def ilmoittaudu():
    tapahtuma_id = request.form["tapahtumaid"]
    sql = "SELECT T.id FROM Tapahtumat T WHERE T.id =:tapahtumaid"
    haku = db.session.execute(sql, {"tapahtumaid":tapahtuma_id})
    tulos = haku.fetchall()
    if not tulos:
        flash("Tapahtumaa ei ole olemassa.")
        return redirect(url_for("kalenteri"))
    sql = "SELECT I.tapahtuma_id FROM Ilmoittautumiset I WHERE I.tapahtuma_id =:tapahtumaid AND I.kayttaja_id =:kayttaja"
    haku = db.session.execute(sql, {"tapahtumaid":tapahtuma_id, "kayttaja":current_user.id})
    tulos = haku.fetchall()
    if tulos:
        flash("Olet jo ilmoittautunut tapahtumaan.")
        return redirect(url_for("kalenteri"))
    sql = "INSERT INTO Ilmoittautumiset (tapahtuma_id, kayttaja_id) VALUES (:tapahtuma_id, :kayttaja_id)"
    db.session.execute(sql, {"tapahtuma_id":tapahtuma_id, "kayttaja_id":current_user.id})
    db.session.commit()
    flash("Ilmoittauduttu.")
    return redirect(url_for("kalenteri"))
    
@app.route("/toplista", methods=["GET"])
@login_required
def top_lista():
    sql = "SELECT K.nimi, COUNT(K.id), K.id FROM Kayttajat K, Ilmoittautumiset I WHERE K.id = I.kayttaja_id GROUP BY K.id ORDER BY COUNT(K.id) DESC"
    haku = db.session.execute(sql)
    tulokset = haku.fetchall()
    return render_template("kirjauduttu.html", tulokset=tulokset, isadmin=current_user.isadmin)

@app.route("/porttikielto", methods=["POST"])
@login_required
def porttikielto():
    isadmin = current_user.isadmin
    if isadmin is False:
        flash("Ei käyttöoikeutta!")
        return redirect(url_for("kirjauduttu"))
    kayttajaid = request.form["porttikieltoid"]
    if int(kayttajaid) == current_user.id:
        flash("Et voi antaa itselle porttikieltoa.")
        return redirect(url_for("kayttajat"))
    sql = "SELECT isbanned FROM Kayttajat WHERE id =:kayttaja"
    porttikielto_haku = db.session.execute(sql, {"kayttaja":kayttajaid})
    onko_porttikielto = porttikielto_haku.fetchone()
    if onko_porttikielto[0]:
        flash("Käyttäjällä on jo porttikielto.")
        return redirect(url_for("kayttajat"))
    sql = "UPDATE Kayttajat set isbanned=True WHERE id=:kayttaja_id"
    db.session.execute(sql, {"kayttaja_id":kayttajaid})
    db.session.commit()
    flash("Porttikielto annettu.")
    return redirect(url_for("kayttajat"))

@app.route("/omaprofiili", methods=["POST", "GET"])
@login_required
def oma_profiili():
    form = omat_tiedot_lomake_f()
    if form.validate_on_submit():
        sql = "SELECT kuvaus, lempiolut FROM Omattiedot WHERE kayttaja_id =:kayttaja"
        sqlhaku = db.session.execute(sql, {"kayttaja":current_user.id})
        omattiedot = sqlhaku.fetchall()
        if omattiedot:
            sql = "UPDATE Omattiedot set lempiolut=:olut, kuvaus=:kirjoitus WHERE kayttaja_id=:kayttaja"
            db.session.execute(sql, {"olut":form.olut.data, "kirjoitus":form.kuvaus.data,"kayttaja":current_user.id})
            db.session.commit()
            flash("Tiedot päivitetty.")
            return redirect(url_for("oma_profiili"))
        sql = "INSERT INTO Omattiedot (kayttaja_id, lempiolut, kuvaus) VALUES (:kayttaja, :olut, :kirjoitus)"
        db.session.execute(sql, {"kayttaja":current_user.id, "olut":form.olut.data, "kirjoitus":form.kuvaus.data})
        db.session.commit()
        flash("Tiedot asetettu.")
        return redirect(url_for("oma_profiili"))
    sql = "SELECT kuvaus, lempiolut FROM Omattiedot WHERE kayttaja_id =:kayttaja"
    sql_haku = db.session.execute(sql, {"kayttaja":current_user.id})
    omat_tiedot = sql_haku.fetchall()
    return render_template(("kirjauduttu.html"), form=form, isadmin=current_user.isadmin, omat_tiedot=omat_tiedot, lomake=True, nimi=current_user.nimi)

@app.route("/kayttajanprofiili", methods=["POST"])
@login_required
def kayttajan_profiili():
    kayttaja_id = request.form["kayttajaid"]
    sql = "SELECT K.nimi, O.lempiolut, O.kuvaus FROM Omattiedot O, Kayttajat K WHERE O.kayttaja_id=K.id AND K.id=:kayttajaid"
    haku = db.session.execute(sql, {"kayttajaid":kayttaja_id})
    kayttajan_haku = haku.fetchall()
    if not kayttajan_haku:
        flash("Käyttäjällä ei ole tietoja.")
        redirect(url_for("kirjauduttu"))
    sql = "SELECT T.nimi, T.tekstiaika FROM Tapahtumat T, Ilmoittautumiset I, Kayttajat K WHERE T.id=I.tapahtuma_id AND I.kayttaja_id=K.id AND K.id=:kayttajaid"
    haku = db.session.execute(sql, {"kayttajaid":kayttaja_id})
    ilmoittautumiset_kayttaja = haku.fetchall()
    sql = "SELECT COUNT(T.id) FROM Tapahtumat T, Kayttajat K WHERE T.omistaja_id = K.id AND K.id=:kayttajaid"
    haku = db.session.execute(sql, {"kayttajaid":kayttaja_id})
    jarjestetyt_tapahtumat = haku.fetchall()
    return render_template("kirjauduttu.html", isadmin=current_user.isadmin, kayttajan_haku=kayttajan_haku, ilmoittautumiset_kayttaja=ilmoittautumiset_kayttaja, jarjestetyt_tapahtumat=jarjestetyt_tapahtumat)

@app.route("/tapahtumantiedot", methods=["POST"])
@login_required
def tapahtuman_tiedot():
    tapahtuma_id = request.form["tapahtumaid"]
    sql = "SELECT T.nimi, T.kuvaus, T.tekstiaika, T.id, K.nimi FROM Tapahtumat T, Kayttajat K WHERE K.id = T.omistaja_id AND T.id =:tapahtuma_id ORDER BY oikeaaika"
    tapahtuma_haku = db.session.execute(sql, {"tapahtuma_id":tapahtuma_id})
    tapahtuma_tiedot = tapahtuma_haku.fetchone()
    if tapahtuma_tiedot is None:
        flash("Tapahtumaa ei ole olemassa.")
        return redirect(url_for("kirjauduttu"))
    sql = "SELECT K.nimi FROM Tapahtumat T, Kayttajat K, Ilmoittautumiset I WHERE T.id =:tapahtuma_id AND T.id = I.tapahtuma_id AND I.kayttaja_id = K.id"
    kayttaja_haku = db.session.execute(sql, {"tapahtuma_id":tapahtuma_id})
    ilmoittautuneet = kayttaja_haku.fetchall()
    return render_template("kirjauduttu.html", tapahtuma_tiedot=tapahtuma_tiedot, ilmoittautuneet=ilmoittautuneet, isadmin=current_user.isadmin)

@app.route("/keskustelu", methods=["POST", "GET"])
@login_required
def keskustelu():
    form = keskustelu_f()
    if form.validate_on_submit():
        sql = "INSERT INTO Keskustelu (kayttaja_id, kayttaja_nimi, viesti, klo) VALUES (:kayttaja, :nimi, :viesti, :aika)"
        klo = datetime.now()
        klo_aika = klo.strftime("%H:%M:%S")
        db.session.execute(sql, {"kayttaja":current_user.id, "nimi":current_user.nimi, "viesti":form.viesti.data, "aika":klo_aika})
        db.session.commit()
        return redirect(url_for("keskustelu"))
    sql = "SELECT kayttaja_nimi, viesti, klo FROM Keskustelu ORDER BY id DESC LIMIT 3"
    viesti_haku = db.session.execute(sql)
    viestit = viesti_haku.fetchall()
    return render_template("kirjauduttu.html", form=form, keskustelu=True, viestit=viestit, isadmin=current_user.isadmin)