package com.example.socialnetwork.data.api

import com.example.socialnetwork.data.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    @POST("auth/register")
    suspend fun register(@Body user: Map<String, String>): Response<Map<String, Any>>

    @POST("auth/login")
    suspend fun login(@Body credentials: Map<String, String>): Response<Map<String, Any>>

    @GET("posts")
    suspend fun getPosts(): Response<List<Post>>

    @POST("posts")
    suspend fun createPost(@Body post: Map<String, String>): Response<Map<String, Any>>

    @GET("posts/{postId}/comments")
    suspend fun getComments(@Path("postId") postId: Int): Response<List<Comment>>

    @POST("posts/{postId}/comments")
    suspend fun createComment(
        @Path("postId") postId: Int,
        @Body comment: Map<String, String>
    ): Response<Map<String, Any>>

    @POST("posts/{postId}/like")
    suspend fun toggleLike(@Path("postId") postId: Int): Response<Map<String, Any>>

    @GET("friends")
    suspend fun getFriends(): Response<List<Friend>>

    @GET("friends/requests")
    suspend fun getFriendRequests(): Response<List<FriendRequest>>

    @POST("friends/{userId}/add")
    suspend fun addFriend(@Path("userId") userId: Int): Response<Map<String, Any>>

    @GET("messages")
    suspend fun getConversations(): Response<List<Conversation>>

    @GET("messages/{userId}")
    suspend fun getMessages(@Path("userId") userId: Int): Response<List<Message>>

    @POST("messages/{userId}")
    suspend fun sendMessage(
        @Path("userId") userId: Int,
        @Body message: Map<String, String>
    ): Response<Map<String, Any>>

    @GET("profile")
    suspend fun getProfile(): Response<User>

    @PUT("profile")
    suspend fun updateProfile(@Body profile: Map<String, String>): Response<Map<String, Any>>
}

object ApiClient {
    private const val BASE_URL = "http://192.168.1.100:5000/api/"

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor { chain ->
            val original = chain.request()
            val request = original.newBuilder()
                .header("Content-Type", "application/json")
                .method(original.method, original.body)
                .build()
            chain.proceed(request)
        }
        .build()

    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()

    val apiService: ApiService = retrofit.create(ApiService::class.java)
} 