# Import necessary modules
import csv
from io import StringIO, BytesIO
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, make_response
from database import (create_user, verify_user, get_user_by_email, test_connection,
                     create_donation, get_all_donations, get_donations_by_donor, 
                     claim_donation, get_claimed_donations_by_ngo,
                     get_pending_pickups, assign_volunteer_to_transaction,
                     get_volunteer_assignments, complete_transaction,
                     search_donations, get_all_users, get_platform_stats,
                     verify_ngo, get_all_transactions_admin,
                     update_user_profile, change_user_password, get_user_activity_stats,
                     get_user_by_id, get_donation_trends, get_donation_type_distribution,
                     get_completion_rate_trend, get_user_growth_data, get_top_donors,
                     get_all_donations_for_export, get_all_users_for_export,
                     get_all_transactions_for_export)
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
# REGISTER ROUTE with Enhanced Validation
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page with comprehensive validation"""
    
    if request.method == 'POST':
        try:
            fullname = request.form.get('fullname', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            role = request.form.get('role', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Validation checks
            errors = []
            
            # Check required fields
            if not all([fullname, email, phone, role, password, confirm_password]):
                errors.append('All fields are required!')
            
            # Name validation
            if fullname and len(fullname) < 3:
                errors.append('Name must be at least 3 characters long!')
            
            # Email validation
            if email:
                if not '@' in email or not '.' in email.split('@')[1]:
                    errors.append('Please enter a valid email address!')
                
                # Check if email exists
                existing_user = get_user_by_email(email)
                if existing_user:
                    errors.append('Email already registered! Please login.')
            
            # Phone validation
            if phone and not phone.isdigit():
                errors.append('Phone number must contain only digits!')
            if phone and len(phone) != 10:
                errors.append('Phone number must be exactly 10 digits!')
            
            # Role validation
            if role and role not in ['donor', 'receiver', 'volunteer', 'ngo']:
                errors.append('Invalid role selected!')
            
            # Password validation
            if password:
                if len(password) < 6:
                    errors.append('Password must be at least 6 characters!')
                if not any(c.isdigit() for c in password):
                    errors.append('Password must contain at least one number!')
            
            # Password match
            if password != confirm_password:
                errors.append('Passwords do not match!')
            
            # If there are errors, show them
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template('register.html')
            
            # Create user
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
                flash('Account created successfully! Please login.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Registration failed. Please try again.', 'danger')
                return render_template('register.html')
                
        except Exception as e:
            print(f"Registration error: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('register.html')
    
    return render_template('register.html')


# LOGIN ROUTE
# LOGIN ROUTE with Enhanced Validation
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with better error handling"""
    
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            # Validation
            if not email or not password:
                flash('Please enter both email and password!', 'warning')
                return render_template('login.html')
            
            # Verify user
            user = verify_user(email, password)
            
            if not user:
                flash('Invalid email or password! Please try again.', 'danger')
                return render_template('login.html')
            
            # Store user info in session
            session['user_id'] = user['user_id']
            session['email'] = user['email']
            session['fullname'] = user['name']
            session['role'] = user['role']
            
            print(f"✅ User logged in: {user['name']} ({user['role']})")
            
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            print(f"Login error: {e}")
            flash('An error occurred during login. Please try again.', 'danger')
            return render_template('login.html')
    
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
# POST DONATION ROUTE with Enhanced Validation
@app.route('/post-donation', methods=['GET', 'POST'])
def post_donation():
    """Donation posting with comprehensive validation"""
    
    if 'email' not in session:
        flash('Please login to post donations!', 'warning')
        return redirect(url_for('login'))
    
    if session.get('role') != 'donor':
        flash('Only donors can post donations!', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            donation_type = request.form.get('type', '').strip()
            description = request.form.get('description', '').strip()
            quantity = request.form.get('quantity', '').strip()
            pickup_address = request.form.get('pickup_address', '').strip()
            pickup_time = request.form.get('pickup_time') or None
            expiry_date = request.form.get('expiry_date') or None
            notes = request.form.get('notes', '').strip()
            
            # Validation
            errors = []
            
            if not donation_type:
                errors.append('Please select a donation type!')
            if not description or len(description) < 10:
                errors.append('Description must be at least 10 characters!')
            if not quantity:
                errors.append('Please specify quantity!')
            if not pickup_address or len(pickup_address) < 10:
                errors.append('Please provide a complete pickup address!')
            
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template('post_donation.html')
            
            # Create donation
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
                flash('Donation posted successfully! NGOs can now see your donation.', 'success')
                return redirect(url_for('my_donations'))
            else:
                flash('Failed to post donation. Please try again.', 'danger')
                return render_template('post_donation.html')
                
        except Exception as e:
            print(f"Error posting donation: {e}")
            flash('An error occurred. Please try again.', 'danger')
            return render_template('post_donation.html')
    
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

# ERROR HANDLERS

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all other exceptions"""
    print(f"Error occurred: {e}")
    return render_template('500.html'), 500

# PROFILE ROUTES

# View Profile
@app.route('/profile')
def profile():
    """View user profile"""
    
    if 'email' not in session:
        flash('Please login to view your profile!', 'warning')
        return redirect(url_for('login'))
    
    # Get full user details
    user = get_user_by_id(session['user_id'])
    
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get activity stats
    stats = get_user_activity_stats(session['user_id'], session['role'])
    
    return render_template('profile.html', user=user, stats=stats)


# Edit Profile
@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    """Edit user profile"""
    
    if 'email' not in session:
        flash('Please login to edit your profile!', 'warning')
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            
            # Validation
            errors = []
            
            if not name or len(name) < 3:
                errors.append('Name must be at least 3 characters!')
            
            if not phone or len(phone) != 10 or not phone.isdigit():
                errors.append('Phone number must be exactly 10 digits!')
            
            if not address or len(address) < 10:
                errors.append('Address must be at least 10 characters!')
            
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template('edit_profile.html', user=user)
            
            # Update profile
            success = update_user_profile(session['user_id'], name, phone, address)
            
            if success:
                # Update session
                session['fullname'] = name
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('profile'))
            else:
                flash('Failed to update profile. Please try again.', 'danger')
                return render_template('edit_profile.html', user=user)
                
        except Exception as e:
            print(f"Error editing profile: {e}")
            flash('An error occurred. Please try again.', 'danger')
            return render_template('edit_profile.html', user=user)
    
    return render_template('edit_profile.html', user=user)


# Change Password
@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """Change user password"""
    
    if 'email' not in session:
        flash('Please login to change password!', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Validation
            errors = []
            
            if not all([current_password, new_password, confirm_password]):
                errors.append('All fields are required!')
            
            # Verify current password
            user = verify_user(session['email'], current_password)
            if not user:
                errors.append('Current password is incorrect!')
            
            # New password validation
            if new_password:
                if len(new_password) < 6:
                    errors.append('New password must be at least 6 characters!')
                if not any(c.isdigit() for c in new_password):
                    errors.append('New password must contain at least one number!')
            
            # Password match
            if new_password != confirm_password:
                errors.append('New passwords do not match!')
            
            # Check if new password is same as current
            if current_password == new_password:
                errors.append('New password must be different from current password!')
            
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template('change_password.html')
            
            # Change password
            success = change_user_password(session['user_id'], new_password)
            
            if success:
                flash('Password changed successfully! Please login again.', 'success')
                session.clear()
                return redirect(url_for('login'))
            else:
                flash('Failed to change password. Please try again.', 'danger')
                return render_template('change_password.html')
                
        except Exception as e:
            print(f"Error changing password: {e}")
            flash('An error occurred. Please try again.', 'danger')
            return render_template('change_password.html')
    
    return render_template('change_password.html')

# ADMIN ANALYTICS ROUTE
@app.route('/admin/analytics')
def admin_analytics():
    """Admin analytics dashboard with charts"""
    
    if 'email' not in session:
        flash('Please login to access analytics!', 'warning')
        return redirect(url_for('login'))
    
    if session.get('role') != 'admin':
        flash('Only admins can access analytics!', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all analytics data
    stats = get_platform_stats()
    donation_trends = get_donation_trends()
    type_distribution = get_donation_type_distribution()
    completion_trends = get_completion_rate_trend()
    user_growth = get_user_growth_data()
    top_donors = get_top_donors(5)
    
    return render_template('admin_analytics.html',
                         stats=stats,
                         donation_trends=donation_trends,
                         type_distribution=type_distribution,
                         completion_trends=completion_trends,
                         user_growth=user_growth,
                         top_donors=top_donors)
 
# EXPORT ROUTES

# Export Users to CSV
@app.route('/admin/export/users')
def export_users():
    """Export all users to CSV"""
    
    if 'email' not in session or session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))
    
    try:
        users = get_all_users_for_export()
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['User ID', 'Name', 'Email', 'Phone', 'Address', 'Role', 'Verified', 'Registered Date'])
        
        # Write data
        for user in users:
            writer.writerow([
                user['user_id'],
                user['name'],
                user['email'],
                user['phone'] or 'N/A',
                user['address'] or 'N/A',
                user['role'],
                'Yes' if user['verified'] else 'No',
                user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        # Prepare response
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response.headers['Content-Type'] = 'text/csv'
        
        return response
        
    except Exception as e:
        print(f"Export error: {e}")
        flash('Failed to export users. Please try again.', 'danger')
        return redirect(url_for('admin_users'))


# Export Donations to CSV
@app.route('/admin/export/donations')
def export_donations():
    """Export all donations to CSV"""
    
    if 'email' not in session or session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))
    
    try:
        donations = get_all_donations_for_export()
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Donation ID', 'Type', 'Description', 'Quantity', 'Pickup Address', 
                        'Status', 'Donor Name', 'Donor Email', 'Donor Phone', 'Posted Date'])
        
        # Write data
        for donation in donations:
            writer.writerow([
                donation['donation_id'],
                donation['type'],
                donation['description'],
                donation['quantity'],
                donation['pickup_address'],
                donation['status'],
                donation['donor_name'],
                donation['donor_email'],
                donation['donor_phone'],
                donation['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=donations_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response.headers['Content-Type'] = 'text/csv'
        
        return response
        
    except Exception as e:
        print(f"Export error: {e}")
        flash('Failed to export donations. Please try again.', 'danger')
        return redirect(url_for('admin_analytics'))


# Export Transactions to CSV
@app.route('/admin/export/transactions')
def export_transactions():
    """Export all transactions to CSV"""
    
    if 'email' not in session or session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))
    
    try:
        transactions = get_all_transactions_for_export()
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Transaction ID', 'Donation Type', 'Description', 'Quantity',
                        'Donor', 'NGO', 'Volunteer', 'Status', 'Created Date', 'Completed Date'])
        
        # Write data
        for txn in transactions:
            writer.writerow([
                txn['transaction_id'],
                txn['donation_type'],
                txn['description'],
                txn['quantity'],
                txn['donor_name'],
                txn['ngo_name'],
                txn['volunteer_name'] or 'Not assigned',
                txn['status'],
                txn['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                txn['completed_at'].strftime('%Y-%m-%d %H:%M:%S') if txn['completed_at'] else 'N/A'
            ])
        
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=transactions_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response.headers['Content-Type'] = 'text/csv'
        
        return response
        
    except Exception as e:
        print(f"Export error: {e}")
        flash('Failed to export transactions. Please try again.', 'danger')
        return redirect(url_for('admin_transactions'))


# Export Platform Summary
@app.route('/admin/export/summary')
def export_summary():
    """Export platform summary report"""
    
    if 'email' not in session or session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))
    
    try:
        stats = get_platform_stats()
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write title
        writer.writerow(['GOODNESS GRID - PLATFORM SUMMARY REPORT'])
        writer.writerow([f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
        writer.writerow([])
        
        # Overall stats
        writer.writerow(['OVERALL STATISTICS'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Users', stats.get('total_users', 0)])
        writer.writerow(['Total Donations', stats.get('total_donations', 0)])
        writer.writerow(['Total Transactions', stats.get('total_transactions', 0)])
        writer.writerow(['Completion Rate', f"{stats.get('completion_rate', 0)}%"])
        writer.writerow([])
        
        # Users by role
        writer.writerow(['USERS BY ROLE'])
        writer.writerow(['Role', 'Count'])
        for role, count in stats.get('users_by_role', {}).items():
            writer.writerow([role.capitalize(), count])
        writer.writerow([])
        
        # Donations by status
        writer.writerow(['DONATIONS BY STATUS'])
        writer.writerow(['Status', 'Count'])
        for status, count in stats.get('donations_by_status', {}).items():
            writer.writerow([status.capitalize(), count])
        writer.writerow([])
        
        # Transactions by status
        writer.writerow(['TRANSACTIONS BY STATUS'])
        writer.writerow(['Status', 'Count'])
        for status, count in stats.get('transactions_by_status', {}).items():
            writer.writerow([status.capitalize(), count])
        
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=platform_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response.headers['Content-Type'] = 'text/csv'
        
        return response
        
    except Exception as e:
        print(f"Export error: {e}")
        flash('Failed to export summary. Please try again.', 'danger')
        return redirect(url_for('dashboard'))
    
   
# Run the app
if __name__ == '__main__':
    app.run(debug=DEBUG, port=PORT)