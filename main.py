from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

#Update with unique movie database key and app secret key
MOVIE_DB_KEY = os.environ.get("MOVIE_DB_KEY")
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL",  "sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)
db = SQLAlchemy(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, unique=False, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)
#Uncomment when creating database for the first time
# db.create_all()

#Quick flaskform for the movie rating
class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")


class AddMovie(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Done")

@app.route("/")
def home():
    #Create list ordered by rank from the Movie class
    all_movies = Movie.query.order_by(Movie.rating).all()
    #This line loops through all the movies
    for i in range(len(all_movies)):
        #This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)

#Add new movie to DB
@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(url=f"https://api.themoviedb.org/3/search/movie?api_key={MOVIE_DB_KEY}&language=en-US&query={movie_title}")
        response.raise_for_status()
        data = response.json()
        movie_list = data["results"]
        return render_template('select.html', movies=movie_list)
    return render_template("add.html", form=form)


@app.route("/find", methods=["GET", "POST"])
def all_data():
    tmdb_id = request.args.get("id")
    if tmdb_id:
        full_response = requests.get(url=f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={MOVIE_DB_KEY}&language=en-US")
        full_response.raise_for_status()
        full_data = full_response.json()
        new_movie = Movie(
            title=full_data['title'],
            year=full_data['release_date'].split("-")[0],
            description=full_data['overview'],
            img_url=f"https://image.tmdb.org/t/p/w500{full_data['poster_path']}"
        )

        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', id=new_movie.id))


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete", methods=["GET", "POST"])
def delete():
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()

    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)
