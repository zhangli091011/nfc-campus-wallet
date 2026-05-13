package com.campus.nfcwallet.ui.refundApproval

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.core.app.NotificationCompat
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.campus.nfcwallet.R
import com.campus.nfcwallet.ui.LoginActivity
import com.campus.nfcwallet.utils.SessionManager

/**
 * 退款申请审批 Activity（管理员使用）
 *
 * 查看收银员提交的退款申请，进行通过或驳回操作。
 * 每5秒自动刷新，收到新退款申请时发送系统通知。
 */
class RefundApprovalActivity : ComponentActivity() {

    private lateinit var sessionManager: SessionManager
    private var notificationId = 1001

    companion object {
        const val CHANNEL_ID = "refund_approval_channel"
    }

    private val viewModel: RefundApprovalViewModel by viewModels {
        object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return RefundApprovalViewModel(
                    sessionManager = SessionManager(this@RefundApprovalActivity),
                    onNewRequest = { sendNotification("收到新退款申请", "有新的退款申请等待审批") },
                ) as T
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        sessionManager = SessionManager(this)

        if (!sessionManager.isLoggedIn) {
            navigateToLogin()
            return
        }

        createNotificationChannel()
        viewModel.init()

        setContent {
            androidx.compose.foundation.layout.Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(RefundApprovalColors.Background)
            ) {
                RefundApprovalScreen(
                    state = viewModel.uiState,
                    onApprove = viewModel::approveRequest,
                    onReject = viewModel::rejectRequest,
                    onFilterChange = viewModel::setFilter,
                    onRefresh = viewModel::loadRequests,
                    onDismissMessage = viewModel::dismissMessage,
                    onLogout = { logout() },
                )
            }
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "退款审批通知",
                NotificationManager.IMPORTANCE_HIGH,
            ).apply {
                description = "收到新退款申请时通知"
            }
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }

    private fun sendNotification(title: String, content: String) {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_launcher)
            .setContentTitle(title)
            .setContentText(content)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .build()
        manager.notify(notificationId++, notification)
    }

    private fun logout() {
        sessionManager.clearSession()
        navigateToLogin()
    }

    private fun navigateToLogin() {
        val intent = Intent(this, LoginActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
        startActivity(intent)
        finish()
    }
}
