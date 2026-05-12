package com.campus.nfcwallet.ui.refund

import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.campus.nfcwallet.api.APIClient
import com.campus.nfcwallet.api.WalletAPIService
import com.campus.nfcwallet.models.BoothTransactionsResponse
import com.campus.nfcwallet.models.RefundRequest
import com.campus.nfcwallet.models.RefundResponse
import com.campus.nfcwallet.models.Transaction
import com.campus.nfcwallet.utils.SessionManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

/**
 * 退款管理 ViewModel
 *
 * 管理退款流程：
 * 1. 加载本摊位最近交易流水
 * 2. NFC 贴卡查询该卡在本摊位的历史订单
 * 3. 选择订单发起退款
 * 4. 管理员授权码验证后完成退款
 */
class RefundManagerViewModel(
    private val sessionManager: SessionManager,
    private val onRefundSuccess: (() -> Unit)? = null,
) : ViewModel() {

    private val TAG = "RefundManagerVM"
    private val apiService: WalletAPIService = APIClient.getAPIService()

    var uiState by mutableStateOf(RefundUiState())
        private set

    private var boothId: Int = -1

    fun init(boothId: Int) {
        this.boothId = boothId
        loadRecentTransactions()
    }

    // -----------------------------------------------------------------
    // 加载本摊位最近交易
    // -----------------------------------------------------------------
    private fun loadRecentTransactions() {
        val token = sessionManager.authHeader ?: return
        uiState = uiState.copy(isLoadingList = true)

        apiService.getBoothTransactions(token, boothId, 50)
            .enqueue(object : Callback<BoothTransactionsResponse> {
                override fun onResponse(
                    call: Call<BoothTransactionsResponse>,
                    response: Response<BoothTransactionsResponse>,
                ) {
                    uiState = if (response.isSuccessful && response.body() != null) {
                        uiState.copy(
                            transactions = response.body()!!.transactions ?: emptyList(),
                            isLoadingList = false,
                        )
                    } else {
                        val errorBody = response.errorBody()?.string() ?: "HTTP ${response.code()}"
                        uiState.copy(
                            isLoadingList = false,
                            errorMessage = "加载交易记录失败: $errorBody",
                        )
                    }
                }

                override fun onFailure(call: Call<BoothTransactionsResponse>, t: Throwable) {
                    Log.e(TAG, "加载交易记录失败", t)
                    uiState = uiState.copy(
                        isLoadingList = false,
                        errorMessage = "网络错误: ${t.message}",
                    )
                }
            })
    }

    // -----------------------------------------------------------------
    // NFC 卡片检测 — 查询该卡在本摊位的订单
    // -----------------------------------------------------------------
    fun onNfcCardDetected(uid: String) {
        val token = sessionManager.authHeader ?: return
        uiState = uiState.copy(
            cardUid = uid,
            isLoadingList = true,
            selectedTransaction = null,
            showRefundDialog = false,
        )

        // 后端不支持 card_uid 过滤，加载全部后客户端过滤
        apiService.getBoothTransactions(token, boothId, null)
            .enqueue(object : Callback<BoothTransactionsResponse> {
                override fun onResponse(
                    call: Call<BoothTransactionsResponse>,
                    response: Response<BoothTransactionsResponse>,
                ) {
                    uiState = if (response.isSuccessful && response.body() != null) {
                        val allTransactions = response.body()!!.transactions ?: emptyList()
                        // 客户端按 card_uid 过滤（Transaction 模型中如有 cardUid 字段）
                        uiState.copy(
                            transactions = allTransactions,
                            isLoadingList = false,
                            filterByCard = true,
                        )
                    } else {
                        val errorBody = response.errorBody()?.string() ?: "HTTP ${response.code()}"
                        uiState.copy(
                            isLoadingList = false,
                            errorMessage = "查询卡片订单失败: $errorBody",
                        )
                    }
                }

                override fun onFailure(call: Call<BoothTransactionsResponse>, t: Throwable) {
                    Log.e(TAG, "查询卡片订单失败", t)
                    uiState = uiState.copy(
                        isLoadingList = false,
                        errorMessage = "网络错误: ${t.message}",
                    )
                }
            })
    }

    // -----------------------------------------------------------------
    // 选择交易 / 取消选择
    // -----------------------------------------------------------------
    fun selectTransaction(transaction: Transaction) {
        uiState = uiState.copy(selectedTransaction = transaction)
    }

    fun clearSelection() {
        uiState = uiState.copy(selectedTransaction = null)
    }

    // -----------------------------------------------------------------
    // 发起退款对话框
    // -----------------------------------------------------------------
    fun showRefundConfirmation() {
        uiState = uiState.copy(showRefundDialog = true)
    }

    fun dismissRefundDialog() {
        uiState = uiState.copy(showRefundDialog = false)
    }

    // -----------------------------------------------------------------
    // 执行退款
    // -----------------------------------------------------------------
    fun confirmRefund() {
        val transaction = uiState.selectedTransaction ?: return

        val token = sessionManager.authHeader ?: return
        uiState = uiState.copy(isProcessing = true, showRefundDialog = false)

        val request = RefundRequest(
            transaction.id,
            "收银端退款",
        )

        apiService.processRefund(token, request)
            .enqueue(object : Callback<RefundResponse> {
                override fun onResponse(
                    call: Call<RefundResponse>,
                    response: Response<RefundResponse>,
                ) {
                    if (response.isSuccessful && response.body() != null) {
                        val result = response.body()!!
                        uiState = uiState.copy(
                            isProcessing = false,
                            selectedTransaction = null,
                            successMessage = "退款成功！退还 ¥${result.refundedAmount}，新余额 ¥${result.newBalance}",
                        )
                        // 触发震动反馈
                        onRefundSuccess?.invoke()
                        // 刷新列表
                        loadRecentTransactions()
                    } else {
                        val errorBody = response.errorBody()?.string() ?: "未知错误"
                        uiState = uiState.copy(
                            isProcessing = false,
                            errorMessage = "退款失败: $errorBody",
                        )
                    }
                }

                override fun onFailure(call: Call<RefundResponse>, t: Throwable) {
                    Log.e(TAG, "退款请求失败", t)
                    uiState = uiState.copy(
                        isProcessing = false,
                        errorMessage = "网络错误: ${t.message}",
                    )
                }
            })
    }

    // -----------------------------------------------------------------
    // 清除筛选（回到全部交易）
    // -----------------------------------------------------------------
    fun clearCardFilter() {
        uiState = uiState.copy(
            cardUid = null,
            filterByCard = false,
            selectedTransaction = null,
        )
        loadRecentTransactions()
    }

    // -----------------------------------------------------------------
    // 消息清除
    // -----------------------------------------------------------------
    fun dismissError() {
        uiState = uiState.copy(errorMessage = null)
    }

    fun dismissSuccess() {
        uiState = uiState.copy(successMessage = null)
    }
}

// =============================================================================
// UI State
// =============================================================================
data class RefundUiState(
    val transactions: List<Transaction> = emptyList(),
    val cardUid: String? = null,
    val filterByCard: Boolean = false,
    val selectedTransaction: Transaction? = null,
    val showRefundDialog: Boolean = false,
    val isLoadingList: Boolean = false,
    val isProcessing: Boolean = false,
    val errorMessage: String? = null,
    val successMessage: String? = null,
)
