"""
Database Helper Functions
Handles all MySQL database operations
"""

import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from config import DB_CONFIG


def get_db_connection():
    """
    Create and return a database connection
    This is like opening a door to your database
    """
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def create_user(name, email, password, phone, address, role, **kwargs):
    """
    Create a new user in the database
    
    Parameters:
    - name: User's full name
    - email: Email address (must be unique)
    - password: Plain text password (will be hashed)
    - phone: Phone number
    - address: User's address
    - role: 'donor', 'ngo', 'volunteer', or 'admin'
    - **kwargs: Additional role-specific fields
    
    Returns:
    - user_id if successful, None if failed
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        
        # Hash the password for security
        # generate_password_hash creates a secure, one-way encrypted password
        hashed_password = generate_password_hash(password)
        
        # Build the INSERT query
        query = """
        INSERT INTO Users (name, email, password, phone, address, role, 
                          donor_type, company_name, gst_no, 
                          ngo_registration_no, ngo_type, 
                          availability, vehicle_details)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            name, email, hashed_password, phone, address, role,
            kwargs.get('donor_type'),
            kwargs.get('company_name'),
            kwargs.get('gst_no'),
            kwargs.get('ngo_registration_no'),
            kwargs.get('ngo_type'),
            kwargs.get('availability'),
            kwargs.get('vehicle_details')
        )
        
        cursor.execute(query, values)
        connection.commit()
        
        # Get the ID of the newly created user
        user_id = cursor.lastrowid
        
        cursor.close()
        connection.close()
        
        return user_id
        
    except Error as e:
        print(f"Error creating user: {e}")
        if connection:
            connection.close()
        return None


def verify_user(email, password):
    """
    Check if email and password are correct
    
    Returns:
    - User data dictionary if valid, None if invalid
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)  # Returns results as dictionary
        
        query = "SELECT * FROM Users WHERE email = %s"
        cursor.execute(query, (email,))
        
        user = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        # Check if user exists and password matches
        if user and check_password_hash(user['password'], password):
            return user
        
        return None
        
    except Error as e:
        print(f"Error verifying user: {e}")
        if connection:
            connection.close()
        return None


def get_user_by_email(email):
    """
    Get user information by email
    
    Returns:
    - User dictionary if found, None if not found
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM Users WHERE email = %s"
        cursor.execute(query, (email,))
        
        user = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return user
        
    except Error as e:
        print(f"Error fetching user: {e}")
        if connection:
            connection.close()
        return None


def get_user_by_id(user_id):
    """
    Get user information by ID
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM Users WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        
        user = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return user
        
    except Error as e:
        print(f"Error fetching user: {e}")
        if connection:
            connection.close()
        return None


def test_connection():
    """
    Test if database connection works
    Returns True if successful, False otherwise
    """
    connection = get_db_connection()
    if connection and connection.is_connected():
        db_info = connection.get_server_info()
        print(f"✅ Successfully connected to MySQL Server version {db_info}")
        connection.close()
        return True
    else:
        print("❌ Failed to connect to MySQL")
        return False


def create_donation(donor_id, donation_type, description, quantity, 
                   pickup_address, pickup_time=None, expiry_date=None, notes=None):
    """
    Create a new donation in the database
    
    Parameters:
    - donor_id: ID of the user posting the donation
    - donation_type: Type of donation (food, clothes, etc.)
    - description: Detailed description
    - quantity: Quantity with unit
    - pickup_address: Where to pick up from
    - pickup_time: When it's available (optional)
    - expiry_date: Expiry date for food/medicine (optional)
    - notes: Additional notes (optional)
    
    Returns:
    - donation_id if successful, None if failed
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        
        query = """
        INSERT INTO Donations 
        (donor_id, type, description, quantity, pickup_address, 
         pickup_time, expiry_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'available')
        """
        
        values = (
            donor_id, donation_type, description, quantity, 
            pickup_address, pickup_time, expiry_date
        )
        
        cursor.execute(query, values)
        connection.commit()
        
        donation_id = cursor.lastrowid
        
        cursor.close()
        connection.close()
        
        print(f"✅ Donation created! ID: {donation_id}")
        return donation_id
        
    except Error as e:
        print(f"Error creating donation: {e}")
        if connection:
            connection.close()
        return None


def get_all_donations(status='available'):
    """
    Get all donations from database
    
    Parameters:
    - status: Filter by status (default: 'available')
    
    Returns:
    - List of donation dictionaries
    """
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Join with Users table to get donor name
        query = """
        SELECT d.*, u.name as donor_name, u.phone as donor_phone
        FROM Donations d
        JOIN Users u ON d.donor_id = u.user_id
        WHERE d.status = %s
        ORDER BY d.created_at DESC
        """
        
        cursor.execute(query, (status,))
        donations = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return donations
        
    except Error as e:
        print(f"Error fetching donations: {e}")
        if connection:
            connection.close()
        return []


def get_donations_by_donor(donor_id):
    """
    Get all donations posted by a specific donor
    
    Returns:
    - List of donation dictionaries
    """
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT * FROM Donations
        WHERE donor_id = %s
        ORDER BY created_at DESC
        """
        
        cursor.execute(query, (donor_id,))
        donations = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return donations
        
    except Error as e:
        print(f"Error fetching donor donations: {e}")
        if connection:
            connection.close()
        return []


def get_donation_by_id(donation_id):
    """
    Get a specific donation by ID
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT d.*, u.name as donor_name, u.email as donor_email, u.phone as donor_phone
        FROM Donations d
        JOIN Users u ON d.donor_id = u.user_id
        WHERE d.donation_id = %s
        """
        
        cursor.execute(query, (donation_id,))
        donation = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return donation
        
    except Error as e:
        print(f"Error fetching donation: {e}")
        if connection:
            connection.close()
        return None

def claim_donation(donation_id, ngo_id):
    """NGO claims a donation"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        update_query = "UPDATE Donations SET status = 'claimed' WHERE donation_id = %s AND status = 'available'"
        cursor.execute(update_query, (donation_id,))
        
        transaction_query = "INSERT INTO Transactions (donation_id, ngo_id, status) VALUES (%s, %s, 'pending')"
        cursor.execute(transaction_query, (donation_id, ngo_id))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"✅ Donation {donation_id} claimed by NGO {ngo_id}")
        return True
        
    except Error as e:
        print(f"Error claiming donation: {e}")
        if connection:
            connection.close()
        return False
    
def get_claimed_donations_by_ngo(ngo_id):
    """
    Get donations claimed by a specific NGO
    """
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT d.*, t.transaction_id, t.status as transaction_status, u.name as donor_name
        FROM Donations d
        JOIN Transactions t ON d.donation_id = t.donation_id
        JOIN Users u ON d.donor_id = u.user_id
        WHERE t.ngo_id = %s
        ORDER BY t.created_at DESC
        """
        
        cursor.execute(query, (ngo_id,))
        donations = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return donations
        
    except Error as e:
        print(f"Error fetching claimed donations: {e}")
        if connection:
            connection.close()
        return []
    
def get_pending_pickups():
    """
    Get all transactions that need volunteer assignment
    Status: pending (not yet assigned to volunteer)
    """
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT t.*, d.type, d.description, d.quantity, d.pickup_address,
               donor.name as donor_name, donor.phone as donor_phone,
               ngo.name as ngo_name, ngo.phone as ngo_phone
        FROM Transactions t
        JOIN Donations d ON t.donation_id = d.donation_id
        JOIN Users donor ON d.donor_id = donor.user_id
        JOIN Users ngo ON t.ngo_id = ngo.user_id
        WHERE t.status = 'pending' AND t.volunteer_id IS NULL
        ORDER BY t.created_at DESC
        """
        
        cursor.execute(query)
        pickups = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return pickups
        
    except Error as e:
        print(f"Error fetching pending pickups: {e}")
        if connection:
            connection.close()
        return []


def assign_volunteer_to_transaction(transaction_id, volunteer_id):
    """
    Assign a volunteer to a transaction
    Updates status to 'in_progress'
    """
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        query = """
        UPDATE Transactions 
        SET volunteer_id = %s, status = 'in_progress'
        WHERE transaction_id = %s
        """
        
        cursor.execute(query, (volunteer_id, transaction_id))
        connection.commit()
        
        cursor.close()
        connection.close()
        
        print(f"✅ Volunteer {volunteer_id} assigned to transaction {transaction_id}")
        return True
        
    except Error as e:
        print(f"Error assigning volunteer: {e}")
        if connection:
            connection.close()
        return False


def get_volunteer_assignments(volunteer_id):
    """
    Get all assignments for a specific volunteer
    """
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT t.*, d.type, d.description, d.quantity, d.pickup_address,
               d.pickup_time, donor.name as donor_name, donor.phone as donor_phone,
               donor.address as donor_address, ngo.name as ngo_name, 
               ngo.phone as ngo_phone, ngo.address as ngo_address
        FROM Transactions t
        JOIN Donations d ON t.donation_id = d.donation_id
        JOIN Users donor ON d.donor_id = donor.user_id
        JOIN Users ngo ON t.ngo_id = ngo.user_id
        WHERE t.volunteer_id = %s
        ORDER BY t.created_at DESC
        """
        
        cursor.execute(query, (volunteer_id,))
        assignments = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return assignments
        
    except Error as e:
        print(f"Error fetching volunteer assignments: {e}")
        if connection:
            connection.close()
        return []


def complete_transaction(transaction_id):
    """
    Mark a transaction as completed
    Updates both transaction and donation status
    """
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Update transaction status
        query1 = """
        UPDATE Transactions 
        SET status = 'completed', completed_at = NOW()
        WHERE transaction_id = %s
        """
        cursor.execute(query1, (transaction_id,))
        
        # Update donation status
        query2 = """
        UPDATE Donations d
        JOIN Transactions t ON d.donation_id = t.donation_id
        SET d.status = 'completed'
        WHERE t.transaction_id = %s
        """
        cursor.execute(query2, (transaction_id,))
        
        connection.commit()
        
        cursor.close()
        connection.close()
        
        print(f"✅ Transaction {transaction_id} completed")
        return True
        
    except Error as e:
        print(f"Error completing transaction: {e}")
        if connection:
            connection.close()
        return False

def search_donations(search_query=None, donation_type=None, status='available'):
    """
    Search and filter donations
    
    Parameters:
    - search_query: Keyword to search in description
    - donation_type: Filter by type (food, clothes, etc.)
    - status: Filter by status (default: available)
    """
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Build dynamic query
        query = """
        SELECT d.*, u.name as donor_name, u.phone as donor_phone
        FROM Donations d
        JOIN Users u ON d.donor_id = u.user_id
        WHERE d.status = %s
        """
        params = [status]
        
        # Add search condition
        if search_query:
            query += " AND (d.description LIKE %s OR d.quantity LIKE %s)"
            search_term = f"%{search_query}%"
            params.extend([search_term, search_term])
        
        # Add type filter
        if donation_type and donation_type != 'all':
            query += " AND d.type = %s"
            params.append(donation_type)
        
        query += " ORDER BY d.created_at DESC"
        
        cursor.execute(query, tuple(params))
        donations = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return donations
        
    except Error as e:
        print(f"Error searching donations: {e}")
        if connection:
            connection.close()
        return []

def get_all_users():
    """Get all users for admin panel"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT user_id, name, email, phone, role, verified, created_at
        FROM Users
        ORDER BY created_at DESC
        """
        
        cursor.execute(query)
        users = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return users
        
    except Error as e:
        print(f"Error fetching users: {e}")
        if connection:
            connection.close()
        return []


def get_platform_stats():
    """Get overall platform statistics"""
    connection = get_db_connection()
    if not connection:
        return {}
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        stats = {}
        
        # Total users by role
        cursor.execute("SELECT role, COUNT(*) as count FROM Users GROUP BY role")
        role_counts = cursor.fetchall()
        stats['users_by_role'] = {row['role']: row['count'] for row in role_counts}
        stats['total_users'] = sum(stats['users_by_role'].values())
        
        # Total donations by status
        cursor.execute("SELECT status, COUNT(*) as count FROM Donations GROUP BY status")
        donation_counts = cursor.fetchall()
        stats['donations_by_status'] = {row['status']: row['count'] for row in donation_counts}
        stats['total_donations'] = sum(stats['donations_by_status'].values())
        
        # Total transactions by status
        cursor.execute("SELECT status, COUNT(*) as count FROM Transactions GROUP BY status")
        transaction_counts = cursor.fetchall()
        stats['transactions_by_status'] = {row['status']: row['count'] for row in transaction_counts}
        stats['total_transactions'] = sum(stats['transactions_by_status'].values())
        
        # Completion rate
        if stats['total_transactions'] > 0:
            completed = stats['transactions_by_status'].get('completed', 0)
            stats['completion_rate'] = round((completed / stats['total_transactions']) * 100, 1)
        else:
            stats['completion_rate'] = 0
        
        cursor.close()
        connection.close()
        
        return stats
        
    except Error as e:
        print(f"Error fetching stats: {e}")
        if connection:
            connection.close()
        return {}


def verify_ngo(user_id):
    """Admin verifies an NGO"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        query = "UPDATE Users SET verified = TRUE WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        connection.commit()
        
        cursor.close()
        connection.close()
        
        print(f"✅ User {user_id} verified")
        return True
        
    except Error as e:
        print(f"Error verifying user: {e}")
        if connection:
            connection.close()
        return False


def get_all_transactions_admin():
    """Get all transactions for admin view"""
    connection = get_db_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT t.*, d.type, d.description, 
               donor.name as donor_name, ngo.name as ngo_name, 
               vol.name as volunteer_name
        FROM Transactions t
        JOIN Donations d ON t.donation_id = d.donation_id
        JOIN Users donor ON d.donor_id = donor.user_id
        JOIN Users ngo ON t.ngo_id = ngo.user_id
        LEFT JOIN Users vol ON t.volunteer_id = vol.user_id
        ORDER BY t.created_at DESC
        """
        
        cursor.execute(query)
        transactions = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return transactions
        
    except Error as e:
        print(f"Error fetching transactions: {e}")
        if connection:
            connection.close()
        return []
    
# Test the connection when this file is run directly
if __name__ == "__main__":
    print("Testing database connection...")
    test_connection()