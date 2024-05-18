from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
from werkzeug.security import gen_salt

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['DATABASE'] = 'pizza.db'
app.config.update(
    SESSION_COOKIE_SECURE=True,  # Ensures cookies are sent over HTTPS
    SESSION_COOKIE_HTTPONLY=True,  # Prevents JavaScript access to cookies
    SESSION_COOKIE_SAMESITE='Lax'  # Mitigates CSRF attacks
)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'], timeout=30)  # Increased timeout

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate(username, password):
    hashed_password = hash_password(password)
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user is not None

@app.before_request
def before_request():
    if request.scheme == 'http' and request.url.startswith('https://'):
        return redirect(request.url.replace("http://", "https://"))

@app.route('/recover_password', methods=['GET', 'POST'])
def recover_password():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user:
                flash('Password recovery instructions have been sent to your email.')
            else:
                flash('Username not found')
        else:
            flash('Please provide a username')
    return render_template('recover_password.html')

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('menu'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if validate(username, password):
            session.pop('_flashes', None)  # Clear flashes before login
            session.clear()  # Clear the session to mitigate fixation attacks
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('menu'))
        flash('Invalid Credentials')
    return render_template('login.html')


@app.route('/menu')
def menu():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pizzas")
    menu_items = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('menu.html', menu_items=menu_items)

@app.route('/add_to_cart/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pizzas WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    if item:
        cursor.execute("INSERT INTO cart (username, item_id) VALUES (?, ?)", (session['username'], item_id))
        conn.commit()
        
    cursor.close()
    conn.close()
    return redirect(url_for('menu'))

@app.route('/cart')
def cart():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT pizzas.name, pizzas.price FROM cart INNER JOIN pizzas ON cart.item_id = pizzas.id WHERE cart.username = ?", (session['username'],))
    cart_items = cursor.fetchall()
    total_price = sum(item[1] for item in cart_items)
    cursor.close()
    conn.close()
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/place_order', methods=['POST'])
def place_order():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT pizzas.name, pizzas.price FROM cart INNER JOIN pizzas ON cart.item_id = pizzas.id WHERE cart.username = ?", (session['username'],))
    cart_items = cursor.fetchall()
    total_price = sum(item[1] for item in cart_items)
    if total_price == 0:
        flash('Your cart is empty. Please add items before placing an order.')
        cursor.close()
        conn.close()
        return redirect(url_for('menu'))
    cursor.execute("INSERT INTO orders (username, item_id) SELECT username, item_id FROM cart WHERE username = ?", (session['username'],))
    cursor.execute("DELETE FROM cart WHERE username = ?", (session['username'],))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Your order has been placed successfully.')
    return redirect(url_for('order_success'))

@app.route('/order_success')
def order_success():
    return render_template('order_success.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            hashed_password = hash_password(password)
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Registration successful. Please log in.')
            return redirect(url_for('login'))
        else:
            flash('Username and password are required')
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
