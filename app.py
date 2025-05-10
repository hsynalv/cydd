from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'gizli-anahtar-123')

# MongoDB bağlantısı
client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
db = client['user_info_system']
users_collection = db['users']
admin_collection = db['admin_users']

# Upload klasörü ayarları
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Klasörü oluştur
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    if 'photo' not in request.files:
        flash('Fotoğraf yüklenmedi')
        return redirect(url_for('index'))
    
    file = request.files['photo']
    if file.filename == '':
        flash('Fotoğraf seçilmedi')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        user_data = {
            'full_name': request.form['full_name'],
            'phone': request.form['phone'],
            'instagram': request.form.get('instagram', ''),
            'image_path': filename,
            'created_at': datetime.now()
        }
        
        users_collection.insert_one(user_data)
        flash('Bilgileriniz başarıyla kaydedildi!')
        return redirect(url_for('index'))
    
    flash('Geçersiz dosya formatı')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = admin_collection.find_one({'username': username})
        if admin and check_password_hash(admin['password'], password):
            session['logged_in'] = True
            return redirect(url_for('admin'))
        
        flash('Geçersiz kullanıcı adı veya şifre')
    return render_template('login.html')

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    users = list(users_collection.find().sort('created_at', -1))
    return render_template('admin.html', users=users)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Admin kullanıcısı yoksa oluştur
    if admin_collection.count_documents({}) == 0:
        admin_collection.insert_one({
            'username': 'admin',
            'password': generate_password_hash('admin123')
        })
    app.run(debug=True) 