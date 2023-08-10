from datetime import date

import werkzeug.security
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, \
    logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from forms import admin_only
from flask_gravatar import Gravatar
import html

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy()
db.init_app(app)

gravatar = Gravatar(app,
                    size=30,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


login_manager=LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)




# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author=relationship('User', back_populates='posts')
    comment=relationship('Comment', back_populates='post')

class Comment(db.Model):
    __tablename__='comments'
    id=db.Column(db.Integer, primary_key=True)
    text=db.Column(db.String(250), nullable=False)
    author_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author=relationship('User', back_populates='comment')
    post_id=db.Column(db.Integer, db.ForeignKey('blog_posts.id'),
                      nullable=False)
    post=relationship('BlogPost', back_populates='comment')

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(250), unique=True, nullable=False)
    email=db.Column(db.String(250), unique=True, nullable=False)
    password=db.Column(db.String(20), nullable=False)
    posts=relationship('BlogPost', back_populates='author')
    comment=relationship('Comment', back_populates='author')


with app.app_context():
    db.create_all()


@app.route('/register', methods=["GET", "POST"])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        if db.session.execute(db.Select(User).where(
                User.email==form.email.data)).scalar():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        new_user=User(
            username=form.username.data,
            email=form.email.data,
            password=werkzeug.security.generate_password_hash(
                password=form.password.data, salt_length=8)

        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return render_template('index.html')
    return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user=db.session.execute(db.Select(User).where(
                User.email==form.email.data)).scalar()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                flash('The password is incorrect')
        else:
            flash("A user with such email doesn't exist")

    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)


@login_required
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment=CommentForm()
    if comment.validate_on_submit():
        new_comment=Comment(
            text=comment.text.data.replace('<p>', '').replace('</p>', ''),
            author=current_user,
            post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    all_comments=db.session.execute(db.Select(Comment).where(
        Comment.post_id==post_id)).scalars()
    return render_template("post.html", post=requested_post,
                           commentsform=comment, comments=all_comments)

@login_required
@admin_only
@app.route("/new-post", methods=["GET", "POST"])
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")        )
        print(current_user)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)

@login_required
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


@app.route("/delete/<int:post_id>")
@admin_only
@login_required
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

@login_required
@app.route("/profile")
def profile():
    return render_template('profile.html')




@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
