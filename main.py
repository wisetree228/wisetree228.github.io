from flask import Flask, render_template, url_for, request, flash, get_flashed_messages, redirect, session, send_file
from sqlite3 import *
import base64



app=Flask(__name__)

app.secret_key='key123456789'

urls=[
    {"name":"Добавить запись", "url":"/add"},
    {"name":"динамический просмотр", "url":"/view/<int:id>"}
]

data={
    'userLogged':False,
    'userName':'',
}


def selectAllWithCondition(table, cond):
    db = connect('database.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM {table} WHERE {cond};")
    db.commit()
    list = cur.fetchall()
    db.close()
    return list


def selectOne(table, cond):
    db = connect('database.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM {table} WHERE {cond};")
    db.commit()
    list = cur.fetchone()
    db.close()
    return list

def selectAll(table):
    db = connect('database.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM {table};")
    db.commit()
    list = cur.fetchall()
    db.close()
    return list

def drop(table, cond):
    db = connect('database.db')
    cur = db.cursor()
    cur.execute(f"DELETE FROM {table} WHERE {cond};")
    db.commit()
    db.close()

def check_id(table, cond):
    db = connect('database.db')
    cur = db.cursor()
    cur.execute(f"SELECT * FROM {table} WHERE {cond};")
    db.commit()
    list = cur.fetchall()
    db.close()
    if len(list)>=1:
        return True
    return False



@app.route('/login',  methods=['POST', 'GET'])
def login():
    if request.method=='POST':
        if len(request.form['username'])>3 and len(request.form['password'])>5:
            username=request.form['username']
            passw=request.form['password']
            users=selectAll('user')
            name_in_db=False
            for user in users:
                if username in user and passw in user:
                    data['userLogged']=True
                    data['userName']=username
                    name_in_db=True
                    return redirect('/')

                elif username in user and not(passw in user):
                    flash('Неверный пароль, повторите попытку')
                    name_in_db = True
                    break
            if not name_in_db:
                flash('Учётной записи с таким именем нет, проведите регистрацию')
        else:
            flash('юзернейм должен быть длиннее 3 символов, а пароль - длиннее 5!')


    return render_template('log.html')


@app.route("/register", methods=['POST', 'GET'])
def register():

    if request.method=='POST':
        if (len(request.form['username'])>3 and len(request.form['password'])>5) and not("'" in request.form['username'] or "'" in request.form['password']):
            username=request.form['username']
            passw=request.form['password']
            users=selectAll('user')
            name_in_db=False
            for user in users:
                if username in user:
                    flash('Аккаунт с таким именем уже существует! Попробуйте другое')
                    name_in_db=True



            if not name_in_db:
                db = connect('database.db')
                cur = db.cursor()
                cur.execute("INSERT INTO user (username, password) VALUES (?, ?);", (username, passw))
                db.commit()
                db.close()
                data['userLogged'] = True
                data['userName'] = username
                return redirect('/')


        else:
            flash('юзернейм должен быть длиннее 3 символов, а пароль - длиннее 5, также запрещено использовать одинарную кавычку в данных с целью защиты от sql иньекций')

    return render_template('register.html')





@app.route("/")
def index():
    db = connect('database.db')
    cur = db.cursor()
    cur.execute("SELECT * FROM article")
    db.commit()
    articles = cur.fetchall()
    db.close()


    return render_template('index.html', title="news", urls=urls, articles=articles, data=data)

@app.route("/add", methods=['POST', 'GET'])
def add():
    if not data['userLogged']:
        return redirect('/')

    if request.method=='POST':

        if len(request.form['header']) > 3 and len(request.form['text'])>10:


            db = connect('database.db')
            cur = db.cursor()
            cur.execute(f"INSERT INTO article (name, text, author) VALUES (?, ?, ?);", (request.form['header'], request.form['text'], data['userName']))
            db.commit()
            db.close()

            flash(f"все ок, статья {request.form['header']} добавлена")
        else:
            flash('ошибка, некорректные данные')


    return render_template('add.html', data=data)


@app.route("/view/<int:id>")
def detailview(id):
    if not check_id('article', f"id={id}"):
        return redirect('error')


    article=selectOne('article', f"id={id}")

    return render_template('detailview.html', article=article, data=data)

@app.route("/delete/<int:id>")
def delete(id):
    if not check_id('article', f"id={id}"):
        return redirect('error')
    auth = selectOne('article', f"id={id}")[3]
    if not data['userLogged']:
        return redirect('/')
    elif data['userName']!=auth:
        return redirect('/')
    else:

        # db = connect('database.db')
        # cur = db.cursor()
        # cur.execute(f"DELETE FROM article WHERE id={id};")
        # db.commit()
        # db.close()
        drop('article', f"id={id}")
        return redirect("/")

@app.route("/update/<int:id>", methods=['POST', 'GET'])
def update(id):
    if not check_id('article', f"id={id}"):
        return redirect('error')
    auth=selectOne('article', f"id={id}")[3]
    if not data['userLogged']:
        return redirect('/')
    elif data['userName']!=auth:
        return redirect('/')
    else:

        article=selectOne('article', f"author='{data['userName']}'")

        db = connect('database.db')
        cur = db.cursor()
        cur.execute(f"SELECT * FROM article WHERE id={id};")
        db.commit()
        article = cur.fetchone()
        db.close()
        if request.method == 'POST':

            if len(request.form['header']) > 3 and len(request.form['text']) > 10:

                db = connect('database.db')
                cur = db.cursor()
                cur.execute(f"UPDATE article SET name='{request.form['header']}', text='{request.form['text']}' WHERE id={id};")
                db.commit()
                db.close()

                flash(f"все ок, статья '{request.form['header']}' обновлена")
            else:
                flash('ошибка, некорректные данные')

    return render_template('update.html', article=article, data=data)



@app.route('/logout')
def logout():
    data['userLogged']=False
    data['userName']=''
    return redirect('/')




@app.errorhandler(404)
def pagenotfound(error):
    return render_template('error.html')


def check_user_image(username):
    conn = connect('database.db')
    cursor = conn.cursor()

    # Выполнение запроса с условием WHERE и COUNT
    cursor.execute(f"SELECT * FROM user WHERE username = '{username}' AND image IS NOT NULL")
    result = cursor.fetchall()

    conn.close()

    if len(result)==0:
        return False
    else:
        return True




@app.route('/profile', methods=['POST', 'GET'])
def profile():
    if not data['userLogged']:
        return redirect(url_for('login'))
    articles=selectAllWithCondition('article', f"author='{data['userName']}'")
    leng=len(articles)
    if request.method=='POST':
        db = connect('database.db')
        cur = db.cursor()

        # Получить файл из запроса
        image_file = request.files['image']

        # Если файл был передан
        if image_file:
            # Преобразование содержимого файла в BLOB
            image_data = image_file.read()

            # Сохранить изображение в базе данных
            cur.execute("UPDATE user SET image = ? WHERE username = ?", (image_data, data['userName']))
            db.commit()

        db.close()


    if check_user_image(data['userName']):
        user = selectOne('user', f"username='{data['userName']}'")
        db = connect('database.db')
        cur = db.cursor()
        cur.execute("SELECT image FROM user WHERE username = ?", (data['userName'],))
        image_data = cur.fetchone()[0]
        db.close()

        # Декодирование и преобразование данных изображения в base64
        img_data_base64 = base64.b64encode(image_data).decode('utf-8')
        return render_template('profile.html', data=data, articles=articles, leng=leng, img=img_data_base64)
    else:
        return render_template('profile.html', data=data, articles=articles, leng=leng, img=None)







users=selectAll('user')


for i in users:
    print(i[0], i[1], i[2])

# print(check_id('article', 'id=3'))
# print(check_id('article', 'id=12'))


# with app.test_request_context():
#     print(url_for("page", user="i"))




if __name__=="__main__":
    app.run(debug=True)
