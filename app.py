# Import necessary modules
from database import (create_user, verify_user, get_user_by_email, test_connection,
                     create_donation, get_all_donations, get_donations_by_donor, 
                     claim_donation, get_claimed_donations_by_ngo,
                     get_pending_pickups, assign_volunteer_to_transaction,
                     get_volunteer_assignments, complete_transaction,
                     search_donations, get_all_users, get_platform_stats,
                     verify_ngo, get_all_transactions_admin)
from flask import Flask, render_template, request, redirect, url_for, session
from config import SECRET_KEY, DEBUG, PORT


# Create Flask app
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Test database connection on startup
print("\n" + "="*50)
print("Starting Goodness Grid Application...")
print("="*50)
test_connection()
print("="*50 + "\n")


# HOME PAGE ROUTE
@app.route('/')
def home():
    """Homepage - shows different content if user is logged in"""
    return render_template('home.html')


# REGISTER ROUTE
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page - create new user account"""
    
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        phone = request.form.get('phone')
        role = request.form.get('role')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Check if email already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            return render_template('register.html', 
                                 error='Email already registered! Please login.')
        
        # Check if passwords match
        if password != confirm_password:
            return render_template('register.html', 
                                 error='Passwords do not match!')
        
        # Check password strength
        if len(password) < 6:
            return render_template('register.html', 
                                 error='Password must be at least 6 characters!')
        
        # Create user in database
        address = ""
        kwargs = {}
        if role == 'donor':
            kwargs['donor_type'] = 'individual'
        elif role == 'volunteer':
            kwargs['availability'] = 'Weekdays'
        
        user_id = create_user(
            name=fullname,
            email=email,
            password=password,
            phone=phone,
            address=address,
            role=role,
            **kwargs
        )
        
        if user_id:
            print(f"✅ User created successfully! ID: {user_id}")
            return render_template('login.html', 
                                 success='Account created successfully! Please login.')
        else:
            return render_template('register.html', 
                                 error='Registration failed. Please try again.')
    
    return render_template('register.html')


# LOGIN ROUTE
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - authenticate user"""
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = verify_user(email, password)
        
        if not user:
            return render_template('login.html', 
                                 error='Invalid email or password!')
        
        # Store user info in session
        session['user_id'] = user['user_id']
        session['email'] = user['email']
        session['fullname'] = user['name']
        session['role'] = user['role']
        
        print(f"✅ User logged in: {user['name']} ({user['role']})")
        
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')


# DASHBOARD ROUTE
@app.route('/dashboard')
def dashboard():
    """Shows personalized dashboard based on user role"""
    
    if 'email' not in session:
        return redirect(url_for('login'))
    
    # Prepare data based on role
    dashboard_data = {
        'my_donations_count': 0,
        'available_count': 0,
        'claimed_count': 0,
        'completed_count': 0,
        'total_donations': 0,
        'total_users': 0
    }
    
    # For donors: get their donation stats
    if session.get('role') == 'donor':
        donations = get_donations_by_donor(session['user_id'])
        dashboard_data['my_donations_count'] = len(donations)
        dashboard_data['available_count'] = len([d for d in donations if d['status'] == 'available'])
        dashboard_data['claimed_count'] = len([d for d in donations if d['status'] == 'claimed'])
        dashboard_data['completed_count'] = len([d for d in donations if d['status'] == 'completed'])

        # For volunteers: show pickup stats
    elif session.get('role') == 'volunteer':
        pending = get_pending_pickups()
        my_tasks = get_volunteer_assignments(session['user_id'])
        dashboard_data['pending_pickups'] = len(pending)
        dashboard_data['my_in_progress'] = len([t for t in my_tasks if t['status'] == 'in_progress'])
        dashboard_data['my_completed'] = len([t for t in my_tasks if t['status'] == 'completed'])
    

    elif session.get('role') in ['receiver', 'ngo']:
        all_donations = get_all_donations(status='available')
        claimed_donations = get_claimed_donations_by_ngo(session['user_id'])
        dashboard_data['total_donations'] = len(all_donations)
        dashboard_data['claimed_count'] = len(claimed_donations)
        dashboard_data['completed_count'] = len([d for d in claimed_donations if d['status'] == 'completed'])

    # For admin: show overall stats
    elif session.get('role') == 'admin':
        stats = get_platform_stats()
        dashboard_data.update(stats)
    
    return render_template('dashboard.html', **dashboard_data)

    


# POST DONATION ROUTE
@app.route('/post-donation', methods=['GET', 'POST'])
def post_donation():
    """Donation posting page for donors"""
    
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') != 'donor':
        return render_template('post_donation.html', 
                             error='Only donors can post donations!')
    
    if request.method == 'POST':
        donation_type = request.form.get('type')
        description = request.form.get('description')
        quantity = request.form.get('quantity')
        pickup_address = request.form.get('pickup_address')
        pickup_time = request.form.get('pickup_time') or None
        expiry_date = request.form.get('expiry_date') or None
        notes = request.form.get('notes')
        
        if not all([donation_type, description, quantity, pickup_address]):
            return render_template('post_donation.html', 
                                 error='Please fill all required fields!')
        
        donation_id = create_donation(
            donor_id=session['user_id'],
            donation_type=donation_type,
            description=description,
            quantity=quantity,
            pickup_address=pickup_address,
            pickup_time=pickup_time,
            expiry_date=expiry_date,
            notes=notes
        )
        
        if donation_id:
            return render_template('post_donation.html', 
                                 success='Donation posted successfully! NGOs can now see your donation.')
        else:
            return render_template('post_donation.html', 
                                 error='Failed to post donation. Please try again.')
    
    return render_template('post_donation.html')


# VIEW ALL DONATIONS (with search and filter)
@app.route('/donations')
def view_donations():
    """Show all available donations with search and filter"""
    
    if 'email' not in session:
        return redirect(url_for('login'))
    
    # Get filter parameters from URL
    search_query = request.args.get('search', '')
    donation_type = request.args.get('type', 'all')
    
    # Search/filter donations
    if search_query or donation_type != 'all':
        donations = search_donations(search_query=search_query, 
                                     donation_type=donation_type,
                                     status='available')
    else:
        donations = get_all_donations(status='available')
    
    return render_template('view_donations.html', 
                         donations=donations,
                         search_query=search_query,
                         selected_type=donation_type)


# MY DONATIONS
@app.route('/my-donations')
def my_donations():
    """Show donations posted by current user"""
    
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') != 'donor':
        return redirect(url_for('dashboard'))
    
    donations = get_donations_by_donor(session['user_id'])
    
    return render_template('my_donations.html', donations=donations)


# LOGOUT ROUTE
@app.route('/logout')
def logout():
    """Clear session and log user out"""
    username = session.get('fullname', 'User')
    session.clear()
    print(f"✅ {username} logged out")
    return render_template('login.html', 
                         success='You have been logged out successfully!')


# ABOUT PAGE
@app.route('/about')
def about():
    return render_template('about.html')


# DONATE PAGE - Redirects to post donation
@app.route('/donate')
def donate():
    if 'email' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('post_donation'))

# CLAIM DONATION ROUTE
@app.route('/claim-donation/<int:donation_id>', methods=['POST'])
def claim_donation_route(donation_id):
    """NGO claims a donation"""
    
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') not in ['receiver', 'ngo']:
        return redirect(url_for('view_donations'))
    
    success = claim_donation(donation_id, session['user_id'])
    
    if success:
        return redirect(url_for('view_donations'))
    else:
        return redirect(url_for('view_donations'))
    
# MY CLAIMS (for NGOs/receivers)
@app.route('/my-claims')
def my_claims():
    """Show donations claimed by current NGO"""
    
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') not in ['receiver', 'ngo']:
        return redirect(url_for('dashboard'))
    
    donations = get_claimed_donations_by_ngo(session['user_id'])
    
    return render_template('my_claims.html', donations=donations)

# VOLUNTEER DASHBOARD
@app.route('/volunteer-pickups')
def volunteer_pickups():
    """Show available pickups for volunteers"""
    
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') != 'volunteer':
        return redirect(url_for('dashboard'))
    
    # Get all pending pickups
    pending = get_pending_pickups()
    # Get volunteer's assigned tasks
    my_tasks = get_volunteer_assignments(session['user_id'])
    
    return render_template('volunteer_pickups.html', 
                         pending_pickups=pending, 
                         my_assignments=my_tasks)


# VOLUNTEER ACCEPTS PICKUP
@app.route('/accept-pickup/<int:transaction_id>', methods=['POST'])
def accept_pickup(transaction_id):
    """Volunteer accepts a pickup task"""
    
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') != 'volunteer':
        return redirect(url_for('volunteer_pickups'))
    
    success = assign_volunteer_to_transaction(transaction_id, session['user_id'])
    
    if success:
        return redirect(url_for('volunteer_pickups'))
    else:
        return redirect(url_for('volunteer_pickups'))


# COMPLETE DELIVERY
@app.route('/complete-delivery/<int:transaction_id>', methods=['POST'])
def complete_delivery(transaction_id):
    """Volunteer marks delivery as completed"""
    
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') != 'volunteer':
        return redirect(url_for('volunteer_pickups'))
    
    success = complete_transaction(transaction_id)
    
    if success:
        return redirect(url_for('volunteer_pickups'))
    else:
        return redirect(url_for('volunteer_pickups'))
    
# ADMIN ROUTES

# Admin - User Management
@app.route('/admin/users')
def admin_users():
    """Admin view all users"""
    
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    
    users = get_all_users()
    
    return render_template('admin_users.html', users=users)


# Admin - Verify NGO
@app.route('/admin/verify-ngo/<int:user_id>', methods=['POST'])
def verify_ngo_route(user_id):
    """Admin verifies an NGO"""
    
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') != 'admin':
        return redirect(url_for('admin_users'))
    
    success = verify_ngo(user_id)
    
    if success:
        return redirect(url_for('admin_users'))
    else:
        return redirect(url_for('admin_users'))


# Admin - View All Transactions
@app.route('/admin/transactions')
def admin_transactions():
    """Admin view all transactions"""
    
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    
    transactions = get_all_transactions_admin()
    
    return render_template('admin_transactions.html', transactions=transactions)

# Run the app
if __name__ == '__main__':
    app.run(debug=DEBUG, port=PORT)