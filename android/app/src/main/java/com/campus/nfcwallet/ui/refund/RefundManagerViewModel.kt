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
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
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
    private val onRefundApproved: (() -> Unit)? = null,
) : ViewModel() {

    private val TAG = "RefundManagerVM"
    private val apiService: WalletAPIService = APIClient.getAPIService()

    var uiState by mutableStateOf(RefundUiState())
        private set

    private var boothId: Int = -1
    private var pollingJob: Job? = null
    private var previousApprovedCount: Int? = null

    fun init(boothId: Int) {
        this.boothId = boothId
        loadRecentTransactions()
        startPolling()
    }

    override fun onCleared() {
        super.onCleared()
        pollingJob?.cancel()
    }

    private fun startPolling() {
        pollingJob?.cancel()
        pollingJob = viewModelScope.launch {
            while (isActive) {
                delay(5000)
                loadRecentTransactionsSilent()
                checkRefundRequestStatus()
            }
        }
    }

    // 静默刷新交易列表
    private fun loadRecentTransactionsSilent() {
        val token = sessionManager.authHeader ?: return
        apiService.getBoothTransactions(token, boothId, 50)
            .enqueue(object : Callback<BoothTransactionsResponse> {
                override fun onResponse(
                    call: Call<BoothTransactionsResponse>,
                    response: Response<BoothTransactionsResponse>,
                ) {
                    if (response.isSuccessful && response.body() != null) {
                        uiState = uiState.copy(
                            transactions = response.body()!!.transactions ?: emptyList(),
                        )
                    }
                }

                override fun onFailure(call: Call<BoothTransactionsResponse>, t: Throwable) {
                    Log.d(TAG, "静默刷新失败: ${t.message}")
                }
            })
    }

    // 检查退款申请状态变化（收银员提交的申请是否被审批）
    @Suppress("UNCHECKED_CAST")
    private fun checkRefundRequestStatus() {
        val token = sessionManager.authHeader ?: return
        // 查询已审批的退款申请
        apiService.getRefundRequests(token, "approved", 50, 0)
            .enqueue(object : Callback<Map<String, Any>> {
                override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                    if (response.isSuccessful && response.body() != null) {
                        val data = response.body()!!
                        val rawList = data["requests"] as? List<Map<String, Any>> ?: emptyList()
                        val currentApprovedCount = rawList.size

                        if (previousApprovedCount != null && currentApprovedCount > previousApprovedCount!!) {
                            // 有新的退款申请被通过
                            onRefundApproved?.invoke()
                            uiState = uiState.copy(
                                successMessage = "🎉 您的退款申请已被管理员通过！"
                            )
                            loadRecentTransactionsSilent()
                        }
                        previousApprovedCount = currentApprovedCount
                    }
                }

                override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                    // 静默失败
                }
            })
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

        // booth_cashier 提交退款申请（需管理员审批）
        // super_admin / event_admin 直接执行退款
        val userRole = sessionManager.userInfo?.role ?: ""
        
        if (userRole == "booth_cashier") {
            submitRefundRequest(token, transaction.id)
        } else {
            executeRefundDirectly(token, transaction.id)
        }
    }

    private fun submitRefundRequest(token: String, transactionId: Int) {
        val requestData = HashMap<String, Any>()
        requestData["original_transaction_id"] = transactionId
        requestData["reason"] = "收银端退款申请"

        apiService.createRefundRequest(token, requestData)
            .enqueue(object : Callback<Map<String, Any>> {
                override fun onResponse(
                    call: Call<Map<String, Any>>,
                    response: Response<Map<String, Any>>,
                ) {
                    if (response.isSuccessful && response.body() != null) {
                        val result = response.body()!!
                        val resultStatus = result["status"] as? String ?: ""
                        val message = result["message"] as? String ?: "操作完成"

                        if (resultStatus == "pending") {
                            // 申请已提交，等待审批
                            uiState = uiState.copy(
                                isProcessing = false,
                                selectedTransaction = null,
                                successMessage = "✅ 退款申请已提交，等待管理员审批",
                            )
                        } else {
                            // 管理员直接通过（不应该走到这里，但兼容）
                            val refunded = (result["refunded_amount"] as? Double) ?: 0.0
                            val newBalance = (result["new_balance"] as? Double) ?: 0.0
                            uiState = uiState.copy(
                                isProcessing = false,
                                selectedTransaction = null,
                                successMessage = "退款成功！退还 ¥${"%.2f".format(refunded)}，新余额 ¥${"%.2f".format(newBalance)}",
                            )
                            onRefundSuccess?.invoke()
                        }
                        loadRecentTransactions()
                    } else {
                        val errorBody = response.errorBody()?.string() ?: "未知错误"
                        uiState = uiState.copy(
                            isProcessing = false,
                            errorMessage = "退款申请失败: $errorBody",
                        )
                    }
                }

                override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                    Log.e(TAG, "退款申请请求失败", t)
                    uiState = uiState.copy(
                        isProcessing = false,
                        errorMessage = "网络错误: ${t.message}",
                    )
                }
            })
    }

    private fun executeRefundDirectly(token: String, transactionId: Int) {
        val request = RefundRequest(
            transactionId,
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
                        onRefundSuccess?.invoke()
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
