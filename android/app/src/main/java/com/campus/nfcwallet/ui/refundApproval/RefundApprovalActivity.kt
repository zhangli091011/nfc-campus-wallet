package com.campus.nfcwallet.ui.refundApproval

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.campus.nfcwallet.ui.LoginActivity
import com.campus.nfcwallet.utils.SessionManager

/**
 * 退款申请审批 Activity（管理员使用）
 *
 * 查看收银员提交的退款申请，进行通过或驳回操作。
 */
class RefundApprovalActivity : ComponentActivity() {

    private lateinit var sessionManager: SessionManager

    private val viewModel: RefundApprovalViewModel by viewModels {
        object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return RefundApprovalViewModel(SessionManager(this@RefundApprovalActivity)) as T
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
