import os
import sys
from flask import Flask, send_from_directory, session
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import db, ChatLog
from src.routes import auth_bp, chatbot_bp, user_bp, admin_bp
from src.utils.scheduler import start_scheduler

def create_app():
    app = Flask(__name__, static_folder='static')

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'

    # Database configuration
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        # Use SQLite with absolute path
        db_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
        database_url = f'sqlite:///{db_path}'
    # Handle Render's postgres:// vs postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    CORS(app, supports_credentials=True)
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    # Create database tables
    with app.app_context():
        # Ensure database directory exists for SQLite
        if 'sqlite' in database_url:
            db_dir = os.path.join(os.path.dirname(__file__), 'database')
            os.makedirs(db_dir, exist_ok=True)
        db.create_all()
        print("[LOG] Database tables created/verified")

    # Start background scheduler
    start_scheduler(app, db, ChatLog)

    # Static file routes
    @app.route('/')
    def serve_index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        # Try to serve the file directly
        if os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        # Fallback to index.html for SPA routing
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/robots.txt')
    def robots():
        return send_from_directory(app.static_folder, 'robots.txt')

    @app.route('/sitemap.xml')
    def sitemap():
        return send_from_directory(app.static_folder, 'sitemap.xml')

    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'app': 'Mormon Express'}, 200

    return app


# Create the app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') != 'production'
    print(f"[LOG] Starting Mormon Express on port {port}")
    print(f"[LOG] Debug mode: {debug}")
    app.run(host='0.0.0.0', port=port, debug=debug)
