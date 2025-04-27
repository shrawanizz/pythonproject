from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta 
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg') 
load_dotenv() # Load environment variables from .env file



conn = mysql.connector.connect(
    host="localhost",        
    port=3306,               
    user="root",
    password="shrawanideshmukh",
    database="budgetbuddie"
)

cursor = conn.cursor(dictionary=True)

app = Flask(__name__)

#app.secret_key = os.getenv('SECRET_KEY')
app.secret_key = '8c0f560fe793bc1ca1899625700c6c0b'




@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        # Get form data
        username = request.form['email']
        password = request.form['password']
        # Check if the user exists in the database
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            # Verify the password
            if check_password_hash(user['password'], password):
                # Password is correct, redirect to the home page
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('home'))
        
        else:
            # User not found
            return "Invalid email or password. Please try again."
            
        
    
    return render_template('login.html')


# Add a new expense (ADD EXPENSE)
@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    title = request.form['title']
    category = request.form['category']
    amount = request.form['amount']
    date = request.form.get('date')
    if not date:
        date = datetime.today()
    else:
        date = datetime.strptime(date, '%Y-%m-%d')

    user_id = session['user_id']  # Assuming the user is logged in

    cursor.execute(
        "INSERT INTO expenses (user_id, title, category, amount, date) VALUES (%s, %s, %s, %s, %s)",
        (user_id, title, category, amount, date)
    )
    conn.commit()
    return redirect(url_for('add_expense_page'))


# Delete an expense (DELETE EXPENSE)
@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cursor.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
    conn.commit()
    return redirect(url_for('view_expense_page'))

#Show the Edit form
@app.route('/edit_expense/<int:expense_id>', methods=['GET'])
def edit_expense(expense_id):
    cursor.execute("SELECT * FROM expenses WHERE id = %s", (expense_id,))
    expense = cursor.fetchone()
    return render_template('edit_expense.html', expense=expense)

#Show the Update form
@app.route('/update_expense/<int:expense_id>', methods=['POST'])
def update_expense(expense_id):
    title = request.form['title']
    category = request.form['category']
    amount = request.form['amount']

    cursor.execute(
        "UPDATE expenses SET title = %s, category = %s, amount = %s WHERE id = %s",
        (title, category, amount, expense_id)
    )
    conn.commit()
    return redirect(url_for('view_expense_page'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Check if the passwords match
        if password != confirm_password:
            return "Passwords do not match. Please try again."
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        # Check if the email already exists in the database
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            return "Email already registered. Please login or use a different email."
        
        # Insert the new user into the database
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
        
        return render_template('login.html')
    
    return render_template('register.html')


@app.route('/')
def home():
    if 'user_id' in session:
        # User is logged in, show the home page
        
        user_id = session['user_id']
        search_query = request.args.get('query')
        amount = request.args.get('amount')
        date = request.args.get('date')
        # Fetch expenses from the database
        sql = "SELECT id,title, category, amount, date FROM expenses WHERE user_id = %s"
        params = [user_id]

        if search_query:
            sql +=" AND (title LIKE %s OR category LIKE %s)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])

        if amount:
            sql += " AND amount = %s"
            params.append(amount)
        
        if date:
            sql += " AND DATE(date) = %s"
            params.append(date)
        
        cursor.execute(sql, tuple(params))
        expenses = cursor.fetchall()

        total = sum(exp['amount'] for exp in expenses)       
        

        return render_template('index.html', expenses=expenses, total=total,)
    
    else:
        # User is not logged in, redirect to the login page
        return redirect(url_for('login'))
    
#Add expense page rendering
@app.route('/add_expense_page')
def add_expense_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cursor.execute("SELECT * FROM expenses order by date desc limit 3")
    expenses = cursor.fetchall()    
    return render_template('add_expense.html',expenses=expenses)


#View expense page rendering
@app.route('/view_expense_page')
def view_expense_page():
    if 'user_id' in session:
        # User is logged in, show the home page
        
        user_id = session['user_id']
        search_query = request.args.get('query')
        amount = request.args.get('amount')
        date = request.args.get('date')
        # Fetch expenses from the database
        sql = "SELECT id,title, category, amount, date FROM expenses WHERE user_id = %s"
        params = [user_id]

        if search_query:
            sql +=" AND (title LIKE %s OR category LIKE %s)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])

        if amount:
            sql += " AND amount = %s"
            params.append(amount)
        
        if date:
            sql += " AND DATE(date) = %s"
            params.append(date)
        
        cursor.execute(sql, tuple(params))
        expenses = cursor.fetchall()

        return render_template('view_expense.html', expenses=expenses)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/monthly_expense_page', methods=['GET', 'POST'])
def monthly_expense_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get current year and create options for last 2 years
    current_year = datetime.now().year
    years = [current_year, current_year-1, current_year-2]
    
    # For form submission
    if request.method == 'POST':
        selected_month = int(request.form.get('month', datetime.now().month))
        selected_year = int(request.form.get('year', current_year))
    else:
        # Default to current month if no selection
        selected_month = datetime.now().month
        selected_year = current_year
    
    # Fetch data for pie chart (category-wise expenses for selected month)
    cursor.execute("""
        SELECT category, SUM(amount) as total_amount 
        FROM expenses 
        WHERE user_id = %s 
        AND MONTH(date) = %s 
        AND YEAR(date) = %s 
        GROUP BY category
    """, (user_id, selected_month, selected_year))
    
    pie_data = cursor.fetchall()
    
    # Fetch data for line chart (month-wise total expenses for the selected year)
    cursor.execute("""
        SELECT MONTH(date) as month, SUM(amount) as total_amount 
        FROM expenses 
        WHERE user_id = %s 
        AND YEAR(date) = %s 
        GROUP BY MONTH(date)
        ORDER BY MONTH(date)
    """, (user_id, selected_year))
    
    line_data = cursor.fetchall()
    
    # Prepare data for charts
    categories = [item['category'] for item in pie_data]
    category_amounts = [float(item['total_amount']) for item in pie_data]
    
    # Calculate total for the selected month
    monthly_total = sum(category_amounts) if category_amounts else 0
    
    # Get month name
    month_name = datetime(2000, selected_month, 1).strftime('%B')
    
    # Make sure static directory exists
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    os.makedirs(static_dir, exist_ok=True)
    
    # Generate unique filenames with timestamp to avoid caching issues
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    pie_chart_filename = f"pie_chart_{user_id}_{timestamp}.png"
    line_chart_filename = f"line_chart_{user_id}_{timestamp}.png"
    
    # Full paths for saving the charts
    pie_chart_path = os.path.join(static_dir, pie_chart_filename)
    line_chart_path = os.path.join(static_dir, line_chart_filename)
    
    # Generate the charts
    try:
        # Generate pie chart
        plt.figure(figsize=(8, 6))
        if categories and category_amounts:
            # Create the pie chart with exploded slices
            plt.pie(
                category_amounts, 
                labels=categories, 
                autopct='%1.1f%%', 
                startangle=90,
                shadow=True,
                explode=[0.05] * len(categories)  # Slight explosion of all pie slices
            )
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            plt.title(f'Category-wise Expenses Breakdown - {month_name} {selected_year}', fontsize=14)
        else:
            # No data case
            plt.text(0.5, 0.5, "No expense data available for this month", 
                    ha='center', va='center', fontsize=12)
            plt.axis('off')
        
        plt.savefig(pie_chart_path)
        plt.close()
        
        # Generate line chart that shows all months from January
        plt.figure(figsize=(10, 6))
        
        # Month names for x-axis labels (all 12 months)
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Create a dictionary to map actual data to all months
        monthly_data = {i+1: 0 for i in range(12)}  # Initialize all months to zero
        
        # Fill in actual data where available
        for item in line_data:
            monthly_data[item['month']] = float(item['total_amount'])
        
        # Get all monthly totals in order from January to December
        monthly_totals = [monthly_data[i+1] for i in range(12)]
        
        # Plot the line chart with markers
        plt.plot(month_names, monthly_totals, marker='o', linestyle='-', 
                linewidth=2, markersize=8, color='#3366cc')
        
        # Fill area under the line
        plt.fill_between(month_names, monthly_totals, alpha=0.2, color='#3366cc')
        
        # Grid lines
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Labels and title
        plt.xlabel('Month', fontsize=12)
        plt.ylabel('Total Expenses (₹)', fontsize=12)
        plt.title(f'Monthly Expenses Trend - {selected_year}', fontsize=14)
        
        # Format y-axis to show rupee values
        plt.gca().yaxis.set_major_formatter(
            plt.matplotlib.ticker.StrMethodFormatter('₹{x:,.0f}')
        )
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        
        # Add value labels only to non-zero points
        for i, amount in enumerate(monthly_totals):
            if amount > 0:
                plt.annotate(
                    f'₹{amount:,.0f}', 
                    (month_names[i], amount),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha='center',
                    fontsize=9
                )
        
        plt.tight_layout()
        plt.savefig(line_chart_path)
        plt.close()
        
    except Exception as e:
        print(f"Error generating charts: {e}")
        # Provide default empty chart filenames in case of error
        pie_chart_filename = "no_data.png"
        line_chart_filename = "no_data.png"
    
    return render_template(
        'monthly_expense.html',
        years=years,
        selected_month=selected_month,
        selected_year=selected_year,
        pie_chart_filename=pie_chart_filename,
        line_chart_filename=line_chart_filename,
        monthly_total=monthly_total,
        month_name=month_name
        # Removed categories and category_amounts to prevent separate expense listing
    ) 
if __name__ == '__main__':
    app.run(debug=True)