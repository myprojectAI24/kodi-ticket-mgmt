# controllers.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from functools import wraps
from models import db, Admin, Profile, Ticket
from datetime import datetime
import subprocess
import os

main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
profile_bp = Blueprint('profile', __name__, url_prefix='/profiles')
ticket_bp = Blueprint('ticket', __name__, url_prefix='/tickets')
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Decorator for login required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Main Routes
@main_bp.route('/')
def index():
    if 'admin_id' in session:
        return redirect(url_for('profile.list_profiles'))
    return redirect(url_for('auth.login'))

# Auth Routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'admin_id' in session:
        return redirect(url_for('profile.list_profiles'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['username'] = admin.username
            flash('Login successful!', 'success')
            return redirect(url_for('profile.list_profiles'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

# Profile Routes
@profile_bp.route('/')
@login_required
def list_profiles():
    profiles = Profile.query.order_by(Profile.created_at.desc()).all()
    return render_template('profiles.html', profiles=profiles)

@profile_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        
        if not name:
            flash('Profile name is required.', 'danger')
            return render_template('profile_form.html')
        
        # Check if profile already exists
        if Profile.query.filter_by(name=name).first():
            flash('Profile with this name already exists.', 'danger')
            return render_template('profile_form.html')
        
        profile = Profile(name=name)
        db.session.add(profile)
        db.session.commit()
        
        flash(f'Profile "{name}" created successfully!', 'success')
        return redirect(url_for('profile.view_profile', id=profile.id))
    
    return render_template('profile_form.html')

@profile_bp.route('/view/<int:id>')
@login_required
def view_profile(id):
    profile = Profile.query.get_or_404(id)
    return render_template('profile_detail.html', profile=profile)

@profile_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_profile(id):
    profile = Profile.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        
        if not name:
            flash('Profile name is required.', 'danger')
            return render_template('profile_form.html', profile=profile)
        
        # Check if another profile with this name exists
        existing = Profile.query.filter_by(name=name).first()
        if existing and existing.id != profile.id:
            flash('Profile with this name already exists.', 'danger')
            return render_template('profile_form.html', profile=profile)
        
        profile.name = name
        db.session.commit()
        
        flash(f'Profile "{name}" updated successfully!', 'success')
        return redirect(url_for('profile.view_profile', id=profile.id))
    
    return render_template('profile_form.html', profile=profile)

@profile_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_profile(id):
    profile = Profile.query.get_or_404(id)
    name = profile.name
    db.session.delete(profile)
    db.session.commit()
    flash(f'Profile "{name}" and all its tickets deleted successfully!', 'success')
    return redirect(url_for('profile.list_profiles'))

# Ticket Routes
@ticket_bp.route('/create/<int:profile_id>', methods=['GET', 'POST'])
@login_required
def create_ticket(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    
    if request.method == 'POST':
        length = request.form.get('length')
        
        if not length:
            flash('Length is required.', 'danger')
            return render_template('ticket_form.html', profile=profile)
        
        try:
            length = int(length)
            if length <= 0:
                raise ValueError
        except ValueError:
            flash('Length must be a positive number.', 'danger')
            return render_template('ticket_form.html', profile=profile)
        
        # Generate unique PIN
        try:
            lock_code = Ticket.generate_unique_pin()
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('ticket_form.html', profile=profile)
        
        # Create ticket
        ticket = Ticket(
            profile_id=profile.id,
            lock_code=lock_code,
            length=length,
            is_active=True
        )
        db.session.add(ticket)
        db.session.commit()
        
        # Execute SSH script
        success = execute_kodi_script(profile.name, lock_code)
        
        if success:
            flash(f'Ticket created with PIN {lock_code} and script executed successfully!', 'success')
        else:
            flash(f'Ticket created with PIN {lock_code}, but script execution failed. Check logs.', 'warning')
        
        return redirect(url_for('profile.view_profile', id=profile.id))
    
    return render_template('ticket_form.html', profile=profile)

@ticket_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    profile_id = ticket.profile_id
    db.session.delete(ticket)
    db.session.commit()
    flash('Ticket deleted successfully!', 'success')
    return redirect(url_for('profile.view_profile', id=profile_id))

# API Routes
@api_bp.route('/login', methods=['POST'])
def register_login():
    """
    API endpoint for Kodi to register when a profile logs in
    Expected JSON: {"lock_code": "1234"}
    """
    data = request.get_json()
    
    if not data or 'lock_code' not in data:
        return jsonify({'error': 'lock_code is required'}), 400
    
    lock_code = data['lock_code']
    
    # Find the ticket
    ticket = Ticket.query.filter_by(lock_code=lock_code, is_active=True).first()
    
    if not ticket:
        return jsonify({'error': 'Invalid or inactive ticket'}), 404
    
    # Mark ticket as used
    ticket.is_active = False
    ticket.used_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Login registered successfully',
        'profile': ticket.profile.name,
        'length': ticket.length,
        'used_at': ticket.used_at.strftime('%Y-%m-%d %H:%M:%S')
    }), 200

@api_bp.route('/ticket/<lock_code>', methods=['GET'])
def get_ticket_info(lock_code):
    """
    API endpoint to get ticket information
    """
    ticket = Ticket.query.filter_by(lock_code=lock_code).first()
    
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    
    return jsonify(ticket.to_dict()), 200

# Helper function
def execute_kodi_script(profile_name, pin):
    """
    Execute the SSH script to set password on Kodi
    For now, just logs to a file
    """
    try:
        # Ensure log directory exists
        log_dir = '/app/log'
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'exec.log')
        
        # For now, just write to log file
        with open(log_file, 'a') as f:
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] execute-on-kodi_set-passwd-per-profile.sh {profile_name}:{pin}\n")
        
        # TODO: Uncomment this when ready to execute actual SSH script
        # script_path = '/app/scripts/execute-on-kodi_set-passwd-per-profile.sh'
        # result = subprocess.run(
        #     [script_path, f"{profile_name}:{pin}"],
        #     capture_output=True,
        #     text=True,
        #     timeout=30
        # )
        # return result.returncode == 0
        
        return True
        
    except Exception as e:
        print(f"Error executing script: {e}")
        return False