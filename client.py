from flask import Flask, jsonify, render_template, request, redirect, flash
import requests
import sqlite3
import json

app=Flask(__name__)
app.secret_key = '11218413'

base_url = 'http://127.0.0.1:5000/users'
sqldbname = 'Organic_farm.db'

@app.route('/users', methods = ['GET'])
def get_users():

    conn = sqlite3.connect(sqldbname)
    cur = conn.cursor()
    cur.execute('select * from user')
    users = cur.fetchall()
    users_list = []

    for user in users:
        users_list.append({'userid': user[0], 'username': user[1],'password': user[2], 'email': user[3]})
    return jsonify(users_list)

@app.route('/')
def index():
    response = requests.get(base_url)
    if response.status_code == 200:
        users = response.json()
        return render_template('user.html', users=users)
    else:
        flash('Something went wrong. Please try again later!')
    return render_template('user.html')

@app.route('/add', methods=['get', 'post'])
def add():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if username and email and password:
            response = requests.post(base_url)
            json = {'username':username, 'email':email, 'password': password}
            if response.status_code == 200:
                user = response.json()
                flash('user added successfully.')
                return redirect('/')
            else:
                flash('Something went wrong.')
                return render_template('/')


if __name__ == '__main__':
    app.run(debug=True, port=5001)