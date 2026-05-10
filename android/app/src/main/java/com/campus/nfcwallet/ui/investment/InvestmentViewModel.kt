package com.campus.nfcwallet.ui.investment

import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.campus.nfcwallet.api.APIClient
import com.campus.nfcwallet.api.WalletAPIService
import com.campus.nfcwallet.models.BalanceResponse
import com.campus.nfcwallet.models.BoothInfo
import com.campus.nfcwallet.models.ParticipantInfo
import com.campus.nfcwallet.models.StockBuyRequest
import com.campus.nfcwallet.models.StockBuyResponse
import com.campus.nfcwallet.utils.SessionManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

/**
 * 投资办理 ViewModel
 *
 * 简化版：直接从主账户余额购买股票，不再有独立投资币账户。
 * 所有金额以"元"为单位。
 */
class InvestmentViewModel(
    private val sessionManager: SessionManager,
) : ViewModel() {

    private val TAG = "InvestmentViewModel"
    private val apiService: WalletAPIService = APIClient.getAPIService()

    var uiState by mutableStateOf(InvestmentUiState())
        private set

    private var currentParticipant: ParticipantInfo? = null
    private var eventId: Int = -1

    fun init(eventId: Int) {
        this.eventId = eventId
        loadBooths()
    }

    // -------------------------------------------------------------
    // 加载可投资摊位（排除"官方中央银行"本身）
    // -------------------------------------------------------------
    private fun loadBooths() {
        val token = sessionManager.authHeader ?: return
        apiService.getBooths(token, "active").enqueue(object : Callback<List<BoothInfo>> {
            override fun onResponse(
                call: Call<List<BoothInfo>>,
                response: Response<List<BoothInfo>>,
            ) {
                if (response.isSuccessful && response.body() != null) {
                    val booths = response.body()!!
                        .filter { it.name != "官方中央银行" && it.isActive }
                        .map { BoothOption(it.id, it.name, it.className ?: "") }
                    uiState = uiState.copy(booths = booths)
                }
            }

            override fun onFailure(call: Call<List<BoothInfo>>, t: Throwable) {
                Log.e(TAG, "加载摊位失败", t)
                uiState = uiState.copy(errorMessage = "加载摊位失败: ${t.message}")
            }
        })
    }

    // -------------------------------------------------------------
    // NFC 卡被检测
    // -------------------------------------------------------------
    fun onNfcCardDetected(uid: String) {
        if (uiState.isLoading) return
        uiState = uiState.copy(
            cardUid = uid,
            isLoading = true,
            errorMessage = null,
        )

        apiService.getParticipantByCard(uid).enqueue(object : Callback<ParticipantInfo> {
            override fun onResponse(
                call: Call<ParticipantInfo>,
                response: Response<ParticipantInfo>,
            ) {
                if (response.isSuccessful && response.body() != null) {
                    currentParticipant = response.body()
                    uiState = uiState.copy(
                        participantName = "${currentParticipant!!.name} (${currentParticipant!!.className ?: "-"})",
                    )
                    loadBalance(uid)
                } else {
                    uiState = uiState.copy(
                        isLoading = false,
                        cardUid = null,
                        errorMessage = "该卡未注册或无效",
                    )
                }
            }

            override fun onFailure(call: Call<ParticipantInfo>, t: Throwable) {
                Log.e(TAG, "查询参与者失败", t)
                uiState = uiState.copy(
                    isLoading = false,
                    cardUid = null,
                    errorMessage = "网络错误: ${t.message}",
                )
            }
        })
    }

    private fun loadBalance(uid: String) {
        apiService.getBalanceByEvent(eventId, uid).enqueue(object : Callback<BalanceResponse> {
            override fun onResponse(
                call: Call<BalanceResponse>,
                response: Response<BalanceResponse>,
            ) {
                uiState = if (response.isSuccessful && response.body() != null) {
                    val balance = response.body()!!.balance
                    uiState.copy(
                        accountBalance = balance,
                        isLoading = false,
                    )
                } else {
                    uiState.copy(
                        isLoading = false,
                        errorMessage = "该参与者未开通此活动账户",
                    )
                }
            }

            override fun onFailure(call: Call<BalanceResponse>, t: Throwable) {
                Log.e(TAG, "查询余额失败", t)
                uiState = uiState.copy(
                    isLoading = false,
                    errorMessage = "查询余额失败: ${t.message}",
                )
            }
        })
    }

    // -------------------------------------------------------------
    // 表单变更
    // -------------------------------------------------------------
    fun onBoothSelected(booth: BoothOption) {
        uiState = uiState.copy(selectedBooth = booth)
    }

    fun onSharesChanged(shares: String) {
        uiState = uiState.copy(sharesInput = shares)
    }

    fun onDismissMessage() {
        uiState = uiState.copy(errorMessage = null, successMessage = null)
    }

    // -------------------------------------------------------------
    // 确认投资：直接从主账户购买股票
    // -------------------------------------------------------------
    fun onConfirmInvestment() {
        val uid = uiState.cardUid ?: return
        val booth = uiState.selectedBooth ?: return
        val shares = uiState.sharesInput.toIntOrNull() ?: return
        if (shares <= 0) return

        val totalYuan = shares * 10.0

        // 余额校验
        if (uiState.accountBalance < totalYuan) {
            uiState = uiState.copy(errorMessage = "账户余额不足，需要¥%.2f，当前¥%.2f".format(totalYuan, uiState.accountBalance))
            return
        }

        uiState = uiState.copy(isLoading = true, errorMessage = null)

        viewModelScope.launch(Dispatchers.IO) {
            performBuyStock(uid, booth.id, shares)
        }
    }

    private fun performBuyStock(uid: String, boothId: Int, shares: Int) {
        val token = sessionManager.authHeader ?: run {
            uiState = uiState.copy(isLoading = false, errorMessage = "登录已过期，请重新登录")
            return
        }
        val request = StockBuyRequest(uid, eventId, boothId, shares)
        apiService.buyStock(token, request).enqueue(object : Callback<StockBuyResponse> {
            override fun onResponse(call: Call<StockBuyResponse>, response: Response<StockBuyResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val body = response.body()!!
                    uiState = uiState.copy(
                        isLoading = false,
                        accountBalance = body.newBalanceYuan,
                        sharesInput = "",
                        selectedBooth = null,
                        successMessage = "✓ 投资成功：${body.boothName} ${body.shares}股，扣款¥%.2f".format(body.totalAmountYuan),
                    )
                } else {
                    uiState = uiState.copy(
                        isLoading = false,
                        errorMessage = "购买失败: ${APIClient.getErrorMessage(response)}",
                    )
                }
            }

            override fun onFailure(call: Call<StockBuyResponse>, t: Throwable) {
                Log.e(TAG, "购买股票失败", t)
                uiState = uiState.copy(isLoading = false, errorMessage = "网络错误: ${t.message}")
            }
        })
    }
}
