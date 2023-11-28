from pprint import pprint
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests


TMDB_API_KEY = "---YOUR API KEY HERE-------"
URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_SEARCH_API_URL = 'https://api.themoviedb.org/3/movie/'
MOVIE_DB_IMAGE_URL = 'https://image.tmdb.org/t/p/w500'


headers = {
    "accept": "application/json",
    "Authorization": "-----YOUR AUTHORIZATION KEY HERE-----"
}


app = Flask(__name__)
app.config['SECRET_KEY'] = '----YOUR SECRET KEY HERE-----'
Bootstrap5(app)
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies_database.db"
db.init_app(app)


class MyForms(FlaskForm):
    rating = StringField(label="Your Rating out of 10", validators=[DataRequired()])
    review = StringField(label="Your Review", validators=[DataRequired()])
    Submit = SubmitField(label="Edit")


class AddMovie(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    Submit = SubmitField("Add Movie")


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    all_movies = db.session.execute(db.select(Movie)).scalars().all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route('/edit', methods=["GET", "POST"])
def edit():
    form = MyForms()
    movie_id = request.args.get("id")
    edit_movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        edit_movie.rating = float(form.rating.data)
        edit_movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=edit_movie, form=form)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = AddMovie()

    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(url=URL, params={'api_key': TMDB_API_KEY, "query": movie_title})
        data = response.json()['results']
        return render_template('select.html', options=data)
    return render_template('add.html', form=form)


@app.route('/adding')
def adding():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_SEARCH_API_URL}/{movie_api_id}"
        response = requests.get(url=movie_api_url, params={'api_key': TMDB_API_KEY}).json()
        pprint(response)
        new_movie = Movie(
            title=response['original_title'],
            year=response['release_date'].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{response['poster_path']}",
            description=response["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
