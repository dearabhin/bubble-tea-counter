from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import sqlite3
from datetime import datetime
from bubble_analyzer import count_bubbles
import secrets
import numpy as np
from datetime import datetime  # Make sure this import is present

app = Flask(__name__)

# A strong secret key is important for session management (used by flash messages)
app.secret_key = secrets.token_hex(16)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --- Database Functions ---

def get_db_connection():
    """Establishes a connection to the database."""
    conn = sqlite3.connect('tea.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema if it doesn't exist."""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            bubble_count INTEGER NOT NULL,
            image_path TEXT NOT NULL,
            steps_path TEXT NOT NULL,
            final_path TEXT NOT NULL,
            submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


# --- Template Filters ---

@app.template_filter('format_date')
def format_date(date_str):
    """Custom Jinja filter to format dates nicely."""
    try:
        date_obj = datetime.strptime(
            date_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
        return date_obj.strftime('%b %d, %Y')
    except (ValueError, TypeError):
        return date_str


@app.context_processor
def inject_current_year():
    """Injects the current year into all templates."""
    return {'current_year': datetime.utcnow().year}

# --- Helper Functions ---


def allowed_file(filename):
    """Checks if a filename has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Routes ---

@app.route('/')
def home():
    """Renders the new landing page."""
    return render_template('home.html')


@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """Handles image upload, analysis, and displays results."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Please enter your name.', 'error')
            return redirect(url_for('analyze'))

        if 'file' not in request.files or not request.files['file'].filename:
            flash('No image file selected.', 'error')
            return redirect(url_for('analyze'))

        file = request.files['file']

        if file and allowed_file(file.filename):
            try:
                # Save uploaded file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = secure_filename(f"{timestamp}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                # Process the image
                num_bubbles, steps_path, final_path = count_bubbles(filepath)

                # Get relative paths for web URLs (use forward slashes)
                image_rel_path = os.path.relpath(
                    filepath, 'static').replace('\\', '/')
                steps_rel_path = os.path.relpath(
                    steps_path, 'static').replace('\\', '/')
                final_rel_path = os.path.relpath(
                    final_path, 'static').replace('\\', '/')

                # Save to database
                conn = get_db_connection()
                conn.execute('''
                    INSERT INTO submissions (name, bubble_count, image_path, steps_path, final_path)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, num_bubbles, image_rel_path, steps_rel_path, final_rel_path))
                conn.commit()
                conn.close()

                flash(
                    f'Success! We found {num_bubbles} bubbles in your tea.', 'success')

                # Create a results dictionary to pass to the template
                results = {
                    "bubble_count": num_bubbles,
                    "steps_path": steps_rel_path,
                    "final_path": final_rel_path,
                    "name": name
                }
                # Re-render the same page with the results
                return render_template('analyze.html', results=results)

            except Exception as e:
                app.logger.error(f"Error processing image: {e}")
                flash(f'An error occurred during analysis: {e}', 'error')
                return redirect(url_for('analyze'))
        else:
            flash('Invalid file type. Please upload a PNG, JPG, or JPEG image.', 'error')
            return redirect(url_for('analyze'))

    # For GET requests
    return render_template('analyze.html', results=None)


@app.route('/dashboard')
def dashboard():
    """Displays the leaderboard and key statistics."""
    conn = get_db_connection()

    # Get top 10 leaderboard entries
    leaderboard = conn.execute('''
        SELECT name, bubble_count, final_path, submission_date 
        FROM submissions 
        ORDER BY bubble_count DESC, submission_date DESC
        LIMIT 10
    ''').fetchall()

    # Get statistics
    stats = conn.execute(
        'SELECT COUNT(id), AVG(bubble_count), MAX(bubble_count) FROM submissions').fetchone()

    conn.close()

    dashboard_stats = {
        'total_submissions': stats[0] or 0,
        'avg_bubbles': round(stats[1] or 0),
        'max_bubbles': stats[2] or 0
    }

    return render_template('dashboard.html', leaderboard=leaderboard, stats=dashboard_stats)


@app.route('/how-it-works')
def how_it_works():
    """Renders the flowchart page that explains the project workflow."""
    # This route just needs to render the HTML file you already created.
    # The content from your flowchart.html will be moved into a new template.
    return render_template('how_it_works.html')


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
