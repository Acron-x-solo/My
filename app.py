from flask import Flask, jsonify, request, render_template, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_migrate import Migrate
import os
from pathlib import Path
from models import db, User, Post, Comment, Like, Follow, Friendship, PrivateMessage
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from werkzeug.utils import secure_filename
from api import api

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
app.config['UPLOAD_FOLDER'] = 'static/uploads/avatars'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Создаем папку для загрузки аватаров, если она не существует
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Инициализация расширений
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.remember_cookie_duration = timedelta(days=30)

# Регистрация API
app.register_blueprint(api, url_prefix='/api')

# Создаем базу данных, если она не существует
with app.app_context():
    db.create_all()
    print("База данных инициализирована!")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    # Получаем сначала закрепленные посты
    pinned_posts = Post.query.filter_by(is_pinned=True).order_by(Post.created_at.desc()).all()
    # Затем получаем обычные посты
    regular_posts = Post.query.filter_by(is_pinned=False).order_by(Post.created_at.desc()).all()
    # Объединяем посты
    posts = pinned_posts + regular_posts
    
    return render_template('index.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', 'false') == 'true'  # Получаем значение чекбокса "запомнить меня"
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)  # Передаем параметр remember в login_user
            return redirect(url_for('index'))
        
        flash('Неверное имя пользователя или пароль')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/api/posts', methods=['GET'])
@login_required
def posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return jsonify([{
        'id': post.id,
        'content': post.content,
        'image_url': post.image_url,
        'created_at': post.created_at,
        'author': post.author.username
    } for post in posts])

@app.route('/api/posts/<int:post_id>/comments', methods=['GET', 'POST'])
@login_required
def comments(post_id):
    if request.method == 'POST':
        content = request.form.get('content')
        
        comment = Comment(
            content=content,
            user_id=current_user.id,
            post_id=post_id
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({'message': 'Comment added successfully'})
    
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.desc()).all()
    return jsonify([{
        'id': comment.id,
        'content': comment.content,
        'created_at': comment.created_at,
        'author': comment.author.username
    } for comment in comments])

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if like:
        db.session.delete(like)
        db.session.commit()
        return jsonify({'message': 'Post unliked'})
    
    like = Like(user_id=current_user.id, post_id=post_id)
    db.session.add(like)
    db.session.commit()
    
    return jsonify({'message': 'Post liked'})

@app.route('/api/users/<int:user_id>/follow', methods=['POST'])
@login_required
def follow_user(user_id):
    if current_user.id == user_id:
        return jsonify({'message': 'Cannot follow yourself'})
    
    follow = Follow.query.filter_by(follower_id=current_user.id, followed_id=user_id).first()
    
    if follow:
        db.session.delete(follow)
        db.session.commit()
        return jsonify({'message': 'User unfollowed'})
    
    follow = Follow(follower_id=current_user.id, followed_id=user_id)
    db.session.add(follow)
    db.session.commit()
    
    return jsonify({'message': 'User followed'})

@app.route('/friends')
@login_required
def friends():
    # Получаем список друзей и заявок в друзья
    friends = Friendship.query.filter(
        ((Friendship.user_id == current_user.id) | (Friendship.friend_id == current_user.id)) &
        (Friendship.status == 'accepted')
    ).all()
    
    friend_requests = Friendship.query.filter(
        (Friendship.friend_id == current_user.id) &
        (Friendship.status == 'pending')
    ).all()
    
    return render_template('friends.html', friends=friends, friend_requests=friend_requests)

@app.route('/api/friends/<int:user_id>/add', methods=['POST'])
@login_required
def add_friend(user_id):
    if current_user.id == user_id:
        return jsonify({'message': 'Cannot add yourself as a friend'})
    
    # Проверяем, не существует ли уже заявка
    existing_request = Friendship.query.filter(
        ((Friendship.user_id == current_user.id) & (Friendship.friend_id == user_id)) |
        ((Friendship.user_id == user_id) & (Friendship.friend_id == current_user.id))
    ).first()
    
    if existing_request:
        return jsonify({'message': 'Friend request already exists'})
    
    friendship = Friendship(
        user_id=current_user.id,
        friend_id=user_id,
        status='pending'
    )
    
    db.session.add(friendship)
    db.session.commit()
    
    return jsonify({'message': 'Friend request sent'})

@app.route('/api/friends/<int:request_id>/accept', methods=['POST'])
@login_required
def accept_friend(request_id):
    friendship = Friendship.query.get_or_404(request_id)
    
    if friendship.friend_id != current_user.id:
        return jsonify({'message': 'Unauthorized'})
    
    friendship.status = 'accepted'
    db.session.commit()
    
    return jsonify({'message': 'Friend request accepted'})

@app.route('/api/friends/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_friend(request_id):
    friendship = Friendship.query.get_or_404(request_id)
    
    if friendship.friend_id != current_user.id:
        return jsonify({'message': 'Unauthorized'})
    
    friendship.status = 'rejected'
    db.session.commit()
    
    return jsonify({'message': 'Friend request rejected'})

@app.route('/messages')
@login_required
def messages():
    # Получаем список диалогов
    conversations = db.session.query(
        User, PrivateMessage
    ).join(
        PrivateMessage,
        (User.id == PrivateMessage.sender_id) | (User.id == PrivateMessage.receiver_id)
    ).filter(
        (PrivateMessage.sender_id == current_user.id) | (PrivateMessage.receiver_id == current_user.id)
    ).order_by(PrivateMessage.created_at.desc()).all()
    
    return render_template('messages.html', conversations=conversations)

@app.route('/messages/<int:user_id>')
@login_required
def chat(user_id):
    other_user = User.query.get_or_404(user_id)
    
    # Получаем историю сообщений
    messages = PrivateMessage.query.filter(
        ((PrivateMessage.sender_id == current_user.id) & (PrivateMessage.receiver_id == user_id)) |
        ((PrivateMessage.sender_id == user_id) & (PrivateMessage.receiver_id == current_user.id))
    ).order_by(PrivateMessage.created_at.asc()).all()
    
    # Помечаем сообщения как прочитанные
    for message in messages:
        if message.receiver_id == current_user.id and not message.is_read:
            message.is_read = True
    db.session.commit()
    
    return render_template('chat.html', other_user=other_user, messages=messages)

@app.route('/api/messages/<int:user_id>', methods=['POST'])
@login_required
def send_message(user_id):
    content = request.form.get('content')
    
    if not content:
        return jsonify({'message': 'Message content is required'}), 400
    
    message = PrivateMessage(
        sender_id=current_user.id,
        receiver_id=user_id,
        content=content
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'id': message.id,
        'content': message.content,
        'created_at': message.created_at.strftime('%d.%m.%Y %H:%M'),
        'sender': {
            'id': current_user.id,
            'username': current_user.username
        }
    })

@app.route('/users')
@login_required
def users():
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('users.html', users=users)

@app.route('/users/<int:user_id>')
@login_required
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    # Получаем сначала закрепленные посты, затем обычные
    pinned_posts = Post.query.filter_by(author_id=user_id, is_pinned=True).order_by(Post.created_at.desc()).all()
    regular_posts = Post.query.filter_by(author_id=user_id, is_pinned=False).order_by(Post.created_at.desc()).all()
    posts = pinned_posts + regular_posts
    return render_template('user_profile.html', user=user, posts=posts)

@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        flash('Файл не выбран')
        return redirect(url_for('user_profile', user_id=current_user.id))
    
    file = request.files['avatar']
    if file.filename == '':
        flash('Файл не выбран')
        return redirect(url_for('user_profile', user_id=current_user.id))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{current_user.id}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Удаляем старый аватар, если он существует и не является дефолтным
        if current_user.avatar != 'default_avatar.png':
            old_avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.avatar)
            if os.path.exists(old_avatar_path):
                os.remove(old_avatar_path)
        
        current_user.avatar = filename
        db.session.commit()
        flash('Аватар успешно обновлен')
    else:
        flash('Недопустимый формат файла')
    
    return redirect(url_for('user_profile', user_id=current_user.id))

@app.route('/static/uploads/avatars/<filename>')
def uploaded_avatar(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True) 