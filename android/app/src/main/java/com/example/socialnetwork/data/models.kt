package com.example.socialnetwork.data

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.google.gson.annotations.SerializedName

data class User(
    @SerializedName("id") val id: Int,
    @SerializedName("username") val username: String,
    @SerializedName("email") val email: String,
    @SerializedName("avatar") val avatar: String?,
    @SerializedName("bio") val bio: String?,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("posts_count") val postsCount: Int,
    @SerializedName("friends_count") val friendsCount: Int,
    @SerializedName("followers_count") val followersCount: Int,
    @SerializedName("following_count") val followingCount: Int
)

data class Post(
    @SerializedName("id") val id: Int,
    @SerializedName("content") val content: String,
    @SerializedName("image_url") val imageUrl: String?,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("author") val author: User,
    @SerializedName("likes_count") val likesCount: Int,
    @SerializedName("comments_count") val commentsCount: Int,
    @SerializedName("is_liked") val isLiked: Boolean
)

data class Comment(
    @SerializedName("id") val id: Int,
    @SerializedName("content") val content: String,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("author") val author: User
)

data class Message(
    @SerializedName("id") val id: Int,
    @SerializedName("content") val content: String,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("is_read") val isRead: Boolean,
    @SerializedName("is_sender") val isSender: Boolean
)

data class Conversation(
    @SerializedName("user") val user: User,
    @SerializedName("last_message") val lastMessage: Message
)

data class Friend(
    @SerializedName("id") val id: Int,
    @SerializedName("username") val username: String,
    @SerializedName("avatar") val avatar: String?,
    @SerializedName("status") val status: String
)

data class FriendRequest(
    @SerializedName("id") val id: Int,
    @SerializedName("username") val username: String,
    @SerializedName("avatar") val avatar: String?,
    @SerializedName("request_id") val requestId: Int
)

@Entity(tableName = "users")
data class LocalUser(
    @PrimaryKey val id: Int,
    val username: String,
    val email: String,
    val avatar: String?,
    val bio: String?,
    val token: String?
)

@Entity(tableName = "posts")
data class LocalPost(
    @PrimaryKey val id: Int,
    val content: String,
    val imageUrl: String?,
    val createdAt: String,
    val authorId: Int,
    val likesCount: Int,
    val commentsCount: Int,
    val isLiked: Boolean
)

@Entity(tableName = "messages")
data class LocalMessage(
    @PrimaryKey val id: Int,
    val content: String,
    val createdAt: String,
    val isRead: Boolean,
    val isSender: Boolean,
    val userId: Int
) 