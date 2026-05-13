package com.campus.nfcwallet.ui.refundApproval

import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.campus.nfcwallet.api.APIClient
import com.campus.nfcwallet.api.WalletAPIService
import com.campus.nfcwallet.utils.SessionManager
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

data class RefundRequestItem(
    val id: Int,
    val requesterName: String,
    val txnAmount: Double,
    val cardUid: String?,
    val reason: String,
    val status: String,
    val createdAt: String?,
    val txnTime: String?,
)

data class RefundApprovalUiState(
    val requests: List<RefundRequestItem> = emptyList(),
    val isLoading: Boolean = false,
    val isProcessing: Boolean = false,
    val errorMessage: String? = null,
    val successMessage: String? = null,
    val filter: String = "pending", // pending, approved, rejected, all
    val hasNewNotification: Boolean = false,
    val notificationMessage: String? = null,
)

class RefundApprovalViewModel(
    private val sessionManager: SessionManager,
    private val onNewRequest: (() -> Unit)? = null,
) : ViewModel() {

    private val TAG = "RefundApprovalVM"
    private val apiService: WalletAPIService = APIClient.getAPIService()

    var uiState by mutableStateOf(RefundApprovalUiState())
        private set

    private var previousPendingCount: Int? = null
    private var pollingJob: Job? = null

    fun init() {
        loadRequests()
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
                loadRequestsSilent()
            }
        }
    }

    // 静默刷新（不显示loading状态）
    private fun loadRequestsSilent() {
        val token = sessionManager.authHeader ?: return
        val statusParam = if (uiState.filter == "all") null else uiState.filter

        apiService.getRefundRequests(token, statusParam, 50, 0)
            .enqueue(object : Callback<Map<String, Any>> {
                @Suppress("UNCHECKED_CAST")
                override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                    if (response.isSuccessful && response.body() != null) {
                        val data = response.body()!!
                        val rawList = data["requests"] as? List<Map<String, Any>> ?: emptyList()
                        val items = rawList.map { r ->
                            RefundRequestItem(
                                id = (r["id"] as? Double)?.toInt() ?: 0,
                                requesterName = r["requester_name"] as? String ?: "-",
                                txnAmount = (r["txn_amount"] as? Double) ?: 0.0,
                                cardUid = r["card_uid"] as? String,
                                reason = r["reason"] as? String ?: "",
                                status = r["status"] as? String ?: "pending",
                                createdAt = r["created_at"] as? String,
                                txnTime = r["txn_time"] as? String,
                            )
                        }

                        // 检测新的待审批请求
                        val currentPendingCount = items.count { it.status == "pending" }
                        if (previousPendingCount != null && currentPendingCount > previousPendingCount!!) {
                            onNewRequest?.invoke()
                            uiState = uiState.copy(
                                hasNewNotification = true,
                                notificationMessage = "收到 ${currentPendingCount - previousPendingCount!!} 条新退款申请"
                            )
                        }
                        previousPendingCount = currentPendingCount

                        uiState = uiState.copy(requests = items)
                    }
                }

                override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                    // 静默失败，不影响UI
                    Log.d(TAG, "静默刷新失败: ${t.message}")
                }
            })
    }

    fun setFilter(filter: String) {
        uiState = uiState.copy(filter = filter)
        loadRequests()
    }

    @Suppress("UNCHECKED_CAST")
    fun loadRequests() {
        val token = sessionManager.authHeader ?: return
        uiState = uiState.copy(isLoading = true)

        val statusParam = if (uiState.filter == "all") null else uiState.filter

        apiService.getRefundRequests(token, statusParam, 50, 0)
            .enqueue(object : Callback<Map<String, Any>> {
                override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                    if (response.isSuccessful && response.body() != null) {
                        val data = response.body()!!
                        val rawList = data["requests"] as? List<Map<String, Any>> ?: emptyList()
                        val items = rawList.map { r ->
                            RefundRequestItem(
                                id = (r["id"] as? Double)?.toInt() ?: 0,
                                requesterName = r["requester_name"] as? String ?: "-",
                                txnAmount = (r["txn_amount"] as? Double) ?: 0.0,
                                cardUid = r["card_uid"] as? String,
                                reason = r["reason"] as? String ?: "",
                                status = r["status"] as? String ?: "pending",
                                createdAt = r["created_at"] as? String,
                                txnTime = r["txn_time"] as? String,
                            )
                        }
                        uiState = uiState.copy(isLoading = false, requests = items)
                    } else {
                        uiState = uiState.copy(isLoading = false, errorMessage = "加载失败")
                    }
                }

                override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                    Log.e(TAG, "加载退款申请失败", t)
                    uiState = uiState.copy(isLoading = false, errorMessage = "网络错误: ${t.message}")
                }
            })
    }

    fun approveRequest(id: Int) {
        val token = sessionManager.authHeader ?: return
        uiState = uiState.copy(isProcessing = true)

        val body = HashMap<String, Any>()
        body["remark"] = ""

        apiService.approveRefundRequest(token, id, body)
            .enqueue(object : Callback<Map<String, Any>> {
                override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                    if (response.isSuccessful) {
                        uiState = uiState.copy(isProcessing = false, successMessage = "退款申请已通过")
                        loadRequests()
                    } else {
                        val error = APIClient.getErrorMessage(response) ?: "审批失败"
                        uiState = uiState.copy(isProcessing = false, errorMessage = error)
                    }
                }

                override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                    uiState = uiState.copy(isProcessing = false, errorMessage = "网络错误: ${t.message}")
                }
            })
    }

    fun rejectRequest(id: Int) {
        val token = sessionManager.authHeader ?: return
        uiState = uiState.copy(isProcessing = true)

        val body = HashMap<String, Any>()
        body["remark"] = "管理员驳回"

        apiService.rejectRefundRequest(token, id, body)
            .enqueue(object : Callback<Map<String, Any>> {
                override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                    if (response.isSuccessful) {
                        uiState = uiState.copy(isProcessing = false, successMessage = "退款申请已驳回")
                        loadRequests()
                    } else {
                        val error = APIClient.getErrorMessage(response) ?: "驳回失败"
                        uiState = uiState.copy(isProcessing = false, errorMessage = error)
                    }
                }

                override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                    uiState = uiState.copy(isProcessing = false, errorMessage = "网络错误: ${t.message}")
                }
            })
    }

    fun dismissMessage() {
        uiState = uiState.copy(errorMessage = null, successMessage = null, hasNewNotification = false, notificationMessage = null)
    }
}
