package com.campus.nfcwallet.ui.cardInspector

import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import com.campus.nfcwallet.api.APIClient
import com.campus.nfcwallet.api.WalletAPIService
import com.campus.nfcwallet.ui.cardDetail.AccountDetail
import com.campus.nfcwallet.ui.cardDetail.CardDetailUiState
import com.campus.nfcwallet.ui.cardDetail.LoanSummary
import com.campus.nfcwallet.ui.cardDetail.ParticipantDetail
import com.campus.nfcwallet.ui.cardDetail.StockHoldingDetail
import com.campus.nfcwallet.ui.cardDetail.TransactionDetail
import com.campus.nfcwallet.utils.SessionManager
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

/**
 * 刷卡查询终端 ViewModel（校方巡查用）
 *
 * 通过 NFC 识别卡片后，调用后端接口获取持卡人完整明细：
 * - 基本信息（姓名、班级、学号、状态）
 * - 账户余额
 * - 贷款信息
 * - 股票持仓
 * - 最近交易流水
 */
class CardInspectorViewModel(
    private val sessionManager: SessionManager,
) : ViewModel() {

    private val TAG = "CardInspectorVM"
    private val apiService: WalletAPIService = APIClient.getAPIService()

    var uiState by mutableStateOf(CardDetailUiState())
        private set

    private var eventId: Int = -1

    fun init(eventId: Int) {
        this.eventId = eventId
    }

    fun onNfcCardDetected(uid: String) {
        if (uiState.isLoading) return

        uiState = CardDetailUiState(cardUid = uid, isLoading = true)
        loadCardDetail(uid)
    }

    private fun loadCardDetail(cardUid: String) {
        val token = sessionManager.authHeader ?: run {
            uiState = uiState.copy(isLoading = false, errorMessage = "登录已过期，请重新登录")
            return
        }
        val eid = if (eventId > 0) eventId else 0
        val txnLimit = 50

        apiService.getCardDetail(token, cardUid, eid, txnLimit).enqueue(object : Callback<Map<String, Any>> {
            override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                if (response.isSuccessful && response.body() != null) {
                    val data = response.body()!!
                    parseCardDetail(data)
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
    private fun parseCardDetail(data: Map<String, Any>) {
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
            Log.e(TAG, "解析数据失败", e)
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
