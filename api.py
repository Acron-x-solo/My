from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from models import db, User, Post, Comment, Like, Follow, Friendship, PrivateMessage
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from werkzeug.utils import secure_filename
import os

api = Blueprint('api', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Аутентификация
@api.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User registered successfully',
        'user_id': user.id
    }), 201

@api.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password_hash, password):
        return jsonify({
            'message': 'Login successful',
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'avatar': user.avatar
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

# Посты
@api.route('/posts', methods=['GET'])
@login_required
def get_posts():
    # Сначала получаем закрепленные посты
    pinned_posts = Post.query.filter_by(is_pinned=True).order_by(Post.created_at.desc()).all()
    # Затем получаем обычные посты
    regular_posts = Post.query.filter_by(is_pinned=False).order_by(Post.created_at.desc()).all()
    
    # Объединяем посты, сначала закрепленные, затем обычные
    all_posts = pinned_posts + regular_posts
    
    return jsonify([{
        'id': post.id,
        'content': post.content,
        'image_url': post.image_url,
        'created_at': post.created_at.isoformat(),
        'is_pinned': post.is_pinned,
        'author': {
            'id': post.author.id,
            'username': post.author.username,
            'avatar': post.author.avatar
        },
        'likes_count': len(post.likes),
        'comments_count': len(post.comments),
        'is_liked': any(like.user_id == current_user.id for like in post.likes)
    } for post in all_posts])

@api.route('/posts', methods=['POST'])
@login_required
def create_post():
    try:
        # Получаем данные из формы
        content = request.form.get('content')
        image = request.files.get('image')
        
        # Проверяем обязательное поле content
        if not content:
            return jsonify({'error': 'Содержание поста обязательно'}), 400
            
        # Обрабатываем изображение, если оно есть
        image_url = None
        if image and image.filename:
            if not allowed_file(image.filename):
                return jsonify({'error': 'Недопустимый формат файла'}), 400
                
            # Создаем уникальное имя файла
            filename = secure_filename(f"{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{image.filename}")
            
            # Создаем директорию для изображений, если её нет
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'posts')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Сохраняем файл
            image_path = os.path.join(upload_folder, filename)
            image.save(image_path)
            
            # Сохраняем относительный путь для URL
            image_url = f'/static/uploads/posts/{filename}'
        
        # Создаем пост
        post = Post(
            content=content,
            image_url=image_url,
            author_id=current_user.id,
            is_pinned=False
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'message': 'Пост успешно создан',
            'post': {
                'id': post.id,
                'content': post.content,
                'image_url': post.image_url,
                'created_at': post.created_at.isoformat(),
                'author': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'avatar': current_user.avatar
                }
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при создании поста: {str(e)}'}), 500

# Комментарии
@api.route('/posts/<int:post_id>/comments', methods=['GET'])
@login_required
def get_comments(post_id):
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.desc()).all()
    return jsonify([{
        'id': comment.id,
        'content': comment.content,
        'created_at': comment.created_at.isoformat(),
        'author': {
            'id': comment.author.id,
            'username': comment.author.username,
            'avatar': comment.author.avatar
        }
    } for comment in comments])

@api.route('/posts/<int:post_id>/comments', methods=['POST'])
@login_required
def create_comment(post_id):
    data = request.get_json()
    content = data.get('content')
    
    comment = Comment(
        content=content,
        user_id=current_user.id,
        post_id=post_id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'message': 'Comment added successfully',
        'comment_id': comment.id
    }), 201

# Лайки
@api.route('/posts/<int:post_id>/like', methods=['POST'])
@login_required
def toggle_like(post_id):
    like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if like:
        db.session.delete(like)
        db.session.commit()
        return jsonify({'message': 'Post unliked', 'is_liked': False})
    
    like = Like(user_id=current_user.id, post_id=post_id)
    db.session.add(like)
    db.session.commit()
    
    return jsonify({'message': 'Post liked', 'is_liked': True})

# Друзья
@api.route('/friends', methods=['GET'])
@login_required
def get_friends():
    friends = Friendship.query.filter(
        ((Friendship.user_id == current_user.id) | (Friendship.friend_id == current_user.id)) &
        (Friendship.status == 'accepted')
    ).all()
    
    return jsonify([{
        'id': friend.friend.id if friend.user_id == current_user.id else friend.user.id,
        'username': friend.friend.username if friend.user_id == current_user.id else friend.user.username,
        'avatar': friend.friend.avatar if friend.user_id == current_user.id else friend.user.avatar,
        'status': friend.status
    } for friend in friends])

@api.route('/friends/requests', methods=['GET'])
@login_required
def get_friend_requests():
    requests = Friendship.query.filter(
        (Friendship.friend_id == current_user.id) &
        (Friendship.status == 'pending')
    ).all()
    
    return jsonify([{
        'id': request.user.id,
        'username': request.user.username,
        'avatar': request.user.avatar,
        'request_id': request.id
    } for request in requests])

@api.route('/friends/<int:user_id>/add', methods=['POST'])
@login_required
def add_friend(user_id):
    if current_user.id == user_id:
        return jsonify({'error': 'Cannot add yourself as a friend'}), 400
    
    existing_request = Friendship.query.filter(
        ((Friendship.user_id == current_user.id) & (Friendship.friend_id == user_id)) |
        ((Friendship.user_id == user_id) & (Friendship.friend_id == current_user.id))
    ).first()
    
    if existing_request:
        return jsonify({'error': 'Friend request already exists'}), 400
    
    friendship = Friendship(
        user_id=current_user.id,
        friend_id=user_id,
        status='pending'
    )
    
    db.session.add(friendship)
    db.session.commit()
    
    return jsonify({'message': 'Friend request sent'})

# Сообщения
@api.route('/messages', methods=['GET'])
@login_required
def get_conversations():
    conversations = db.session.query(
        User, PrivateMessage
    ).join(
        PrivateMessage,
        (User.id == PrivateMessage.sender_id) | (User.id == PrivateMessage.receiver_id)
    ).filter(
        (PrivateMessage.sender_id == current_user.id) | (PrivateMessage.receiver_id == current_user.id)
    ).order_by(PrivateMessage.created_at.desc()).all()
    
    return jsonify([{
        'user': {
            'id': user.id,
            'username': user.username,
            'avatar': user.avatar
        },
        'last_message': {
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'is_read': message.is_read
        }
    } for user, message in conversations])

@api.route('/messages/<int:user_id>', methods=['GET'])
@login_required
def get_messages(user_id):
    messages = PrivateMessage.query.filter(
        ((PrivateMessage.sender_id == current_user.id) & (PrivateMessage.receiver_id == user_id)) |
        ((PrivateMessage.sender_id == user_id) & (PrivateMessage.receiver_id == current_user.id))
    ).order_by(PrivateMessage.created_at.asc()).all()
    
    # Помечаем сообщения как прочитанные
    for message in messages:
        if message.receiver_id == current_user.id and not message.is_read:
            message.is_read = True
    db.session.commit()
    
    return jsonify([{
        'id': message.id,
        'content': message.content,
        'created_at': message.created_at.isoformat(),
        'is_read': message.is_read,
        'is_sender': message.sender_id == current_user.id
    } for message in messages])

@api.route('/messages/<int:user_id>', methods=['POST'])
@login_required
def send_message(user_id):
    data = request.get_json()
    content = data.get('content')
    
    message = PrivateMessage(
        sender_id=current_user.id,
        receiver_id=user_id,
        content=content
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'message': 'Message sent successfully',
        'message_id': message.id
    }), 201

# Профиль
@api.route('/profile', methods=['GET'])
@login_required
def get_profile():
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'avatar': current_user.avatar,
        'bio': current_user.bio,
        'created_at': current_user.created_at.isoformat(),
        'posts_count': len(current_user.posts),
        'friends_count': len(current_user.friends),
        'followers_count': len(current_user.followers),
        'following_count': len(current_user.following)
    })

@api.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json()
    
    if 'username' in data:
        current_user.username = data['username']
    if 'email' in data:
        current_user.email = data['email']
    if 'bio' in data:
        current_user.bio = data['bio']
    if 'avatar' in data:
        current_user.avatar = data['avatar']
    
    db.session.commit()
    
    return jsonify({'message': 'Profile updated successfully'})

@api.route('/posts/<int:post_id>/pin', methods=['POST'])
@login_required
def toggle_pin(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Проверяем, что пользователь является автором поста
    if post.author_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    post.is_pinned = not post.is_pinned
    db.session.commit()
    
    return jsonify({
        'message': 'Post pinned successfully' if post.is_pinned else 'Post unpinned successfully',
        'is_pinned': post.is_pinned
    }) 