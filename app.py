from flask import Flask, flash, render_template, request, redirect, url_for,session
from celery import Celery
from flask_mail import Mail,Message
from flask_mysqldb import MySQL



app = Flask(__name__)
app.config['SECRET_KEY'] = '1234567890-=qwertyuiooppsdfghjklzxcvbnm'

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = '',
    MAIL_PASSWORD=  '',
    MAIL_DEFAULT_SENDER= ''
)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = ''
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MYSQL_DB'] = 'reminder'
mail = Mail(app)
client = Celery(app.name,broker= 'redis://127.0.0.1:6379/0',)
client.conf.timezone = 'Asia/Calcutta'
mysql = MySQL(app)

@client.task
def send_mail(data):
    with app.app_context():
        msg = Message("Ping!",
                    recipients=[data['email']])
        msg.body = data['message']
        mail.send(msg)

@app.route('/',methods=['GET','POST'])
def index():
    return render_template('login.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        check = cur.execute('SELECT * from `user` WHERE email=%s',[email])
        if check:
            return 'Account Found'
        else:
            cur.execute('INSERT into `user` (`email`,`password`) VALUES (%s,%s)',(email,password))
            mysql.connection.commit()
            return 'done'
    return 'Try Again'
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute('SELECT `u_id` FROM `user` WHERE `email`=%s and `password`=%s',(email,password))
        x = cur.fetchall()
        if x:
            cur.execute('SELECT `task` FROM `task` WHERE `email`=%s',['akhani.bharga@gmail.com'])
            info = cur.fetchall()
            l = []
            for i in info:
                l.append(i['task'])
            return render_template('main.html',l=l)
        else:
            return '<h1>Incorrect Password</h1>'
        return '<h1>Enter Valid Details</h1>'

@app.route('/main', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        return render_template('main.html')

    elif request.method == 'POST':
        data = {}
        data['email'] = request.form['email']
        data['first_name'] = request.form['first_name']
        data['last_name'] = request.form['last_name']
        data['message'] = request.form['message']
        duration = int(request.form['duration'])
        duration_unit = request.form['duration_unit']

        if duration_unit == 'minutes':
            duration *= 60
        elif duration_unit == 'hours':
            duration *= 3600
        elif duration_unit == 'days':
            duration *= 86400
        print(duration)
        send_mail.apply_async(args=[data], countdown = duration)
        flash(f"Email will be sent to {data['email']} in {request.form['duration']} {duration_unit}")
        return redirect(url_for('main'))


if __name__=='__main__':
    app.run(debug=True)