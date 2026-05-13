package com.campus.nfcwallet.ui.cardReturn

import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.campus.nfcwallet.api.APIClient
import com.campus.nfcwallet.api.WalletAPIService
import com.campus.nfcwallet.models.BalanceResponse
import com.campus.nfcwallet.models.ParticipantInfo
import com.campus.nfcwallet.utils.SessionManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import kotlin.coroutines.resume

/**
 * 还款+退卡终端 ViewModel
 *
 * 管理还款和退卡的完整业务流程：
 * 1. NFC 识别学生卡片
 * 2. 查询持卡人信息和余额/贷款状态
 * 3. 选择操作模式：仅还款 / 先还贷退卡 / 直接退余额
 * 4. 调用 API 执行操作
 */
class CardReturnViewModel(
    private val sessionManager: SessionManager,
) : ViewModel() {

    private val TAG = "CardReturnViewModel"
    private val apiService: WalletAPIService = APIClient.getAPIService()

    var uiState by mutableStateOf(CardReturnUiState())
        private set

    private var eventId: Int = -1

    fun init(eventId: Int) {
        this.eventId = eventId
    }

    // NFC 卡片检测
    fun onNfcCardDetected(uid: String) {
        if (uiState.isLoading || uiState.isSuccess) return

        uiState = CardReturnUiState(cardUid = uid, isLoadingInfo = true)
        lookupParticipant(uid)
    }

    // 查询持卡人信息
    private fun lookupParticipant(cardUid: String) {
        apiService.getParticipantByCard(cardUid).enqueue(object : Callback<ParticipantInfo> {
            override fun onResponse(call: Call<ParticipantInfo>, response: Response<ParticipantInfo>) {
                if (response.isSuccessful && response.body() != null) {
                    val participant = response.body()!!
                    uiState = uiState.copy(
                        participantName = participant.name,
                        participantId = participant.id,
                        className = participant.className,
                    )
                    // 继续查询余额
                    loadBalance(cardUid)
                } else {
                    uiState = uiState.copy(
                        isLoadingInfo = false,
                        errorMessage = "未找到该卡片对应的参与者",
                        cardUid = null,
                    )
                }
            }

            override fun onFailure(call: Call<ParticipantInfo>, t: Throwable) {
                Log.e(TAG, "查询持卡人失败", t)
                uiState = uiState.copy(
                    isLoadingInfo = false,
                    errorMessage = "网络错误：${t.message}",
                    cardUid = null,
                )
            }
        })
    }

    // 查询余额和贷款信息
    private fun loadBalance(cardUid: String) {
        // 先查余额
        apiService.getBalanceByEvent(eventId, cardUid).enqueue(object : Callback<BalanceResponse> {
            override fun onResponse(call: Call<BalanceResponse>, response: Response<BalanceResponse>) {
                val balance = if (response.isSuccessful && response.body() != null) {
                    response.body()!!.balance
                } else {
                    0.0
                }
                uiState = uiState.copy(balance = balance)
                // 查询贷款信息
                loadLoanInfo()
            }

            override fun onFailure(call: Call<BalanceResponse>, t: Throwable) {
                Log.e(TAG, "查询余额失败", t)
                uiState = uiState.copy(balance = 0.0)
                loadLoanInfo()
            }
        })
    }

    // 查询贷款信息
    private fun loadLoanInfo() {
        val token = sessionManager.authHeader ?: run {
            uiState = uiState.copy(isLoadingInfo = false)
            return
        }
        val participantId = uiState.participantId ?: run {
            uiState = uiState.copy(isLoadingInfo = false)
            return
        }

        // 使用 loans 接口查询该参与者的活跃贷款
        apiService.getParticipantLoans(token, eventId, uiState.cardUid ?: "")
            .enqueue(object : Callback<Map<String, Any>> {
                override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                    if (response.isSuccessful && response.body() != null) {
                        val data = response.body()!!
                        val loanCount = (data["loan_count"] as? Double)?.toInt() ?: 0
                        val loanTotal = (data["total_debt"] as? Double) ?: 0.0
                        uiState = uiState.copy(
                            isLoadingInfo = false,
                            loanAmount = loanTotal,
                            loanCount = loanCount,
                        )
                    } else {
                        uiState = uiState.copy(isLoadingInfo = false)
                    }
                }

                override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                    Log.e(TAG, "查询贷款信息失败", t)
                    uiState = uiState.copy(isLoadingInfo = false)
                }
            })
    }

    // 模式1: 余额先偿还贷款再退卡
    fun onReturnWithRepay() {
        executeReturn(repayLoanFirst = true)
    }

    // 模式2: 直接全额退还余额，贷款另行偿还
    fun onReturnWithoutRepay() {
        executeReturn(repayLoanFirst = false)
    }

    // 显示还款弹窗
    fun onShowRepayDialog() {
        val maxRepay = minOf(uiState.balance, uiState.loanAmount)
        uiState = uiState.copy(
            showRepayDialog = true,
            repayAmount = "%.0f".format(maxRepay),
        )
    }

    // 关闭还款弹窗
    fun onDismissRepayDialog() {
        uiState = uiState.copy(showRepayDialog = false, repayAmount = "")
    }

    // 还款金额变更
    fun onRepayAmountChange(value: String) {
        // 只允许数字和小数点
        val filtered = value.filter { it.isDigit() || it == '.' }
        uiState = uiState.copy(repayAmount = filtered)
    }

    // 仅还款（不退卡）
    fun onRepayOnly() {
        val cardUid = uiState.cardUid ?: return
        val token = sessionManager.authHeader ?: run {
            uiState = uiState.copy(errorMessage = "登录已过期，请重新登录")
            return
        }
        if (uiState.isLoading) return

        val amount = uiState.repayAmount.toDoubleOrNull()
        if (amount == null || amount <= 0) {
            uiState = uiState.copy(errorMessage = "请输入有效的还款金额")
            return
        }

        val maxRepay = minOf(uiState.balance, uiState.loanAmount)
        if (amount > maxRepay) {
            uiState = uiState.copy(errorMessage = "还款金额不能超过 ¥${"%.2f".format(maxRepay)}")
            return
        }

        uiState = uiState.copy(isLoading = true, showRepayDialog = false, errorMessage = null)

        val requestData = HashMap<String, Any>()
        requestData["event_id"] = eventId
        requestData["card_uid"] = cardUid
        requestData["amount"] = amount.toInt()
        requestData["remark"] = "还款+退卡终端操作还款"

        apiService.repayLoan(token, requestData).enqueue(object : Callback<Map<String, Any>> {
            override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!
                    val repaid = (result["repaid_amount"] as? Double) ?: amount
                    val remaining = (result["remaining_debt"] as? Double) ?: 0.0
                    val newBalance = (result["balance_after"] as? Double) ?: (uiState.balance - amount)

                    uiState = uiState.copy(
                        isLoading = false,
                        isSuccess = true,
                        resultLoanRepaid = repaid,
                        resultRemainingDebt = remaining,
                        resultNewBalance = newBalance,
                        resultMode = "repay_only",
                    )
                } else {
                    val errorMsg = APIClient.getErrorMessage(response) ?: "还款失败 (${response.code()})"
                    uiState = uiState.copy(isLoading = false, errorMessage = errorMsg)
                }
            }

            override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                Log.e(TAG, "还款请求失败", t)
                uiState = uiState.copy(isLoading = false, errorMessage = "网络错误: ${t.message}")
            }
        })
    }

    private fun executeReturn(repayLoanFirst: Boolean) {
        val cardUid = uiState.cardUid ?: return
        val token = sessionManager.authHeader ?: run {
            uiState = uiState.copy(errorMessage = "登录已过期，请重新登录")
            return
        }
        if (uiState.isLoading) return

        uiState = uiState.copy(isLoading = true, errorMessage = null)

        viewModelScope.launch(Dispatchers.IO) {
            try {
                val requestData = HashMap<String, Any>()
                requestData["event_id"] = eventId
                requestData["card_uid"] = cardUid
                requestData["refund_balance"] = true
                requestData["repay_loan_first"] = repayLoanFirst
                requestData["remark"] = if (repayLoanFirst) "退卡-余额偿还贷款后退还" else "退卡-直接退还余额"

                val result = suspendCancellableCoroutine<Map<String, Any>?> { continuation ->
                    val call = apiService.returnCard(token, requestData)
                    continuation.invokeOnCancellation { call.cancel() }

                    call.enqueue(object : Callback<Map<String, Any>> {
                        override fun onResponse(
                            call: Call<Map<String, Any>>,
                            response: Response<Map<String, Any>>
                        ) {
                            if (response.isSuccessful && response.body() != null) {
                                continuation.resume(response.body())
                            } else {
                                val errorMsg = APIClient.getErrorMessage(response)
                                    ?: "退卡失败 (${response.code()})"
                                uiState = uiState.copy(
                                    isLoading = false,
                                    errorMessage = errorMsg,
                                )
                                continuation.resume(null)
                            }
                        }

                        override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                            Log.e(TAG, "退卡请求失败", t)
                            uiState = uiState.copy(
                                isLoading = false,
                                errorMessage = "网络错误: ${t.message}",
                            )
                            continuation.resume(null)
                        }
                    })
                }

                if (result != null) {
                    val refunded = (result["balance_refunded"] as? Double) ?: 0.0
                    val loanRepaid = (result["loan_repaid"] as? Double) ?: 0.0
                    val remainingDebt = (result["remaining_debt"] as? Double) ?: 0.0

                    uiState = uiState.copy(
                        isLoading = false,
                        isSuccess = true,
                        resultRefunded = refunded,
                        resultLoanRepaid = loanRepaid,
                        resultRemainingDebt = remainingDebt,
                        resultMode = if (repayLoanFirst) "repay_first" else "direct_refund",
                    )
                }
            } catch (e: Exception) {
                Log.e(TAG, "退卡异常", e)
                uiState = uiState.copy(
                    isLoading = false,
                    errorMessage = "系统异常：${e.message}",
                )
            }
        }
    }

    fun onReset() {
        uiState = CardReturnUiState()
    }

    fun onDismissError() {
        uiState = uiState.copy(errorMessage = null)
    }
}
