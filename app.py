from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL
from datetime import datetime

app = Flask(__name__)

# ✅ MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  # your MySQL username
app.config['MYSQL_PASSWORD'] = 'Bhavan@2003'  # your MySQL password
app.config['MYSQL_DB'] = 'geo_db'

mysql = MySQL(app)

# ✅ Home route
@app.route('/')
def home():
    return render_template('index.html')


# ✅ Register new user
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        cursor.close()
        return jsonify({'status': 'error', 'message': 'Username already exists'})

    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'status': 'success'})


# ✅ Login user
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    cursor = mysql.connection.cursor()

    # Read user + role from DB
    cursor.execute("SELECT username, password, role FROM users WHERE username=%s AND password=%s",
                   (username, password))
    user = cursor.fetchone()

    if user:
        db_role = user[2]  # role from database

        cursor.execute("UPDATE users SET status='login', login_time=%s WHERE username=%s",
                       (datetime.now(), username))
        mysql.connection.commit()
        cursor.close()

        return jsonify({'status': 'success', 'role': db_role})
    cursor.close()
    return jsonify({'status': 'error'})



# ✅ Logout user
@app.route('/logout', methods=['POST'])
def logout():
    data = request.get_json()
    username = data['username']

    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE users SET status='logout', logout_time=%s WHERE username=%s", (datetime.now(), username))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'status': 'success'})



# ✅ Admin – View all users
@app.route('/admin/users', methods=['GET'])
def admin_users():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT username, role, status, login_time, logout_time FROM users")
    result = cursor.fetchall()
    cursor.close()

    # Convert tuples → JSON-friendly list
    users = []
    for row in result:
        users.append({
            'username': row[0],
            'role': row[1],
            'status': row[2],
            'login_time': str(row[3]) if row[3] else None,
            'logout_time': str(row[4]) if row[4] else None
        })

    return jsonify(users)


# ✅ Admin – Update user role
@app.route('/admin/update-role', methods=['POST'])
def update_role():
    data = request.get_json()
    username = data['username']
    role = data['role']

    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE users SET role=%s WHERE username=%s", (role, username))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'status': 'success'})


# ✅ Admin – Delete user
@app.route('/admin/delete', methods=['POST'])
def delete_user():
    data = request.get_json()
    username = data['username']

    # Prevent admin deletion
    if username == 'admin':
        return jsonify({'status': 'error', 'message': "Can't delete admin"})

    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM users WHERE username=%s", (username,))
    mysql.connection.commit()
    cursor.close()

    return jsonify({'status': 'success'})

# ✅ Admin - Change role
@app.route('/admin/change-role', methods=['POST'])
def change_role():
    data = request.get_json()
    username = data['username']
    role = data['role']

    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE users SET role=%s WHERE username=%s", (role, username))
    mysql.connection.commit()
    cursor.close()

    return jsonify({'status': 'success'})



# Fetch all products
@app.route('/products', methods=['GET'])
def get_products():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    cursor.close()

    products = []
    for row in rows:
        products.append({
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "image": row[3]
        })

    return jsonify(products)

@app.route('/cart/increase', methods=['POST'])
def increase_quantity():
    data = request.get_json()
    username = data['username']
    product_id = data['product_id']

    cursor = mysql.connection.cursor()
    cursor.execute("""
        UPDATE cart SET quantity = quantity + 1
        WHERE username=%s AND product_id=%s
    """, (username, product_id))

    mysql.connection.commit()
    cursor.close()

    return jsonify({'status': 'success'})

@app.route('/cart/decrease', methods=['POST'])
def decrease_quantity():
    data = request.get_json()
    username = data['username']
    product_id = data['product_id']

    cursor = mysql.connection.cursor()
    cursor.execute("""
        UPDATE cart SET quantity = quantity - 1
        WHERE username=%s AND product_id=%s AND quantity > 1
    """, (username, product_id))

    mysql.connection.commit()
    cursor.close()

    return jsonify({'status': 'success'})

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    username = data['username']
    product_id = data['product_id']

    cursor = mysql.connection.cursor()

    # Check if exists
    cursor.execute("SELECT quantity FROM cart WHERE username=%s AND product_id=%s",
                   (username, product_id))
    item = cursor.fetchone()

    if item:
        cursor.execute("""
            UPDATE cart SET quantity = quantity + 1
            WHERE username=%s AND product_id=%s
        """, (username, product_id))

    else:
        cursor.execute("""
            INSERT INTO cart (username, product_id, quantity)
            VALUES (%s, %s, 1)
        """, (username, product_id))

    mysql.connection.commit()
    cursor.close()

    return jsonify({'status': 'success'})

@app.route('/cart/<username>', methods=['GET'])
def get_cart(username):
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT c.id, p.name, p.price, p.image, c.quantity, p.id
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.username=%s
    """, (username,))
    rows = cursor.fetchall()
    cursor.close()

    cart = []
    for r in rows:
        cart.append({
            'cart_id': r[0],
            'name': r[1],
            'price': r[2],
            'image': r[3],
            'quantity': r[4],
            'product_id': r[5]
        })

    return jsonify(cart)

import re


@app.route('/order/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    username = data['username']

    cursor = mysql.connection.cursor()

    # Fetch product price directly as DECIMAL/FLOAT
    cursor.execute("""
        SELECT c.product_id, p.name, p.price, c.quantity
        FROM cart c 
        JOIN products p ON c.product_id = p.id
        WHERE c.username=%s
    """, (username,))
    items = cursor.fetchall()

    # Total calculation without regex
    total_amount = sum(float(item[2]) * item[3] for item in items)

    cursor.execute(
        "INSERT INTO orders (username, total_amount) VALUES (%s, %s)",
        (username, round(total_amount, 2))
    )
    order_id = cursor.lastrowid

    for item in items:
        cursor.execute("""
            INSERT INTO order_items (order_id, product_name, price, quantity)
            VALUES (%s, %s, %s, %s)
        """, (order_id, item[1], float(item[2]), item[3]))

    cursor.execute("DELETE FROM cart WHERE username=%s", (username,))
    mysql.connection.commit()
    cursor.close()

    return jsonify({'status': 'success'})


@app.route('/orders/<username>', methods=['GET'])
def get_orders(username):
    cursor = mysql.connection.cursor()

    # Check role
    cursor.execute("SELECT role FROM users WHERE username=%s", (username,))
    role = cursor.fetchone()

    if not role or role[0] != "admin":
        cursor.close()
        return jsonify({"error": "Only admin can view orders!"}), 403

    # Admin gets ALL orders
    cursor.execute("SELECT id, username, total_amount, date FROM orders")
    orders = cursor.fetchall()

    final = []

    for o in orders:
        cursor.execute(
            "SELECT product_name, price, quantity FROM order_items WHERE order_id=%s",
            (o[0],)
        )
        items = cursor.fetchall()

        final.append({
            'order_id': o[0],
            'username': o[1],
            'total_amount': o[2],
            'date': str(o[3]),
            'items': [{'name': i[0], 'price': i[1], 'qty': i[2], 'username': o[1] } for i in items]
        })

    cursor.close()
    return jsonify(final)


if __name__ == '__main__':
    app.run(debug=True)