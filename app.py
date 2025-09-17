
from flask import Flask, render_template, request, redirect, session, g
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DATABASE = 'shop.db'

# Home page
@app.route('/')
def index():
    db = get_db()
    cur = db.execute('SELECT * FROM products')
    products = cur.fetchall()
    return render_template('index.html', products=products)

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        db.execute(f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')")
        db.commit()
        return redirect('/login')
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cur = db.execute(f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'")
        user = cur.fetchone()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/')
        else:
            return 'Invalid credentials'
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Admin login and panel
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'admin_logged' not in session:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if username == 'admin' and password == 'pass12345':
                session['admin_logged'] = True
            else:
                return render_template('admin_login.html', error='Invalid admin credentials')
        else:
            return render_template('admin_login.html')
    db = get_db()
    users = db.execute('SELECT * FROM users').fetchall()
    products = db.execute('SELECT * FROM products').fetchall()
    return render_template('admin.html', users=users, products=products)

# Delete user
@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if 'admin_logged' not in session:
        return redirect('/admin')
    db = get_db()
    db.execute(f"DELETE FROM users WHERE id = {user_id}")
    db.commit()
    return redirect('/admin')

# Delete product
@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def admin_delete_product(product_id):
    if 'admin_logged' not in session:
        return redirect('/admin')
    db = get_db()
    db.execute(f"DELETE FROM products WHERE id = {product_id}")
    db.commit()
    return redirect('/admin')

# Add product
@app.route('/admin/add_product', methods=['POST'])
def admin_add_product():
    if 'admin_logged' not in session:
        return redirect('/admin')
    name = request.form['name']
    price = request.form['price']
    description = request.form['description']
    db = get_db()
    db.execute(f"INSERT INTO products (name, price, description) VALUES ('{name}', {price}, '{description}')")
    db.commit()
    return redirect('/admin')

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product(product_id):
    db = get_db()
    if request.method == 'POST':
        if 'user_id' in session:
            comment = request.form['comment']
            rating = request.form['rating']
            db.execute(f"INSERT INTO comments (user_id, product_id, comment) VALUES ({session['user_id']}, {product_id}, '{comment}')")
            db.execute(f"INSERT INTO ratings (user_id, product_id, rating) VALUES ({session['user_id']}, {product_id}, {rating})")
            db.commit()
        else:
            return redirect('/login')
    cur = db.execute(f"SELECT * FROM products WHERE id = {product_id}")
    product = cur.fetchone()
    cur = db.execute(f"SELECT c.comment, u.username FROM comments c JOIN users u ON c.user_id = u.id WHERE c.product_id = {product_id}")
    comments = cur.fetchall()
    cur = db.execute(f"SELECT AVG(rating) FROM ratings WHERE product_id = {product_id}")
    avg_rating = cur.fetchone()[0]
    return render_template('product.html', product=product, comments=comments, avg_rating=avg_rating)

@app.route('/cart')
def cart():
    if 'cart' not in session:
        session['cart'] = []
    db = get_db()
    cart_items = []
    total = 0
    for pid in session['cart']:
        cur = db.execute(f"SELECT * FROM products WHERE id = {pid}")
        product = cur.fetchone()
        if product:
            cart_items.append(product)
            total += product[2]
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []
    cart = session['cart']
    cart.append(product_id)
    session['cart'] = cart
    return redirect('/cart')


@app.route('/checkout')
def checkout():
    session['cart'] = []
    return render_template('checkout.html')

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        with sqlite3.connect(DATABASE) as db:
            db.executescript('''
            CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT);
            CREATE TABLE products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price INTEGER, description TEXT);
            CREATE TABLE comments (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product_id INTEGER, comment TEXT);
            CREATE TABLE ratings (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product_id INTEGER, rating INTEGER);
            INSERT INTO products (name, price, description) VALUES ('Widget', 10, 'A useful widget.');
            INSERT INTO products (name, price, description) VALUES ('Gadget', 20, 'A fancy gadget.');
            INSERT INTO products (name, price, description) VALUES ('Thingamajig', 15, 'A mysterious thingamajig.');
            INSERT INTO products (name, price, description) VALUES ('Doodad', 12, 'A handy doodad for your needs.');
            INSERT INTO products (name, price, description) VALUES ('Whatchamacallit', 18, 'Everyone needs a whatchamacallit.');
            INSERT INTO products (name, price, description) VALUES ('Doohickey', 25, 'A premium doohickey for pros.');
            INSERT INTO products (name, price, description) VALUES ('Contraption', 30, 'A complex contraption for fun.');
            INSERT INTO products (name, price, description) VALUES ('Gizmo', 22, 'A high-tech gizmo.');
            INSERT INTO products (name, price, description) VALUES ('Device', 17, 'A reliable device for daily use.');
            INSERT INTO products (name, price, description) VALUES ('Apparatus', 28, 'A sturdy apparatus for any task.');
            ''')
    app.run(debug=True)
