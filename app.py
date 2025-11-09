# Import necessary modules
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Mail, Message
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, make_response, jsonify

from config import (SECRET_KEY, DEBUG, PORT, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, 
                   MAX_FILE_SIZE, MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, 
                   MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER, BASE_URL)
import csv
import os
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
                     get_all_transactions_for_export, verify_user_email, is_email_verified,
                     get_donation_by_id,get_recent_available_donations,get_average_rating_for_donor,add_feedback,get_feedback_for_donor)




# Create Flask app
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Configure upload folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Configure email
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER
app.config['BASE_URL'] = BASE_URL

# Initialize Mail
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def send_verification_email(user_email, user_name):
    """
    Send email verification link to new user
    """
    try:
        # Generate token
        token = serializer.dumps(user_email, salt='email-verification')
        
        # Create verification URL
        verify_url = f"{app.config['BASE_URL']}/verify-email/{token}"
        
        # Create email
        msg = Message(
            subject='Verify Your Goodness Grid Account',
            recipients=[user_email]
        )
        
        msg.html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #4caf50; text-align: center;">🌟 Welcome to Goodness Grid!</h2>
                
                <p>Hi <strong>{user_name}</strong>,</p>
                
                <p>Thank you for registering with Goodness Grid - A Network of Good Deeds!</p>
                
                <p>To activate your account and start making a difference, please verify your email address by clicking the button below:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verify_url}" style="background-color: #4caf50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                        ✓ Verify Email Address
                    </a>
                </div>
                
                <p style="color: #666; font-size: 14px;">Or copy and paste this link in your browser:</p>
                <p style="background: #f5f5f5; padding: 10px; border-radius: 5px; word-break: break-all; font-size: 12px;">
                    {verify_url}
                </p>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    <strong>Note:</strong> This verification link will expire in 24 hours.
                </p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p style="color: #999; font-size: 12px; text-align: center;">
                    If you didn't create an account with Goodness Grid, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        mail.send(msg)
        print(f"✅ Verification email sent to {user_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send verification email: {e}")
        return False


def send_notification_email(recipient_email, subject, body_html):
    """
    Generic function to send notification emails
    """
    try:
        msg = Message(
            subject=subject,
            recipients=[recipient_email]
        )
        msg.html = body_html
        
        mail.send(msg)
        print(f"✅ Email sent to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


def send_donation_claimed_email(donor_email, donor_name, donation_desc, ngo_name):
    """
    Notify donor when their donation is claimed
    """
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
            <h2 style="color: #4caf50;">🎉 Your Donation Has Been Claimed!</h2>
            
            <p>Hi <strong>{donor_name}</strong>,</p>
            
            <p>Great news! Your donation has been claimed by an NGO.</p>
            
            <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Donation:</strong> {donation_desc}</p>
                <p><strong>Claimed by:</strong> {ngo_name}</p>
            </div>
            
            <p>A volunteer will be assigned soon to arrange pickup. You'll receive another notification when the pickup is scheduled.</p>
            
            <p style="margin-top: 30px;">Thank you for your generosity! 💚</p>
            
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                - Team Goodness Grid
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_notification_email(donor_email, "Your Donation Has Been Claimed", body)


def send_pickup_assigned_email(volunteer_email, volunteer_name, donation_desc, donor_name, ngo_name):
    """
    Notify volunteer when assigned to a pickup
    """
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
            <h2 style="color: #ff9800;">🚚 New Pickup Assignment</h2>
            
            <p>Hi <strong>{volunteer_name}</strong>,</p>
            
            <p>You have been assigned a new pickup task!</p>
            
            <div style="background: #fff3e0; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Donation:</strong> {donation_desc}</p>
                <p><strong>Pickup from:</strong> {donor_name}</p>
                <p><strong>Deliver to:</strong> {ngo_name}</p>
            </div>
            
            <p>Please login to your dashboard to view full pickup details including addresses and contact information.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{app.config['BASE_URL']}/volunteer-pickups" style="background-color: #ff9800; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                    View Pickup Details
                </a>
            </div>
            
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                - Team Goodness Grid
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_notification_email(volunteer_email, "New Pickup Assignment", body)


def send_delivery_completed_email(donor_email, ngo_email, donor_name, ngo_name, donation_desc):
    """
    Notify both donor and NGO when delivery is completed
    """
    # Email to donor
    donor_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
            <h2 style="color: #4caf50;">✅ Donation Delivered Successfully!</h2>
            
            <p>Hi <strong>{donor_name}</strong>,</p>
            
            <p>Your donation has been successfully delivered!</p>
            
            <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Donation:</strong> {donation_desc}</p>
                <p><strong>Delivered to:</strong> {ngo_name}</p>
            </div>
            
            <p>Thank you for making a difference in someone's life! Your kindness helps build a better community. 💚</p>
            
            <p style="margin-top: 30px;">We hope to see more contributions from you!</p>
            
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                - Team Goodness Grid
            </p>
        </div>
    </body>
    </html>
    """
    
    # Email to NGO
    ngo_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
            <h2 style="color: #2196f3;">📦 Donation Received!</h2>
            
            <p>Hi <strong>{ngo_name}</strong>,</p>
            
            <p>The donation you claimed has been successfully delivered to you.</p>
            
            <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Donation:</strong> {donation_desc}</p>
                <p><strong>From:</strong> {donor_name}</p>
            </div>
            
            <p>We hope this donation helps you serve your community better!</p>
            
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                - Team Goodness Grid
            </p>
        </div>
    </body>
    </html>
    """
    
    send_notification_email(donor_email, "Donation Delivered Successfully", donor_body)
    send_notification_email(ngo_email, "Donation Received", ngo_body)


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

# REGISTER ROUTE with Email Verification
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page with email verification"""
    
    if request.method == 'POST':
        try:
            fullname = request.form.get('fullname', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            role = request.form.get('role', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Validation checks (keep existing validation)
            errors = []
            
            if not all([fullname, email, phone, role, password, confirm_password]):
                errors.append('All fields are required!')
            
            if fullname and len(fullname) < 3:
                errors.append('Name must be at least 3 characters long!')
            
            if email:
                if not '@' in email or not '.' in email.split('@')[1]:
                    errors.append('Please enter a valid email address!')
                
                existing_user = get_user_by_email(email)
                if existing_user:
                    errors.append('Email already registered! Please login.')
            
            if phone and not phone.isdigit():
                errors.append('Phone number must contain only digits!')
            if phone and len(phone) != 10:
                errors.append('Phone number must be exactly 10 digits!')
            
            if role and role not in ['donor', 'receiver', 'volunteer', 'ngo']:
                errors.append('Invalid role selected!')
            
            if password:
                if len(password) < 6:
                    errors.append('Password must be at least 6 characters!')
                if not any(c.isdigit() for c in password):
                    errors.append('Password must contain at least one number!')
            
            if password != confirm_password:
                errors.append('Passwords do not match!')
            
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
                
                # Send verification email
                email_sent = send_verification_email(email, fullname)
                
                if email_sent:
                    flash('Account created! Please check your email to verify your account before logging in.', 'success')
                else:
                    flash('Account created but verification email failed. Please contact support.', 'warning')
                
                return redirect(url_for('login'))
            else:
                flash('Registration failed. Please try again.', 'danger')
                return render_template('register.html')
                
        except Exception as e:
            print(f"Registration error: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('register.html')
    
    return render_template('register.html')


# LOGIN ROUTE with Email Verification Check
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with email verification check"""
    
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Please enter both email and password!', 'warning')
                return render_template('login.html')
            
            # Verify user credentials
            user = verify_user(email, password)
            
            if not user:
                flash('Invalid email or password! Please try again.', 'danger')
                return render_template('login.html')
            
            # Check if email is verified
            from database import is_email_verified
            if not is_email_verified(email):
                flash('Please verify your email before logging in. Check your inbox for the verification link.', 'warning')
                # Offer to resend verification
                return render_template('login.html', unverified_email=email)
            
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
    
    dashboard_data = {
        'my_donations_count': 0,
        'available_count': 0,
        'claimed_count': 0,
        'completed_count': 0,
        'total_donations': 0,
        'total_users': 0,
        'recent_donations': [],
        'avg_rating': 0,
        'feedback_list': [],
    }
    
    role = session.get('role')
    user_id = session.get('user_id')

    # DONOR DASHBOARD
    if role == 'donor':
        donations = get_donations_by_donor(user_id)
        dashboard_data['my_donations_count'] = len(donations)
        dashboard_data['available_count'] = len([d for d in donations if d['status'] == 'available'])
        dashboard_data['claimed_count'] = len([d for d in donations if d['status'] == 'claimed'])
        dashboard_data['completed_count'] = len([d for d in donations if d['status'] == 'completed'])
        dashboard_data['avg_rating'] = get_average_rating_for_donor(session['user_id'])
        dashboard_data['feedback_list'] = get_feedback_for_donor(user_id)
        # default for everyone


    # VOLUNTEER DASHBOARD
    elif role == 'volunteer':
        pending = get_pending_pickups()
        my_tasks = get_volunteer_assignments(user_id)
        dashboard_data['pending_pickups'] = len(pending)
        dashboard_data['my_in_progress'] = len([t for t in my_tasks if t['status'] == 'in_progress'])
        dashboard_data['my_completed'] = len([t for t in my_tasks if t['status'] == 'completed'])

    # RECEIVER / NGO DASHBOARD
    elif role in ['receiver', 'ngo']:
        all_donations = get_all_donations(status='available')
        claimed_donations = get_claimed_donations_by_ngo(user_id)
        dashboard_data['total_donations'] = len(all_donations)
        dashboard_data['claimed_count'] = len(claimed_donations)
        dashboard_data['completed_count'] = len([d for d in claimed_donations if d['status'] == 'completed'])
        dashboard_data['recent_donations'] = get_recent_available_donations(limit=6)

    # ADMIN DASHBOARD
    elif role == 'admin':
        stats = get_platform_stats()
        dashboard_data.update(stats)
    
    return render_template('dashboard.html', **dashboard_data)


    
from werkzeug.utils import secure_filename

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            image_file=request.files.get('image')
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
            
             # Validate image
            image_path = None
            if image_file and image_file.filename != '':
                if allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    unique_name = f"{session['user_id']}_{int(datetime.now().timestamp())}_{filename}"
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name).replace('\\','/')
                    image_file.save(image_path)
                    print(f"✅ Image uploaded to: {image_path}")
                else:
                    errors.append('Invalid image format! Allowed: png, jpg, jpeg, gif.')
            
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
                notes=notes,
                image_path=image_path
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


@app.route('/api/donation/<int:donation_id>')
def get_donation_details(donation_id):
    """Returns JSON data for a specific donation"""
    if 'email' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    donation = get_donation_by_id(donation_id)
    if not donation:
        return jsonify({'success': False, 'error': 'Donation not found'}), 404

    # Convert datetime to string
    if donation.get('created_at'):
        donation['created_at'] = donation['created_at'].strftime("%Y-%m-%d %H:%M:%S")

    return jsonify({'success': True, 'donation': donation})


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
# CLAIM DONATION ROUTE with Email Notification
@app.route('/claim-donation/<int:donation_id>', methods=['POST'])
def claim_donation_route(donation_id):
    """NGO claims a donation"""
    
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') not in ['receiver', 'ngo']:
        return redirect(url_for('view_donations'))
    
    # Get donation details before claiming
    donation = get_donation_by_id(donation_id)
    
    if donation:
        success = claim_donation(donation_id, session['user_id'])
        
        if success:
            # Send email notification to donor
            donor_user = get_user_by_id(donation['donor_id'])
            if donor_user and donor_user.get('email_verified'):
                send_donation_claimed_email(
                    donor_user['email'],
                    donor_user['name'],
                    donation['description'],
                    session['fullname']
                )
            
            flash('Donation claimed successfully!', 'success')
            return redirect(url_for('view_donations'))
    
    flash('Failed to claim donation.', 'danger')
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
# VOLUNTEER ACCEPTS PICKUP with Email Notification
@app.route('/accept-pickup/<int:transaction_id>', methods=['POST'])
def accept_pickup(transaction_id):
    """Volunteer accepts a pickup task"""
    
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') != 'volunteer':
        return redirect(url_for('volunteer_pickups'))
    
    # Get transaction details
    from database import get_user_by_id
    
    success = assign_volunteer_to_transaction(transaction_id, session['user_id'])
    
    if success:
        # Get full transaction details for email
        transactions = get_all_transactions_admin()
        txn = next((t for t in transactions if t['transaction_id'] == transaction_id), None)
        
        if txn:
            # Send email to volunteer (already logged in, but for records)
            volunteer_user = get_user_by_id(session['user_id'])
            if volunteer_user and volunteer_user.get('email_verified'):
                send_pickup_assigned_email(
                    volunteer_user['email'],
                    volunteer_user['name'],
                    txn['description'],
                    txn['donor_name'],
                    txn['ngo_name']
                )
        
        flash('Pickup task accepted!', 'success')
        return redirect(url_for('volunteer_pickups'))
    
    flash('Failed to accept pickup.', 'danger')
    return redirect(url_for('volunteer_pickups'))

# COMPLETE DELIVERY
# COMPLETE DELIVERY with Email Notifications
@app.route('/complete-delivery/<int:transaction_id>', methods=['POST'])
def complete_delivery(transaction_id):
    """Volunteer marks delivery as completed"""
    
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') != 'volunteer':
        return redirect(url_for('volunteer_pickups'))
    
    # Get transaction details before completing
    transactions = get_all_transactions_admin()
    txn = next((t for t in transactions if t['transaction_id'] == transaction_id), None)
    
    success = complete_transaction(transaction_id)
    
    if success and txn:
        # Get donor and NGO details
        donation = get_donation_by_id(txn['donation_id'])
        if donation:
            donor_user = get_user_by_id(donation['donor_id'])
            ngo_user = get_user_by_id(txn['ngo_id'])
            
            # Send completion emails to both
            if donor_user and donor_user.get('email_verified') and ngo_user and ngo_user.get('email_verified'):
                send_delivery_completed_email(
                    donor_user['email'],
                    ngo_user['email'],
                    donor_user['name'],
                    ngo_user['name'],
                    txn['description']
                )
        
        flash('Delivery marked as completed!', 'success')
        return redirect(url_for('volunteer_pickups'))
    
    flash('Failed to complete delivery.', 'danger')
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
    
# EMAIL VERIFICATION ROUTES

@app.route('/verify-email/<token>')
def verify_email(token):
    """Verify user email from token"""
    try:
        # Decode token (expires in 24 hours)
        email = serializer.loads(token, salt='email-verification', max_age=86400)
        
        # Verify email in database
        from database import verify_user_email
        success = verify_user_email(email)
        
        if success:
            flash('Email verified successfully! You can now login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email verification failed. Please try again.', 'danger')
            return redirect(url_for('login'))
            
    except SignatureExpired:
        flash('Verification link has expired. Please register again.', 'danger')
        return redirect(url_for('register'))
    except BadSignature:
        flash('Invalid verification link.', 'danger')
        return redirect(url_for('register'))
    except Exception as e:
        print(f"Verification error: {e}")
        flash('Verification failed. Please contact support.', 'danger')
        return redirect(url_for('login'))


@app.route('/resend-verification')
def resend_verification():
    """Resend verification email"""
    email = request.args.get('email')
    
    if not email:
        flash('Email address required.', 'danger')
        return redirect(url_for('login'))
    
    user = get_user_by_email(email)
    
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))
    
    if user['email_verified']:
        flash('Email already verified. Please login.', 'info')
        return redirect(url_for('login'))
    
    # Send verification email
    email_sent = send_verification_email(email, user['name'])
    
    if email_sent:
        flash('Verification email sent! Please check your inbox.', 'success')
    else:
        flash('Failed to send verification email. Please try again later.', 'danger')
    
    return redirect(url_for('login'))
  
@app.route('/feedback/<int:donation_id>', methods=['POST'])
def submit_feedback(donation_id):
    """Receiver submits feedback for a donation"""
    if 'email' not in session:
        return redirect(url_for('login'))

    rating = request.form.get('rating')
    comments = request.form.get('comments', '').strip()

    if not rating or not rating.isdigit():
        flash("Please select a valid star rating before submitting!", "danger")
        return redirect(url_for('my_claims'))

    rating = int(rating)

    # Get donor_id from the donation
    donation = get_donation_by_id(donation_id)
    if not donation:
        flash("Donation not found!", "danger")
        return redirect(url_for('my_claims'))

    donor_id = donation['donor_id']
    receiver_id = session['user_id']

    result = add_feedback(donation_id, donor_id, receiver_id, rating, comments)

    if result == "exists":
        flash("⚠️ You’ve already submitted feedback for this donation!", "warning")
    elif result is True:
        flash("✅ Feedback submitted successfully!", "success")
    else:
        flash("❌ Error submitting feedback. Please try again.", "danger")

    return redirect(url_for('my_claims'))


  
 
# Run the app
if __name__ == '__main__':
    app.run(debug=DEBUG, port=PORT)