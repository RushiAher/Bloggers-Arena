from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import datetime
from werkzeug.utils import secure_filename
from flask_mail import Mail
import os
import json
import math

with open("config.json","r") as js:
    params = json.load(js)["params"]
app = Flask(__name__)

app.secret_key = 'super-secret key'
local_server = True


if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['production_uri']
    
db = SQLAlchemy(app)

app.config['upload_path'] = params['upload_location']
class Register(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(25),  nullable=False)
    password = db.Column(db.String(20),  nullable=False)
    date = db.Column(db.String(12),  nullable=True)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(50),  nullable=False)
    title = db.Column(db.String(100),  nullable=False)
    tagline = db.Column(db.String(100),  nullable=False)
    content = db.Column(db.String(1000),  nullable=False)
    img_file = db.Column(db.String(20),  nullable=False) 
    author = db.Column(db.String(20),  nullable=False) 
    date = db.Column(db.String(12),  nullable=True)

class Contacts(db.Model):
    sr_no= db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30),  nullable=False)
    email = db.Column(db.String(12),  nullable=False)
    phone_num = db.Column(db.String(12),  nullable=False)
    msg = db.Column(db.String(120),  nullable=False)
    date = db.Column(db.String(), nullable=True)

class Comments(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30),  nullable=False)
    email = db.Column(db.String(12),  nullable=False)
    message = db.Column(db.String(120),  nullable=False)
    postsno = db.Column(db.String(100),  nullable=False)
    date = db.Column(db.String(), nullable=True)


app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD= params['gmail-password']
)
mail = Mail(app)

loggedin = "false"


@app.route('/')
def home():
    global loggedin
    loggedin = "false"
    posts = Posts.query.filter_by().all()
    posts = posts[::-1]
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    if page==1:
        prev = "#"
        next = "/?page=" + str(page+1)
    elif page==last:
        prev = "/?page=" + str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    return render_template("home.html", params=params,posts=posts,prev=prev, next=next, loggedin=loggedin)


@app.route('/writeblog')
def writeblog():
    global loggedin
    loggedin = "true"
    return render_template("writeblog.html", params=params, loggedin=loggedin)


@app.route('/blogs')
def blogs():
    posts = Posts.query.all()
    return render_template("blogs.html", params=params, posts=posts, loggedin=loggedin)


@app.route('/getblog/<string:sno>' )
def getblogs(sno):
    posts = Posts.query.all()
    post = Posts.query.filter_by(sno=sno).first()
    comm = Comments.query.filter_by(postsno=sno).all()
    return render_template("getblog.html", params=params, comm=comm, posts=posts, post=post, loggedin=loggedin)
    

@app.route('/about')
def about():
    return render_template("about.html", params=params, loggedin=loggedin)
    

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        name = request.form.get('myname')
        email = request.form.get('myemail')
        phone = request.form.get('myphone_num')
        msg = request.form.get('mymsg')
        entry =Contacts(name=name, email=email, phone_num = phone, date = datetime.datetime.now(), msg = msg)
        db.session.add(entry)
        db.session.commit()
        mail.send_message("New Messege From " + name,
                          sender=email,
                          recipients=[params['gmail-user']],
                          body=msg + "\n" + "contact no: " + phone)
        flash("Message send successfully!")
    return render_template("contact.html", params=params, loggedin=loggedin)


@app.route('/post', methods=['GET','POST'])
def post():
    if 'user' in session:
        if request.method == 'POST':
            title = request.form.get("title")
            tline = request.form.get("tagline")
            content = request.form.get("content")
            author = request.form.get("author")
            
            f = request.files["file1"]
            f.save(os.path.join(app.config['upload_path'], secure_filename(f.filename)))
            post = Posts(user=session['user'],title=title, tagline=tline, content=content,author=author, img_file=f.filename, date=datetime.datetime.now())
            db.session.add(post)
            db.session.commit()
            flash("Your blog post has been posted successfully!")
        return redirect("/writeblog")
    return redirect("/")


@app.route('/myblog')
def myblog():
    global loggedin
    loggedin = "true"
    if 'user' in session:
        post = Posts.query.filter_by(user=session['user']).all()
        print(post)
    return render_template("myblog.html", params=params, posts=post, loggedin=loggedin)



@app.route('/edit/<string:sno>',methods = ["GET", "POST"])
def edit(sno):
    global loggedin
    if ('user' in session):
        loggedin = "true"
        if (request.method=="POST"):
            title = request.form.get("title")
            tline = request.form.get("tagline")
            content = request.form.get("content")
            author = request.form.get("author")
            img_file = request.form.get("file1")
            post = Posts.query.filter_by(sno=sno).first()
            post.title = title
            post.tagline = tline
            post.content = content
            post.author = author
            post.date = datetime.datetime.now()
            f = request.files["file1"]
            if secure_filename(f.filename) != "":
                f.save(os.path.join(app.config['upload_path'], secure_filename(f.filename)))
                post.img_file = f.filename
            
            db.session.commit()
            flash("Post edited successfully!")
            print("y")
            return redirect("/myblog")
        post = Posts.query.filter_by(sno=sno).first()
        return render_template("edit.html", params=params, post=post, loggedin=loggedin)
    else:
        loggedin="false"
        return redirect("/")


@app.route('/delete/<string:sno>',methods = ["GET", "POST"])
def Del(sno):
    if ('user' in session):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        flash("Post deleted successfully!")
        return redirect("/myblog")


@app.route('/comment/<string:sno>', methods=['GET','POST'])
def comment(sno):
    if request.method == 'POST':
        name = request.form.get("uname")
        email = request.form.get("email")
        msg = request.form.get("message")
        comm = Comments(name=name, email=email, message=msg, postsno=sno, date=datetime.datetime.now())
        db.session.add(comm)
        db.session.commit()
    return redirect("/getblog/" + sno)


@app.route('/login', methods=['GET', 'POST'])
def login():
    global loggedin
    if request.method == "POST":
        Lemail = request.form.get("Luname")
        Lpass = request.form.get("Lpass")
        user = Register.query.filter_by(email=Lemail).first()
        if user == None:
            pass
        elif user.email == Lemail and user.password == Lpass:
            session['user'] = Lemail
            loggedin = "true"
            flash("Logging successfully!")
            return redirect("/writeblog")
        flash("Incorrect username or password!")
    return render_template("home.html", params=params, loggedin=loggedin)


@app.route('/signup', methods=['GET', 'POST'])
def signup():   
    if request.method == "POST":
        email = request.form.get("Remail")
        psw = request.form.get("Rpass")
        repsw = request.form.get("Rpsw-repeat")
        users = Register.query.filter_by(email=email).first()
        print(users)
        if users == None:
            if psw == repsw:
                user = Register(email=email, password=psw, date=datetime.datetime.now())
                db.session.add(user)
                db.session.commit()
                flash("SignUp Successfully! Now click on  login button to continue.")
            else:
                flash("Password does not match! try again.")

        elif (users.email == email) and psw != repsw:
            flash("Email id already exist and password not match!")
        elif psw != repsw:
            flash("Password does not match! try again.")
        elif users.email == email:
            flash("Email id already exist! try another email.")
       
            
    return redirect("/")

@app.route('/logout')
def Logout():
    session.pop('user')
    return redirect("/")
app.run(debug=True)





