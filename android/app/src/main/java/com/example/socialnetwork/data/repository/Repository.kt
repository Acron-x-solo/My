package com.example.socialnetwork.data.repository

import com.example.socialnetwork.data.*
import com.example.socialnetwork.data.api.ApiClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import retrofit2.Response

class Repository {
    private val apiService = ApiClient.apiService

    suspend fun register(username: String, email: String, password: String): Response<Map<String, Any>> {
        return withContext(Dispatchers.IO) {
            apiService.register(mapOf(
                "username" to username,
                "email" to email,
                "password" to password
            ))
        }
    }

    suspend fun login(username: String, password: String): Response<Map<String, Any>> {
        return withContext(Dispatchers.IO) {
            apiService.login(mapOf(
                "username" to username,
                "password" to password
            ))
        }
    }

    suspend fun getPosts(): Response<List<Post>> {
        return withContext(Dispatchers.IO) {
            apiService.getPosts()
        }
    }

    suspend fun createPost(content: String, imageUrl: String? = null): Response<Map<String, Any>> {
        return withContext(Dispatchers.IO) {
            apiService.createPost(mapOf(
                "content" to content,
                "image_url" to (imageUrl ?: "")
            ))
        }
    }

    suspend fun getComments(postId: Int): Response<List<Comment>> {
        return withContext(Dispatchers.IO) {
            apiService.getComments(postId)
        }
    }

    suspend fun createComment(postId: Int, content: String): Response<Map<String, Any>> {
        return withContext(Dispatchers.IO) {
            apiService.createComment(postId, mapOf("content" to content))
        }
    }

    suspend fun toggleLike(postId: Int): Response<Map<String, Any>> {
        return withContext(Dispatchers.IO) {
            apiService.toggleLike(postId)
        }
    }

    suspend fun getFriends(): Response<List<Friend>> {
        return withContext(Dispatchers.IO) {
            apiService.getFriends()
        }
    }

    suspend fun getFriendRequests(): Response<List<FriendRequest>> {
        return withContext(Dispatchers.IO) {
            apiService.getFriendRequests()
        }
    }

    suspend fun addFriend(userId: Int): Response<Map<String, Any>> {
        return withContext(Dispatchers.IO) {
            apiService.addFriend(userId)
        }
    }

    suspend fun getConversations(): Response<List<Conversation>> {
        return withContext(Dispatchers.IO) {
            apiService.getConversations()
        }
    }

    suspend fun getMessages(userId: Int): Response<List<Message>> {
        return withContext(Dispatchers.IO) {
            apiService.getMessages(userId)
        }
    }

    suspend fun sendMessage(userId: Int, content: String): Response<Map<String, Any>> {
        return withContext(Dispatchers.IO) {
            apiService.sendMessage(userId, mapOf("content" to content))
        }
    }

    suspend fun getProfile(): Response<User> {
        return withContext(Dispatchers.IO) {
            apiService.getProfile()
        }
    }

    suspend fun updateProfile(
        username: String? = null,
        email: String? = null,
        bio: String? = null,
        avatar: String? = null
    ): Response<Map<String, Any>> {
        return withContext(Dispatchers.IO) {
            val profile = mutableMapOf<String, String>()
            username?.let { profile["username"] = it }
            email?.let { profile["email"] = it }
            bio?.let { profile["bio"] = it }
            avatar?.let { profile["avatar"] = it }
            apiService.updateProfile(profile)
        }
    }
} 