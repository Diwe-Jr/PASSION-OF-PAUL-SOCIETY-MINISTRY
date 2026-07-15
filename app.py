from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)

app.secret_key = "pops@2017"

# 🔹 Init database
def init_db():
    conn = sqlite3.connect('donations.db')
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            phone TEXT,
            amount REAL,
            category TEXT,
            month TEXT,
            year INTEGER,
            payment_status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

init_db()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/donate', methods=['POST'])
def donate():
    name = request.form['name']
    phone = request.form['phone']
    amount = float(request.form['amount'])
    category = request.form['category']
    month = request.form['month']
    year = 2026

    conn = sqlite3.connect('donations.db')
    cursor = conn.cursor()

    # duplicate check
    cursor.execute("""
        SELECT * FROM donations
        WHERE phone=? AND month=? AND year=?
    """, (phone, month, year))

    if cursor.fetchone():
        conn.close()
        return "<h3>Already donated for this month</h3><a href='/'>Back</a>"

    # insert donation (Pending payment)
    cursor.execute("""
        INSERT INTO donations
        (full_name, phone, amount, category, month, year, payment_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, phone, amount, category, month, year, "Pending"))

    conn.commit()
    conn.close()

    return render_template('donate.html')

@app.route('/thankyou')
def thankyou():
    return render_template('donate.html')


@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect('/login')

    conn = sqlite3.connect('donations.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM donations ORDER BY id DESC")
    donations = cursor.fetchall()

    cursor.execute("SELECT COALESCE(SUM(amount),0) FROM donations")
    total_amount = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM donations")
    total_records = cursor.fetchone()[0]

    cursor.execute("""
        SELECT month, SUM(amount)
        FROM donations
        GROUP BY month
    """)
    monthly_data = cursor.fetchall()

    conn.close()

    return render_template(
        'admin.html',
        donations=donations,
        total_amount=total_amount,
        total_records=total_records,
        monthly_data=monthly_data
    )

@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []

    if request.method == 'POST':
        keyword = request.form['keyword']

        conn = sqlite3.connect('donations.db')
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM donations
            WHERE full_name LIKE ?
            OR phone LIKE ?
            ORDER BY id DESC
        """, (f"%{keyword}%", f"%{keyword}%"))

        results = cursor.fetchall()
        conn.close()

    return render_template('search.html', results=results)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "pops@2017":
            session['logged_in'] = True
            return redirect('/admin')
        else:
            return render_template('login.html', error="Wrong credentials")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')



import pandas as pd
import sqlite3
from flask import send_file
import os

@app.route('/export')
def export_excel():
    try:
        conn = sqlite3.connect('donations.db')

        df = pd.read_sql_query("""
            SELECT full_name, phone, amount, category, month, year
            FROM donations
            ORDER BY id DESC
        """, conn)

        conn.close()

        file_path = "donations_report.xlsx"
        df.to_excel(file_path, index=False, engine='openpyxl')

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return f"Export failed: {str(e)}"

@app.route('/mark-paid/<int:id>')
def mark_paid(id):
    conn = sqlite3.connect('donations.db')
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE donations
        SET payment_status='Paid'
        WHERE id=?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect('/admin')

@app.route('/')
def home():
    return render_template('index.html')

first_name = request.form['first_name']
last_name = request.form['last_name']
phone = request.form['phone']
amount = request.form['amount']
payment_method = request.form['payment_method']
country = request.form['country']
city = request.form['city']


if __name__ == '__main__':
    app.run(debug=True)