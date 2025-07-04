from flask import Flask, render_template, request, redirect, url_for, flash
import csv
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

DATA_FOLDER = "data"
CSV_FILE = os.path.join(DATA_FOLDER, "transactions.csv")
MONTHLY_BUDGET =    5000

os.makedirs(DATA_FOLDER, exist_ok=True)

def load_transactions():
    transactions = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['amount'] = float(row['amount'])
                row['id'] = int(row['id'])
                transactions.append(row)
    return transactions

def save_transactions(transactions):
    with open(CSV_FILE, mode='w', newline='') as f:
        fieldnames = ["id", "date", "type", "category", "amount", "description"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for txn in transactions:
            writer.writerow(txn)

def check_budget(transactions):
    this_month = datetime.now().strftime("%Y-%m")
    total_expense = sum(txn['amount'] for txn in transactions if txn['type'] == 'expense' and txn['date'].startswith(this_month))
    return total_expense > MONTHLY_BUDGET, total_expense

@app.route('/')
def index():
    transactions = load_transactions()
    budget_exceeded, total_expense = check_budget(transactions)
    return render_template('index.html', transactions=transactions, 
                           budget_exceeded=budget_exceeded, total_expense=total_expense, monthly_budget=MONTHLY_BUDGET)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        transactions = load_transactions()
        new_id = transactions[-1]['id'] + 1 if transactions else 1

        txn = {
            "id": new_id,
            "date": request.form['date'],
            "type": request.form['type'],
            "category": request.form['category'],
            "amount": float(request.form['amount']),
            "description": request.form['description']
        }
        transactions.append(txn)
        save_transactions(transactions)
        flash("Transaction added successfully.")
        return redirect(url_for('index'))

    return render_template('add.html')

@app.route('/edit/<int:txn_id>', methods=['GET', 'POST'])
def edit(txn_id):
    transactions = load_transactions()
    txn = next((t for t in transactions if t['id'] == txn_id), None)
    if not txn:
        return "Transaction not found", 404

    if request.method == 'POST':
        txn['date'] = request.form['date']
        txn['type'] = request.form['type']
        txn['category'] = request.form['category']
        txn['amount'] = float(request.form['amount'])
        txn['description'] = request.form['description']
        save_transactions(transactions)
        flash("Transaction updated successfully.")
        return redirect(url_for('index'))

    return render_template('edit.html', txn=txn)

@app.route('/delete/<int:txn_id>', methods=['POST'])
def delete(txn_id):
    transactions = load_transactions()
    transactions = [t for t in transactions if t['id'] != txn_id]
    # Re-assign IDs sequentially
    for i, t in enumerate(transactions, 1):
        t['id'] = i
    save_transactions(transactions)
    flash("Transaction deleted successfully.")
    return redirect(url_for('index'))

@app.route('/sSummary')
def summary():
    transactions = load_transactions()
    this_month = datetime.now().strftime("%Y-%m")
    income = sum(txn['amount'] for txn in transactions if txn['type'] == 'income' and txn['date'].startswith(this_month))
    expense = sum(txn['amount'] for txn in transactions if txn['type'] == 'expense' and txn['date'].startswith(this_month))
    savings = income - expense
    return render_template('summary.html', month=this_month, income=income, expense=expense, savings=savings)

if __name__ == "__main__":
    app.run(debug=True)
