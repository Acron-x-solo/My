from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app
from models import db, User, Post, Comment, Like, Follow, Friendship, PrivateMessage
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/')
def index():
    return render_template('index.html')

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
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/api/posts', methods=['GET', 'POST'])
@login_required
def posts():
    if request.method == 'POST':
        content = request.form.get('content')
        image_url = request.form.get('image_url')
        
        post = Post(
            content=content,
            image_url=image_url,
            user_id=current_user.id
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({'message': 'Post created successfully'})
    
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
        return jsonify({'message': 'Message content is required'})
    
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
    })

@app.route('/users')
@login_required
def users():
    search = request.args.get('search', '')
    if search:
        users = User.query.filter(User.username.ilike(f'%{search}%')).all()
    else:
        users = User.query.all()
    return render_template('users.html', users=users, search=search)

@app.route('/users/<int:user_id>')
@login_required
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc()).all()
    
    # Проверяем статус дружбы
    friendship = Friendship.query.filter(
        ((Friendship.user_id == current_user.id) & (Friendship.friend_id == user_id)) |
        ((Friendship.user_id == user_id) & (Friendship.friend_id == current_user.id))
    ).first()
    
    return render_template('user_profile.html', user=user, posts=posts, friendship=friendship) 