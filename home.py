import datetime
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, flash
import sqlite3
import stripe

app = Flask(__name__)
app.secret_key = "group8"
sqldbname = 'Organic_farm.db'
stripe.api_key = 'YOUR_STRIPE_SECRET_KEY'


@app.route('/users', methods=['GET'])
def users():
    conn = sqlite3.connect(sqldbname)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return jsonify(users)


#Lấy các shop
def get_users():
    conn = sqlite3.connect(sqldbname)
    cur = conn.cursor()
    #query the db for all users
    cur.execute("select * from users")
    users = cur.fetchall()
    #convert the result to a list of dictionaries
    users_list = []
    for user in users:
        users_list.append({'id':user[0], 'name': user[1]})
    #return the list as a json response
    return users_list



@app.route('/')
def home():
    if 'current_user' in session:
        current_username = session['current_user']['name']
    else:
        current_username = ""
    return render_template('home.html', search_text="", username=current_username)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['txt_email']
        password = request.form['txt_password']

        # store 'username' in the session
        obj_user = get_obj_user(email, password)
        if int(obj_user[0]) > 0:
            obj_user = {
                "id": obj_user[0],
                "name": obj_user[1],
                "email": obj_user[2]
            }
            session['current_user'] = obj_user
        return redirect(url_for('home'))
    return render_template('login.html')


def get_obj_user(email, password):
    result = [],

    conn = sqlite3.connect(sqldbname)
    cursor = conn.cursor()
    sqlcommand = "SELECT * FROM users WHERE email = ? and password = ?"
    cursor.execute(sqlcommand, (email, password))

    obj_user = cursor.fetchone()
    if len(obj_user) > 0:
        result = obj_user
    conn.close()
    return result

#logout
@app.route('/logout')
def logout():
    session.pop('current_user', None)
    # remove 'username' from the session
    return redirect(url_for('home'))

#regis
@app.route('/register', methods=['GET','POST'])
def register():
    con=None
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            address = request.form['address']
            phone = request.form['phone']

            if is_email_taken(email):
                email_error=flash('Email đã tồn tại. Vui lòng chọn email khác.', 'error')
                return redirect(url_for('register'))

            if is_password_taken(password):
                password_error=flash('Mật khẩu đã tồn tại. Vui lòng chọn mật khẩu khác.', 'error')
                return redirect(url_for('register'))

            with sqlite3.connect(sqldbname) as con:
                cur = con.cursor()
                cur.execute('INSERT INTO users (username, password, email, address, phone) VALUES (?, ?, ?, ?, ?)', (username, password, email, address, phone))
                con.commit()
            register_success = "Đăng kí thành công!!"
            print(register_success)
            flash("Bản ghi đã được thêm", "Thành công")
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Xảy ra lỗi: {str(e)}")
            flash("Xảy ra lỗi", "Lỗi")

        
    return render_template('register.html')

def is_email_taken(email):
    con = sqlite3.connect(sqldbname)
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    result = cur.fetchone()
    con.close()
    return result is not None

def is_password_taken(password):
    con = sqlite3.connect(sqldbname)
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE password=?", (password,))
    result = cur.fetchone()
    con.close()
    return result is not None

@app.route(rule='/MyAccount')
def myaccount():
    render_template('myaccount.html')

#shop của mình
@app.route(rule='/MyAccount/MyShop', methods=['get'])
def myshop():
        if 'current_user' in session:
            current_username = session['current_user']['name']
        else:
            current_username = ""
        
        plants = get_plants()
        return render_template('myshop_product.html', plants = plants, username=current_username)

def get_plants():
    user_id = session.get('current_user', {}).get('id')
    if user_id:
        conn = sqlite3.connect(sqldbname)
        cur = conn.cursor()
        cur.execute('select Picture,PlantName, Price, Quantity, Rating from plants where userid="{}"'.format(user_id))
        products = cur.fetchall()
        conn.close()
    return products

#shopping
@app.route(rule='/shopping', methods=['get'])
def shopping():
    if 'current_user' in session:
        current_username = session['current_user']['name']
    else:
        current_username = ""
    shops=get_shop()
    return render_template('shopping.html', shops=shops, username=current_username)
    

def get_shop():
    conn=sqlite3.connect(sqldbname)
    cur=conn.cursor()
    cur.execute('select userid, avatar, username, shopname from users where userid in (select distinct userid from plants)')
    shops = cur.fetchall()
    conn.close()
    return shops
        

#Sản phẩm của 1 shop nào đó
@app.route('/shop/<int:userid>', methods=['get'])
def shop_products(userid):
    if 'current_user' in session:
        current_username = session['current_user']['name']
    else:
        current_username = ""
    conn = sqlite3.connect(sqldbname)
    cur = conn.cursor()
    sql_command = "SELECT shopname, avatar FROM users WHERE userid NOT IN (?)"
    cur.execute(sql_command, (userid,))
    shop = cur.fetchone()
    cur.execute('SELECT plantid,picture, plantname, price FROM plants WHERE userid="{}"'.format(userid))
    products = cur.fetchall()
    conn.close()
    return render_template('shop_products.html', plants=products, username=current_username, shop=shop)


#search
@app.route(rule='/searchData', methods=['POST'])
def searchData():
    if 'current_user' in session:
        current_username = session['current_user']['name']
    else:
        current_username = ""
    search_text = request.form['searchInput']
    html_table = load_data_from_db(search_text)
    print(html_table)
    return render_template('pr_test.html',
                           search_text=search_text,
                           table=html_table, username=current_username)

def load_data_from_db(search_text):
    if search_text != "":
        conn = sqlite3.connect(sqldbname)
        cursor = conn.cursor()
        sqlcommand = "SELECT * FROM plants WHERE plantname LIKE ? collate nocase"
        cursor.execute(sqlcommand, ('%' + search_text + '%',))
        data = cursor.fetchall()
        conn.close() 
        return data

#thêm giỏ hàng
@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    #1. Declare Database to get price
    #2. Get the product id and quantity from the form
    plant_id = request.form["plant_id"]
    quantity = int(request.form["quantity"])

    #3. get the product name and price from the database
    # or change the structure of shopping cart
    print(plant_id, quantity)
    connection = sqlite3.connect(sqldbname)
    cursor = connection.cursor()
    cursor.execute("SELECT PlantName, Price FROM plants WHERE PlantID = '{}'".format(plant_id))
    #3.1. get one product
    plant = cursor.fetchone()
    print(plant)
    connection.close()
    #4. create a dictionary for the product
    plant_dict = {
        "id": plant_id,
        "name": plant[0],
        "price": plant[1],
        "quantity": quantity
    }
    #5. get the cart from the session or create an empty list
    cart = session.get("cart", [])

    #6. check if the product is already in the cart
    found = False
    for item in cart:
        if item["id"] == plant_id:
            #6.1 update the quantity of the existing product
            item["quantity"] += quantity
            found = True
            break

    if not found:
        #6.2 add the new product to the cart
        cart.append(plant_dict)
    #7. save the cart back to the session
    session["cart"] = cart

    #8. Print out
    rows = len(cart)
    outputmessage = ("Thêm vào giỏ hàng thành công! "
                     "</br>Hiện tại: ")+str(rows) + " sản phẩm."
    # return a success message
    return outputmessage

#Xem giỏ hàng
@app.route("/viewcart", methods=["POST"])
def view_cart():
    # get the cart from the session or create an empty list
    # render the cart.html template and pass the cart
    current_cart = []
    if 'cart' in session:
        current_cart = session.get("cart", [])
    return render_template(
        "cart.html",
        carts=current_cart)

#################################################

def get_plant(plantid):
    conn = sqlite3.connect(sqldbname)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM plants WHERE plantid = ?', (plantid,))
    plant = cursor.fetchone()
    conn.close()
    return plant

def calculate_total(cart):
    return sum(plant['price'] for plant in cart)

@app.route('/pay', methods=['GET', 'POST'])
def pay():
    return render_template("payment.html")

@app.route('/payment', methods=['GET', 'POST'])
def payment():

    if 'cart' not in session or not session['cart']:
        flash('Giỏ hàng trống. Vui lòng thêm sản phẩm vào giỏ hàng trước.', 'warning')
        return redirect(url_for('home'))

    if 'current_user' not in session:
        flash('Vui lòng đăng nhập trước khi thanh toán.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Lấy thông tin khách hàng từ form
        customer_id = request.form.get('receiver_id')
        customer_email = request.form.get('receiver_mail')
        shipping_address = request.form.get('receiver_address')
        customer_phone = request.form.get('receiver_phone')
        payment_method = request.form.get('payment_method')

        if payment_method == 'online':
            return render_template("charge.html")
        elif payment_method == 'offline':

            # Lưu thông tin đơn hàng vào cơ sở dữ liệu
            conn = sqlite3.connect(sqldbname)
            cursor = conn.cursor()

        # Tạo đơn hàng
            cursor.execute('''
                INSERT INTO orders (userid, email, address, phone, shipdate)
                VALUES (?, ?, ?, ?, ?)
                ''', (customer_id, customer_email, shipping_address, customer_phone, datetime.now()))

        # Lấy ID của đơn hàng vừa tạo
            order_id = cursor.lastrowid

        # Thêm mục chi tiết đơn hàng
            for plant in session['cart']:
                cursor.execute('''
                    INSERT INTO order_details (id, plantid, price, quantity)
                    VALUES (?, ?, ?, ?)
                    ''', (order_id, plant['id'], plant['price'], plant['quantity']))

            conn.commit()
            conn.close()

        # Xóa giỏ hàng sau khi thanh toán
            session.pop('cart', None)
            flash('Thanh toán thành công! Đơn hàng của bạn đã được đặt.', 'success')

            return redirect(url_for('view_cart'))

        return render_template('payment.html')
    else:
        return ('Lỗi thanh toán')


@app.route('/charge', methods=['POST'])
def charge():
    if request.method == 'POST':
        # Nhận thông tin từ form thanh toán
        token = request.form['stripeToken']
        email = request.form['email']
        amount = 0  

        # Kiểm tra xem email có trong cơ sở dữ liệu không
        conn = sqlite3.connect(sqldbname)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if user:
            try:
                # Tạo một giao dịch sử dụng token từ Stripe
                charge = stripe.Charge.create(
                    amount=amount,
                    currency='VND',
                    description='Thanh toán bằng thẻ',
                    source=token,
                )
                return render_template('success.html', amount=amount)
            except stripe.error.CardError as e:
                # Xử lý lỗi thẻ tín dụng
                return render_template('error.html', error=str(e))
        else:
            return render_template('error.html', error='Email không tồn tại trong cơ sở dữ liệu.')

@app.route(rule='/blog')
def show_post():
    html_table_posts = take_all_post()
    print(html_table_posts)
    return render_template(template_name_or_list='blog.html', table=html_table_posts)

def take_all_post():
    # Kết nối đến cơ sở dữ liệu
    conn = sqlite3.connect('Organic_farm.db')
    cursor = conn.cursor()

    # Truy vấn tất cả các sản phẩm
    cursor.execute('SELECT * FROM blogs')
    posts = cursor.fetchall()
    # Đóng kết nối
    conn.close()
    return posts

#Admin
def get_db_connection():
    conn = sqlite3.connect(sqldbname)
    conn.row_factory=sqlite3.Row
    return conn

@app.route('/admin')
def admin():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('select * from plants')
    plants = cursor.fetchall()
    print(plants)
    conn.close()
    return render_template('/Admin/Storages/index.html', plants=plants)

@app.route(rule='/add', methods=['get', 'post'])
def add():
    if request.method =='POST':
        plantid = request.form['plantid']
        plantname = request.form['plantname']
        type = request.form['type']
        rating = request.form['rating']
        picture = request.form['picture']
        details = request.form['details']
        price = request.form['price']
        quantity = request.form['quantity']
        conn = get_db_connection()
        cursor  = conn.cursor()
        cursor.execute('insert into plants (plantid, plantname, type, rating, picture, details, price, quantity) values (?,?,?,?,?,?,?,?)',\
                       (plantid, plantname, type, rating, picture, details, price, quantity))
        conn.commit()
        conn.close()

        flash('plant added successfully', 'success')
        return redirect(url_for('admin'))
    return render_template('/Admin/Storages/add.html')

@app.route(rule='/edit/<int:plantid>', methods = ['get', 'post'])
def edit(plantid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('select * from plants where plantid = ?', (plantid,))
    plant = cursor.fetchone()
    conn.close()
    if request.method == 'POST':
        plantid = request.form['plantid']
        plantname = request.form['plantname']
        type = request.form['type']
        rating = request.form['rating']
        picture = request.form['picture']
        details = request.form['details']
        price = request.form['price']
        quantity = request.form['quantity']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('update plants set plantname=?, type=?, rating=?, picture=?, details=?, price=?, quantity=? where plantid=?',\
                       (plantname, type, rating, picture, details, price, quantity, plantid,))
        conn.commit()
        conn.close()
        flash('plant updated successfully!', 'success')
        return redirect(url_for('admin'))
    return render_template('/Admin/Storages/edit.html', plant=plant)

@app.route(rule='/delete/<int:plantid>', methods = ['post'])
def delete(plantid):
    conn=get_db_connection()
    cursor=conn.cursor()
    cursor.execute('delete from plants where plantid=?', (plantid,))
    conn.commit()
    conn.close()

    flash('plant deleted successfully!', 'success')
    return redirect(url_for('admin'))


if __name__ == "__main__":
    app.run(debug=True)