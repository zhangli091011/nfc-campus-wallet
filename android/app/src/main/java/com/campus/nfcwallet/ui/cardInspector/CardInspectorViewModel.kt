package com.campus.nfcwallet.ui.cardInspector

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
 * 刷卡查询终端 ViewModel
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

    var uiState by mutableStateOf(CardInspectorUiState())
        private set

    private var eventId: Int = -1

    fun init(eventId: Int) {
        this.eventId = eventId
    }

    fun onNfcCardDetected(uid: String) {
        if (uiState.isLoading) return

        uiState = CardInspectorUiState(cardUid = uid, isLoading = true)
        loadCardDetail(uid)
    }

    private fun loadCardDetail(cardUid: String) {
        val eid = if (eventId > 0) eventId else null

        apiService.getCardDetail(cardUid, eid).enqueue(object : Callback<Map<String, Any>> {
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
            val participant = data["participant"] as? Map<String, Any>
            val participantInfo = if (participant != null) {
                ParticipantDetail(
                    id = (participant["id"] as? Double)?.toInt() ?: 0,
                    name = participant["name"] as? String ?: "-",
                    cardUid = participant["card_uid"] as? String ?: "-",
                    className = participant["class_name"] as? String,
                    studentNo = participant["student_no"] as? String,
                    status = participant["status"] as? String ?: "unknown",
                    createdAt = participant["created_at"] as? String,
                )
            } else null

            // 解析账户信息
            val account = data["account"] as? Map<String, Any>
            val accountInfo = if (account != null) {
                AccountDetail(
                    balance = (account["balance"] as? Double) ?: 0.0,
                    creditBorrowed = (account["credit_borrowed"] as? Double) ?: 0.0,
                    creditFeePaid = (account["credit_fee_paid"] as? Double) ?: 0.0,
                )
            } else null

            // 解析贷款信息
            val loans = data["loans"] as? Map<String, Any>
            val loanInfo = if (loans != null) {
                LoanDetail(
                    activeCount = (loans["active_count"] as? Double)?.toInt() ?: 0,
                    totalDebt = (loans["total_debt"] as? Double) ?: 0.0,
                )
            } else null

            // 解析股票持仓
            val stockList = data["stock_holdings"] as? List<Map<String, Any>> ?: emptyList()
            val stockHoldings = stockList.map { item ->
                StockHoldingDetail(
                    boothId = (item["booth_id"] as? Double)?.toInt() ?: 0,
                    boothName = item["booth_name"] as? String ?: "-",
                    shares = (item["shares"] as? Double)?.toInt() ?: 0,
                    totalCost = (item["total_cost"] as? Double) ?: 0.0,
                )
            }

            // 解析交易流水
            val txnList = data["transactions"] as? List<Map<String, Any>> ?: emptyList()
            val transactions = txnList.map { item ->
                TransactionDetail(
                    id = (item["id"] as? Double)?.toInt() ?: 0,
                    type = item["type"] as? String ?: "unknown",
                    amount = (item["amount"] as? Double) ?: 0.0,
                    balanceBefore = (item["balance_before"] as? Double) ?: 0.0,
                    balanceAfter = (item["balance_after"] as? Double) ?: 0.0,
                    remark = item["remark"] as? String,
                    boothId = (item["booth_id"] as? Double)?.toInt(),
                    createdAt = item["created_at"] as? String,
                )
            }

            uiState = uiState.copy(
                isLoading = false,
                participant = participantInfo,
                account = accountInfo,
                loan = loanInfo,
                stockHoldings = stockHoldings,
                transactions = transactions,
            )
        } catch (e: Exception) {
            Log.e(TAG, "解析数据失败", e)
            uiState = uiState.copy(isLoading = false, errorMessage = "数据解析失败: ${e.message}")
        }
    }

    fun onReset() {
        uiState = CardInspectorUiState()
    }

    fun onDismissError() {
        uiState = uiState.copy(errorMessage = null)
    }
}
