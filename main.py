from flask import *
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super-secret-key"

def db_conn():
    conn = sqlite3.connect('test.db')
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

SHOP_NAME = "E-Shop"

@app.context_processor
def inject_shop_name():
    return dict(shop_name=SHOP_NAME)

def create_table():
    conn = db_conn()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS login(
        email TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        name TEXT NOT NULL,
        phone INTEGER,
        address TEXT,
        pincode INTEGER,
        FOREIGN KEY (email) REFERENCES login(email)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products(
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        stock INTEGER,
        description TEXT,
        image TEXT,
        purchasing_price REAL DEFAULT 0
    )
    """)
    # try:
    #     cursor.execute("ALTER TABLE products ADD COLUMN purchasing_price REAL DEFAULT 0")
    # except:
    #     pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cart(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        product_id INTEGER,
        quantity INTEGER DEFAULT 1,
        FOREIGN KEY(email) REFERENCES login(email),
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        product_id INTEGER,
        quantity INTEGER,
        status TEXT,
        order_date TEXT,
        total REAL,
        margin REAL DEFAULT 0,
        FOREIGN KEY(email) REFERENCES login(email),
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin(
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_name TEXT,
        password TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bill (
        bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        bill_date TEXT,
        grand_total REAL,
        payment_method TEXT DEFAULT 'COD'
    )
    """)
    try:
        cursor.execute("ALTER TABLE bill ADD COLUMN payment_method TEXT DEFAULT 'COD'")
    except:
        pass


    conn.commit()
    conn.close()


create_table()

# Default HomePage
@app.route('/',methods=['GET','POST'])
def homepage():
    if 'email' in session :
        session.clear()
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    data = cursor.fetchall()
    conn.close()
    return render_template("homepage.html", products=data)

# Logged-In HomePage
@app.route('/home')
def logged_in_home():
    if 'email' not in session:
        return redirect('/login')
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    data = cursor.fetchall()
    conn.close()
    return render_template("homepage.html", products=data)

# User SignUp Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['user_name']
        password = request.form['password']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        pincode = request.form['pincode']

        conn = db_conn()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO login(email,password) VALUES (?,?)", (email, password))
        cursor.execute("INSERT INTO users(email,name,phone,address,pincode) VALUES (?,?,?,?,?)",
                       (email, name, phone, address, pincode))

        conn.commit()
        conn.close()

        return "<script>alert('Signup Successful');window.location='/login';</script>"

    return render_template("signup.html")



# User Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'email' in session :
        session.clear()
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM login WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['email'] = email
            return redirect('/user/products')
        else:
            return "<script>alert('Invalid Email or Password');window.location='/login';</script>"

    return render_template("login.html")

# User Logout : User Side
@app.route('/user/logout')
def user_logout():
    session.clear()
    return redirect('/')

# User Page after Login
@app.route('/user')
def user():
    if 'email' not in session:
        return redirect('/login')

    email = session['email']
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()

    return render_template("user.html", data=user)

#   Update User Profile
@app.route('/user/update_profile',methods=['GET','POST'])
def update():
    if 'email' not in session:
        return redirect('/login')
    show = False
    fix = True
    email = session['email']
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM login WHERE email=?",(email,))
    password = cursor.fetchone()
    cursor.execute("SELECT * FROM users WHERE email=?",(email,))
    user = cursor.fetchone()
    conn.close()
    if request.method == 'POST':
        old_password = request.form['old_password']
        if old_password == password[0] :
            fix = False
            show = True
        else:
            return "<script>alert('Invalid Password');window.location='/user/update_profile';</script>"

    return render_template("update.html", show = show, fix = fix, data=user, password = password[0])
#   Save New Update Details
@app.route('/user/update_profile/save_update',methods=['GET','POST'])
def save_update():
    if "email" not in session:
        return redirect('/')
    name = request.form['name']
    password = request.form['password']
    phone = request.form['phone']
    address = request.form['add']
    pincode = request.form['pincode']

    email = session.get("email")
    conn = db_conn()
    cursor = conn.cursor()
    if request.method == 'POST':
        cursor.execute("UPDATE users SET name=?, phone=?, address=?, pincode=? WHERE email=?",(name,phone,address,pincode,email))
        cursor.execute("UPDATE login SET password=? WHERE email =?",(password,email))
        conn.commit()
        conn.close()
        return "<script>alert('Profile Updated Successfully !!'); window.location='/user';</script>"
#   Delete User Profile
@app.route('/user/delete_profile',methods=['GET','POST'])
def delete():
    if "email" not in session:
        return redirect('/')
    email = session.get("email")
    conn = db_conn()
    cursor = conn.cursor()
    if request.method == 'POST':
        cursor.execute("DELETE FROM cart WHERE email = ?", (email,))
        cursor.execute("DELETE FROM orders WHERE email = ?", (email,))
        cursor.execute("DELETE FROM users WHERE email = ?", (email,))
        cursor.execute("DELETE FROM login WHERE email = ?", (email,))
        conn.commit()
        conn.close()
    return "<script>alert('Account Deleted Successfully !!'); window.location='/login';</script>"

# Show Products : User Side
@app.route('/user/products')
def products():
    if 'email' not in session:
        return redirect('/login')

    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    data = cursor.fetchall()
    conn.close()

    return render_template("show_products.html", products=data)

#   Search Product : User Side
@app.route("/search")
def search():
    q = request.args.get("q", "")
    conn = db_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT product_id, name FROM products WHERE name LIKE ? LIMIT 5",
        (q + "%",)
    )
    data = [{"id" : row[0], "name": row[1]} for row in cur.fetchall()]
    conn.close()
    return jsonify(data)

#       FullScreen Product view
@app.route('/user/product-fullscreen/<int:product_id>')
def fullScreen(product_id):
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("""SELECT * FROM products WHERE product_id = ? """,(product_id,))
    product = cur.fetchone()
    return render_template("product-full.html",product=product)
    

# Add Products to Cart : User Side
@app.route('/user/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    email = session.get('email')
    if not email :
        return redirect('/login')
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO cart(email, product_id) VALUES (?, ?)",(email, product_id))
    conn.commit()
    conn.close()
    return "<script>alert('Added to Cart');window.location='/user/cart';</script>"

# Show Cart : User Side
@app.route('/user/cart',methods=['GET','POST'])
def show_cart():
    email = session.get('email')
    if not email :
        return redirect('/login')
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("""SELECT cart.product_id, products.name, products.price, products.description, products.stock, products.image FROM cart JOIN products ON cart.product_id=products.product_id WHERE cart.email=?""",(email,))
    cart_items = cursor.fetchall()
    conn.commit()
    conn.close()
    return render_template("cart.html",items=cart_items)



# Confirm cart by selecting the quantity of individual products

# Confirm cart by selecting quantity
@app.route('/user/cart/confirm_cart', methods=['GET', 'POST'])
def confirm_cart():

    email = session.get('email')
    if not email:
        return redirect('/login')

    conn = db_conn()
    cursor = conn.cursor()

    if request.method == 'POST':

        # 🔹 1. Get quantities from form
        product_ids = request.form.getlist('product_id[]')
        product_qtys = request.form.getlist('qty[]')

        if not product_ids:
            conn.close()
            return "<script>alert('Cart Empty');window.location='/user/cart';</script>"

        # 🔹 2. Update cart table with new quantities
        for i in range(len(product_ids)):
            pid = int(product_ids[i])
            qty = int(product_qtys[i])

            cursor.execute("""
                UPDATE cart
                SET quantity=?
                WHERE email=? AND product_id=?
            """, (qty, email, pid))

        # 🔹 3. Fetch updated cart items
        cursor.execute("""
            SELECT cart.product_id,
                   products.price,
                   cart.quantity
            FROM cart
            JOIN products ON cart.product_id = products.product_id
            WHERE cart.email=?
        """, (email,))

        cart_items = cursor.fetchall()

        if not cart_items:
            conn.close()
            return "<script>alert('Cart Empty');window.location='/user/cart';</script>"

        # 🔹 4. Calculate grand total
        grand_total = 0
        for item in cart_items:
            grand_total += item[1] * item[2]

        payment_method = request.form.get('payment_method', 'COD')

        # 🔹 5. Insert into bill table
        cursor.execute("""
            INSERT INTO bill(email, bill_date, grand_total, payment_method)
            VALUES (?, ?, ?, ?)
        """, (email, datetime.now(), grand_total, payment_method))

        bill_id = cursor.lastrowid



        # 🔹 6. Insert into orders table
        for item in cart_items:
            product_id = item[0]
            price = item[1]
            qty = item[2]
            total = price * qty

            cursor.execute("SELECT purchasing_price FROM products WHERE product_id=?", (product_id,))
            p_data = cursor.fetchone()
            purchasing_price = p_data[0] if p_data and p_data[0] is not None else 0
            margin = qty * (price - purchasing_price)

            cursor.execute("""
                INSERT INTO orders(email, product_id, quantity, status, order_date, total, bill_id, margin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (email, product_id, qty, "Placed", datetime.now(), total, bill_id, margin))

            # 🔹 7. Update stock
            cursor.execute("""
                UPDATE products
                SET stock = stock - ?
                WHERE product_id=?
            """, (qty, product_id))

        # 🔹 8. Clear cart
        cursor.execute("DELETE FROM cart WHERE email=?", (email,))

        conn.commit()
        conn.close()

        return redirect(f"/user/bill/{bill_id}")

    # 🔹 GET request – show cart page
    cursor.execute("""
        SELECT cart.product_id,
               products.name,
               products.price,
               products.stock,
               products.image,
               cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.product_id
        WHERE cart.email=?
    """, (email,))

    cart_items = cursor.fetchall()
    conn.close()

    return render_template("buy_cart.html", data=cart_items)

# Place order / direct Buy : User Side
@app.route('/user/buy_product/<int:product_id>', methods=['GET','POST'])
def buy_single(product_id):

    if 'email' not in session:
        return redirect('/login')

    conn = db_conn()
    cursor = conn.cursor()

    if request.method == 'POST':

        qty = int(request.form['qty'])

        cursor.execute("SELECT price, stock, purchasing_price FROM products WHERE product_id=?", (product_id,))
        data = cursor.fetchone()

        price = data[0]
        stock = data[1]
        purchasing_price = data[2] if data[2] is not None else 0

        if qty > stock:
            conn.close()
            return "<script>alert('Not enough stock');window.history.back();</script>"

        total = price * qty
        margin = qty * (price - purchasing_price)

        payment_method = request.form.get('payment_method', 'COD')

        # 🔹 Create Bill
        cursor.execute("""
        INSERT INTO bill(email,bill_date,grand_total,payment_method)
        VALUES (?,?,?,?)
        """,(session['email'],datetime.now(),total,payment_method))

        bill_id = cursor.lastrowid



        # 🔹 Insert into orders
        cursor.execute("""
        INSERT INTO orders(email,product_id,quantity,status,order_date,total,bill_id,margin)
        VALUES (?,?,?,?,?,?,?,?)
        """,(session['email'],product_id,qty,"Placed",datetime.now(),total,bill_id,margin))

        cursor.execute("""
        UPDATE products
        SET stock = stock - ?
        WHERE product_id=?
        """,(qty,product_id))

        conn.commit()
        conn.close()

        return redirect(f"/user/bill/{bill_id}")

    # 🔹 GET → show product page
    cursor.execute("SELECT * FROM products WHERE product_id=?", (product_id,))
    product = cursor.fetchone()
    conn.close()

    return render_template("buy_product.html", product=product)


@app.route('/user/orders')
def orders():
    email = session.get('email')
    if not email:
        return redirect('/login')
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("""SELECT orders.id, products.name, products.price, orders.quantity, orders.order_date, orders.total, orders.status FROM orders JOIN products ON orders.product_id = products.product_id WHERE orders.email=? ORDER BY orders.order_date DESC""",(email,))
    orders = cursor.fetchall()
    conn.close()
    return render_template('orders.html',orders=orders)

@app.route('/user/cancel_order/<int:order_id>')
def user_cancel_order(order_id):
    email = session.get('email')
    if not email:
        return redirect('/login')
        
    conn = db_conn()
    cursor = conn.cursor()
    
    cursor.execute("SELECT product_id, quantity, status FROM orders WHERE id=? AND email=?", (order_id, email))
    order = cursor.fetchone()
    
    if order and not order[2].startswith('Cancelled'):
        product_id = order[0]
        qty = order[1]
        
        cursor.execute("UPDATE orders SET status='Cancelled by User' WHERE id=?", (order_id,))
        cursor.execute("UPDATE products SET stock = stock + ? WHERE product_id=?", (qty, product_id))
        conn.commit()
    conn.close()
    
    return redirect('/user/orders')


# Admin Route : Admin Side
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == "POST":
        admin_name = request.form['admin_name']
        password = request.form['password']

        conn = db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE admin_name=? AND password=?",(admin_name, password))
        admin = cursor.fetchone()
        conn.close()

        if admin:
            session['admin'] = admin_name
            return redirect('/admin/panel')
        else:
            return "<script>alert('Invalid Admin');window.location='/admin';</script>"

    return render_template("admin_login.html")

# Admin Panel
@app.route('/admin/panel')
def admin_panel():
    if 'admin' not in session:
        return redirect('/admin')

    conn = db_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SUM(margin) FROM orders")
        total_profit = cursor.fetchone()[0] or 0
    except:
        total_profit = 0
    conn.close()

    return render_template("admin_panel.html", total_profit=total_profit)

# Settings : Admin Side
@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if 'admin' not in session:
        return redirect('/admin')
    
    global SHOP_NAME
    if request.method == 'POST':
        SHOP_NAME = request.form.get('shop_name', 'E-Shop')
        return "<script>alert('Shop Name Updated!'); window.location='/admin/settings';</script>"
        
    return render_template('admin_settings.html', current_name=SHOP_NAME)

# View Users : Admin Side
@app.route('/admin/view_users')
def view_users_admin():
    if 'admin' not in session:
        return redirect('/admin')
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template("view_users_admin.html", users=users)

# Remove a User : Admin Side
@app.route('/admin/remove_user/<email>')
def remove_user_admin(email):
    if 'admin' not in session:
        return redirect('/admin')
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE email = ?", (email,))
    cursor.execute("DELETE FROM orders WHERE email = ?", (email,))
    cursor.execute("DELETE FROM users WHERE email = ?", (email,))
    cursor.execute("DELETE FROM login WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return "<script>alert('User Deleted Successfully !!'); window.location='/admin/view_users';</script>"

# Add new User : Admin Side
@app.route('/admin/add_user', methods=['GET', 'POST'])
def add_user_admin():
    if 'admin' not in session:
        return redirect('/admin')
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        address = request.form['address']
        pincode = request.form['pincode']

        conn = db_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO login(email,password) VALUES (?,?)", (email, password))
            cursor.execute("INSERT INTO users(email,name,phone,address,pincode) VALUES (?,?,?,?,?)",
                           (email, name, phone, address, pincode))
            conn.commit()
            msg = 'User Added Successfully !!'
        except sqlite3.IntegrityError:
            msg = 'Email already exists!'
        conn.close()
        return f"<script>alert('{msg}'); window.location='/admin/view_users';</script>"

    return render_template('add_user_admin.html')

# Update User : Admin Side
@app.route('/admin/update_user/<email>', methods=['GET', 'POST'])
def update_user_admin(email):
    if 'admin' not in session:
        return redirect('/admin')
    
    conn = db_conn()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        phone = request.form['phone']
        address = request.form['address']
        pincode = request.form['pincode']
        
        cursor.execute("UPDATE users SET name=?, phone=?, address=?, pincode=? WHERE email=?", (name, phone, address, pincode, email))
        if password: # only update if provided
            cursor.execute("UPDATE login SET password=? WHERE email=?", (password, email))
        conn.commit()
        conn.close()
        return "<script>alert('User Updated Successfully !!'); window.location='/admin/view_users';</script>"
        
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    cursor.execute("SELECT password FROM login WHERE email=?", (email,))
    login_data = cursor.fetchone()
    conn.close()
    
    return render_template('update_user_admin.html', user=user, login_data=login_data)

# View Admins : Admin Side
@app.route('/admin/view_admins')
def view_admins():
    if 'admin' not in session:
        return redirect('/admin')
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin")
    admins = cursor.fetchall()
    conn.close()
    return render_template("view_admins.html", admins=admins)

# Add Admin : Admin Side
@app.route('/admin/add_admin', methods=['GET', 'POST'])
def add_admin():
    if 'admin' not in session:
        return redirect('/admin')
    if request.method == 'POST':
        admin_name = request.form['admin_name']
        password = request.form['password']
        
        conn = db_conn()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO admin(admin_name, password) VALUES (?,?)", (admin_name, password))
        conn.commit()
        conn.close()
        return "<script>alert('Admin Added Successfully !!'); window.location='/admin/view_admins';</script>"
        
    return render_template('add_admin.html')

# Update Admin : Admin Side
@app.route('/admin/update_admin/<int:id>', methods=['GET', 'POST'])
def update_admin(id):
    if 'admin' not in session:
        return redirect('/admin')
        
    conn = db_conn()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        admin_name = request.form['admin_name']
        password = request.form['password']
        
        cursor.execute("UPDATE admin SET admin_name=?, password=? WHERE admin_id=?", (admin_name, password, id))
        conn.commit()
        conn.close()
        return "<script>alert('Admin Updated Successfully !!'); window.location='/admin/view_admins';</script>"
        
    cursor.execute("SELECT * FROM admin WHERE admin_id=?", (id,))
    admin = cursor.fetchone()
    conn.close()
    
    return render_template('update_admin.html', admin=admin)

# Remove Admin : Admin Side
@app.route('/admin/remove_admin/<int:id>')
def remove_admin(id):
    if 'admin' not in session:
        return redirect('/admin')
    conn = db_conn()
    cursor = conn.cursor()
    # Ensure they don't delete the last admin
    cursor.execute("SELECT COUNT(*) FROM admin")
    count = cursor.fetchone()[0]
    if count <= 1:
        return "<script>alert('Cannot delete the last admin!'); window.location='/admin/view_admins';</script>"
    
    cursor.execute("DELETE FROM admin WHERE admin_id=?", (id,))
    conn.commit()
    conn.close()
    return "<script>alert('Admin Deleted Successfully !!'); window.location='/admin/view_admins';</script>"

# Add New Products : Admin Side
@app.route('/admin/add_product', methods=['GET','POST'])
def add_product():
    if request.method == 'POST' :
        name = request.form['p_name']
        price = request.form['price']
        stock = request.form['stock']
        image = request.files['image']
        desc = request.form['desc']
        purchasing_price = request.form.get('purchasing_price', 0)
        filename = image.filename
        image.save("static/uploads/" + filename)
        conn = db_conn()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO products(name, price, stock, description, image, purchasing_price) VALUES(?,?,?,?,?,?)""",(name, price, stock, desc, filename, purchasing_price))
        conn.commit()
        conn.close()
        return redirect('/admin/view_products_admin')
    return render_template('add_product.html')

# View Products : Admin Side
@app.route('/admin/view_products_admin')
def view_products_admin():
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM products""")
    data = cursor.fetchall()
    cursor.close()
    return render_template("view_products_admin.html",data=data)

# View Orders : Admin Side
@app.route('/admin/view_orders')
def admin_view_orders():
    if 'admin' not in session:
        return redirect('/admin')
    
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT orders.id, users.name, users.email, products.name, 
               orders.quantity, orders.total, orders.order_date, orders.status, 'COD' as payment_method, orders.margin
        FROM orders
        JOIN products ON orders.product_id = products.product_id
        JOIN users ON orders.email = users.email
        ORDER BY orders.order_date DESC
    """)
    orders = cursor.fetchall()
    conn.close()
    
    return render_template('admin_orders.html', orders=orders)

# Cancel Order : Admin Side
@app.route('/admin/cancel_order/<int:order_id>')
def admin_cancel_order(order_id):
    if 'admin' not in session:
        return redirect('/admin')
        
    conn = db_conn()
    cursor = conn.cursor()
    
    cursor.execute("SELECT product_id, quantity, status FROM orders WHERE id=?", (order_id,))
    order = cursor.fetchone()
    
    if order and not order[2].startswith('Cancelled'):
        product_id = order[0]
        qty = order[1]
        
        cursor.execute("UPDATE orders SET status='Cancelled by Admin' WHERE id=?", (order_id,))
        cursor.execute("UPDATE products SET stock = stock + ? WHERE product_id=?", (qty, product_id))
        conn.commit()
        
    conn.close()
    return redirect('/admin/view_orders')

# Update Product Details : Admin Side
@app.route('/admin/update_product_page/<int:id>',methods=['GET','POST'])
def update_product_page(id):
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE product_id=?",(id,))
    product = cursor.fetchone()
    if request.method == 'POST':
        name = request.form["p_name"]
        price = request.form["price"]
        desc = request.form['desc']
        stock = request.form["stock"]
        image = request.files["image"]
        purchasing_price = request.form.get('purchasing_price', 0)
        if image and image.filename != "":
            filename = image.filename
            image.save("static/uploads/" + filename)
            cursor.execute("""UPDATE products SET name=?, price=?, stock=?, image=?,description=?,purchasing_price=?  WHERE product_id=?""",(name,price,stock,filename,desc,purchasing_price,id))
        else:
        #If new image is not uploaded
            cursor.execute("""UPDATE products SET name=?, price=?, stock=?, purchasing_price=? WHERE product_id=?""",(name,price,stock,purchasing_price,id))
        conn.commit()
        conn.close()
        return "<script>alert('Data Updated Successfully !!'); window.location='/admin/view_products_admin';</script>"
    # conn.close(
    return render_template("update_products_page.html",p=product)

# Remove a Product : Admin Side
@app.route('/admin/remove_product/<int:id>')
def remove_product(id):
    conn = db_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM cart WHERE product_id=?", (id,))
        cursor.execute("DELETE FROM orders WHERE product_id=?", (id,))
        cursor.execute("DELETE FROM products WHERE product_id=?",(id,))
        conn.commit()
        msg = "Product and its history in orders and carts deleted successfully !!"
    except Exception as e:
        msg = f"An error occurred: {str(e)}"
    finally:
        conn.close()
    return f"<script>alert('{msg}'); window.location='/admin/view_products_admin';</script>"
# Quick Update Prices : Admin Side
@app.route('/admin/quick_update_price/<int:product_id>', methods=['POST'])
def quick_update_price(product_id):
    if 'admin' not in session:
        return redirect('/admin')
        
    cost = float(request.form.get('cost', 0.0))
    price = float(request.form.get('price', 0.0))
    
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET purchasing_price=?, price=? WHERE product_id=?", (cost, price, product_id))
    conn.commit()
    conn.close()
    
    return redirect('/admin/view_products_admin')

@app.route('/user/bill/<int:bill_id>')
def view_bill(bill_id):

    email = session.get('email')
    if not email:
        return redirect('/login')

    conn = db_conn()
    cursor = conn.cursor()

    # Bill info
    cursor.execute("SELECT * FROM bill WHERE bill_id=?", (bill_id,))
    bill_data = cursor.fetchone()

    formatted_date = bill_data[2] if bill_data else ""
    if formatted_date and '.' in formatted_date:
        formatted_date = formatted_date.split('.')[0]

    # Product list
    cursor.execute("""
    SELECT products.name,
           orders.quantity,
           orders.total
    FROM orders
    JOIN products ON orders.product_id = products.product_id
    WHERE orders.bill_id=?
    ORDER BY orders.order_date DESC
    """,(bill_id,))

    items = cursor.fetchall()

    payment_method = bill_data[4] if len(bill_data) > 4 else "COD"

    conn.close()

    return render_template("bill.html",
                           bill=bill_data,
                           items=items,
                           payment_method=payment_method,
                           formatted_date=formatted_date)