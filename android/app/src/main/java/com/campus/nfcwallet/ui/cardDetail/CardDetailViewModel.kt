package com.campus.nfcwallet.ui.cardDetail

import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import com.campus.nfcwallet.api.APIClient
import com.campus.nfcwallet.api.WalletAPIService
import com.campus.nfcwallet.utils.SessionManager
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

/**
 * 刷卡查看用户明细 ViewModel
 *
 * 管理流程：
 * 1. NFC 识别学生卡片
 * 2. 调用 /card-detail/{card_uid} 获取全部信息
 * 3. 展示在 UI 上
 */
class CardDetailViewModel(
    private val sessionManager: SessionManager,
) : ViewModel() {

    private val TAG = "CardDetailViewModel"
    private val apiService: WalletAPIService = APIClient.getAPIService()

    var uiState by mutableStateOf(CardDetailUiState())
        private set

    private var eventId: Int = -1

    fun init(eventId: Int) {
        this.eventId = eventId
    }

    fun onNfcCardDetected(uid: String) {
        // 允许重复刷卡查看不同用户
        uiState = CardDetailUiState(cardUid = uid, isLoading = true)
        loadCardDetail(uid)
    }

    private fun loadCardDetail(cardUid: String) {
        val token = sessionManager.authHeader ?: run {
            uiState = uiState.copy(isLoading = false, errorMessage = "登录已过期，请重新登录")
            return
        }

        apiService.getCardDetail(token, cardUid, eventId, 50)
            .enqueue(object : Callback<Map<String, Any>> {
                override fun onResponse(
                    call: Call<Map<String, Any>>,
                    response: Response<Map<String, Any>>
                ) {
                    if (response.isSuccessful && response.body() != null) {
                        parseResponse(response.body()!!)
                    } else {
                        val errorMsg = APIClient.getErrorMessage(response) ?: "查询失败 (${response.code()})"
                        uiState = uiState.copy(isLoading = false, errorMessage = errorMsg)
                    }
                }

                override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                    Log.e(TAG, "查询卡片明细失败", t)
                    uiState = uiState.copy(isLoading = false, errorMessage = "网络错误: ${t.message}")
                }
            })
    }

    @Suppress("UNCHECKED_CAST")
    private fun parseResponse(data: Map<String, Any>) {
        try {
            // 解析参与者信息
            val participant = data["participant"] as? Map<String, Any> ?: emptyMap()
            val account = data["account"] as? Map<String, Any> ?: emptyMap()
            val loans = data["loans"] as? Map<String, Any> ?: emptyMap()
            val stockHoldings = data["stock_holdings"] as? List<Map<String, Any>> ?: emptyList()
            val transactions = data["transactions"] as? List<Map<String, Any>> ?: emptyList()

            val participantInfo = ParticipantDetail(
                id = (participant["id"] as? Double)?.toInt() ?: 0,
                name = participant["name"] as? String ?: "-",
                cardUid = participant["card_uid"] as? String ?: "-",
                className = participant["class_name"] as? String,
                studentNo = participant["student_no"] as? String,
                status = participant["status"] as? String ?: "unknown",
                createdAt = participant["created_at"] as? String,
            )

            val accountInfo = AccountDetail(
                balance = (account["balance"] as? Double) ?: 0.0,
                creditBorrowed = (account["credit_borrowed"] as? Double) ?: 0.0,
                creditFeePaid = (account["credit_fee_paid"] as? Double) ?: 0.0,
            )

            val loanInfo = LoanSummary(
                activeCount = (loans["active_count"] as? Double)?.toInt() ?: 0,
                totalDebt = (loans["total_debt"] as? Double) ?: 0.0,
            )

            val holdings = stockHoldings.map { h ->
                StockHoldingDetail(
                    boothId = (h["booth_id"] as? Double)?.toInt() ?: 0,
                    boothName = h["booth_name"] as? String ?: "-",
                    shares = (h["shares"] as? Double)?.toInt() ?: 0,
                    totalInvested = (h["total_invested"] as? Double) ?: 0.0,
                )
            }

            val txnList = transactions.map { t ->
                TransactionDetail(
                    id = (t["id"] as? Double)?.toInt() ?: 0,
                    type = t["type"] as? String ?: "unknown",
                    amount = (t["amount"] as? Double) ?: 0.0,
                    balanceBefore = t["balance_before"] as? Double,
                    balanceAfter = t["balance_after"] as? Double,
                    remark = t["remark"] as? String,
                    createdAt = t["created_at"] as? String,
                )
            }

            uiState = uiState.copy(
                isLoading = false,
                participant = participantInfo,
                account = accountInfo,
                loans = loanInfo,
                stockHoldings = holdings,
                transactions = txnList,
            )
        } catch (e: Exception) {
            Log.e(TAG, "解析响应失败", e)
            uiState = uiState.copy(isLoading = false, errorMessage = "数据解析失败: ${e.message}")
        }
    }

    fun onReset() {
        uiState = CardDetailUiState()
    }

    fun onDismissError() {
        uiState = uiState.copy(errorMessage = null)
    }
}
