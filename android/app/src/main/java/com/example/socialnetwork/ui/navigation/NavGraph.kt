package com.example.socialnetwork.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.example.socialnetwork.ui.screens.*

sealed class Screen(val route: String) {
    object Login : Screen("login")
    object Register : Screen("register")
    object Home : Screen("home")
    object Profile : Screen("profile")
    object Friends : Screen("friends")
    object Messages : Screen("messages")
    object Chat : Screen("chat/{userId}") {
        fun createRoute(userId: Int) = "chat/$userId"
    }
    object PostDetails : Screen("post/{postId}") {
        fun createRoute(postId: Int) = "post/$postId"
    }
}

@Composable
fun NavGraph(navController: NavHostController) {
    NavHost(
        navController = navController,
        startDestination = Screen.Login.route
    ) {
        composable(Screen.Login.route) {
            LoginScreen(navController)
        }
        composable(Screen.Register.route) {
            RegisterScreen(navController)
        }
        composable(Screen.Home.route) {
            HomeScreen(navController)
        }
        composable(Screen.Profile.route) {
            ProfileScreen(navController)
        }
        composable(Screen.Friends.route) {
            FriendsScreen(navController)
        }
        composable(Screen.Messages.route) {
            MessagesScreen(navController)
        }
        composable(Screen.Chat.route) { backStackEntry ->
            val userId = backStackEntry.arguments?.getString("userId")?.toIntOrNull()
            if (userId != null) {
                ChatScreen(navController, userId)
            }
        }
        composable(Screen.PostDetails.route) { backStackEntry ->
            val postId = backStackEntry.arguments?.getString("postId")?.toIntOrNull()
            if (postId != null) {
                PostDetailsScreen(navController, postId)
            }
        }
    }
} 