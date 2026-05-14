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
import com.campus.nfcwallet.models.StockHoldingInfo
import com.campus.nfcwallet.models.StockSellRequest
import com.campus.nfcwallet.models.StockSellResponse
import com.campus.nfcwallet.utils.SessionManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

/**
 * 投资办理 ViewModel
 *
 * 支持买入和卖出股票。
 * 买入：直接从主账户余额购买股票。
 * 卖出：以当前股价抛售持仓，资金返回主账户。
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
    
    // 动态股价缓存 (booth_id -> price)
    private var dynamicPrices: Map<Int, Double> = emptyMap()
    private var priceRefreshJob: kotlinx.coroutines.Job? = null

    fun init(eventId: Int) {
        this.eventId = eventId
        loadBooths()
        startPriceRefresh()
    }
    
    override fun onCleared() {
        super.onCleared()
        priceRefreshJob?.cancel()
    }
    
    // -------------------------------------------------------------
    // 定时刷新股价（每15秒）
    // -------------------------------------------------------------
    private fun startPriceRefresh() {
        priceRefreshJob?.cancel()
        priceRefreshJob = viewModelScope.launch(Dispatchers.IO) {
            while (true) {
                loadDynamicPrices()
                delay(15_000L)
            }
        }
    }
    
    private fun loadDynamicPrices() {
        try {
            val response = apiService.getStockPrices(eventId).execute()
            if (response.isSuccessful && response.body() != null) {
                val priceList = response.body()!!
                val priceMap = mutableMapOf<Int, Double>()
                for (item in priceList) {
                    val boothId = (item["booth_id"] as? Number)?.toInt() ?: continue
                    val price = (item["current_price"] as? Number)?.toDouble() ?: 5.0
                    priceMap[boothId] = price
                }
                dynamicPrices = priceMap
                
                // 更新持仓中的当前股价
                if (uiState.holdings.isNotEmpty()) {
                    val updatedHoldings = uiState.holdings.map { h ->
                        val newPrice = dynamicPrices[h.boothId] ?: h.currentPrice
                        h.copy(currentPrice = newPrice, marketValue = newPrice * h.shares)
                    }
                    uiState = uiState.copy(holdings = updatedHoldings)
                }
            }
        } catch (e: Exception) {
            Log.w(TAG, "刷新股价失败: ${e.message}")
        }
    }
    
    fun getCurrentPrice(boothId: Int): Double {
        return dynamicPrices[boothId] ?: 5.0
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
                    if (!currentParticipant!!.isVerified) {
                        // 未实名：弹出实名认证对话框
                        uiState = uiState.copy(
                            isLoading = false,
                            showVerificationDialog = true,
                            verificationParticipantId = currentParticipant!!.id,
                        )
                        return
                    }
                    uiState = uiState.copy(
                        participantName = "${currentParticipant!!.name} (${currentParticipant!!.className ?: "-"})",
                    )
                    loadBalance(uid)
                    loadHoldings(uid)
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
    // 加载持仓信息
    // -------------------------------------------------------------
    private fun loadHoldings(uid: String) {
        val token = sessionManager.authHeader ?: return
        apiService.getStockHoldingsByCard(token, uid, eventId).enqueue(object : Callback<List<StockHoldingInfo>> {
            override fun onResponse(
                call: Call<List<StockHoldingInfo>>,
                response: Response<List<StockHoldingInfo>>,
            ) {
                if (response.isSuccessful && response.body() != null) {
                    val holdings = response.body()!!.map {
                        HoldingInfo(
                            boothId = it.boothId,
                            boothName = it.boothName,
                            className = it.className ?: "",
                            shares = it.shares,
                            currentPrice = it.currentPrice,
                            marketValue = it.marketValue,
                        )
                    }
                    uiState = uiState.copy(holdings = holdings)
                }
            }

            override fun onFailure(call: Call<List<StockHoldingInfo>>, t: Throwable) {
                Log.e(TAG, "加载持仓失败", t)
                // 非关键错误，不阻塞流程
            }
        })
    }

    // -------------------------------------------------------------
    // Tab 切换
    // -------------------------------------------------------------
    fun onTabChanged(tab: Int) {
        uiState = uiState.copy(currentTab = tab)
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

    fun onHoldingSelected(holding: HoldingInfo) {
        uiState = uiState.copy(selectedHolding = holding, sellSharesInput = "")
    }

    fun onSellSharesChanged(shares: String) {
        uiState = uiState.copy(sellSharesInput = shares)
    }

    fun onDismissMessage() {
        uiState = uiState.copy(errorMessage = null, successMessage = null)
    }

    // -------------------------------------------------------------
    // 实名认证
    // -------------------------------------------------------------
    fun onDismissVerificationDialog() {
        uiState = uiState.copy(
            showVerificationDialog = false,
            verificationParticipantId = null,
            cardUid = null,
            isLoading = false,
        )
        currentParticipant = null
    }

    fun onSubmitVerification(name: String, className: String) {
        val participantId = uiState.verificationParticipantId ?: return
        val token = sessionManager.authHeader ?: return
        val uid = uiState.cardUid ?: return

        uiState = uiState.copy(showVerificationDialog = false, isLoading = true)

        val updateData = HashMap<String, Any>()
        updateData["name"] = name
        if (className.isNotBlank()) {
            updateData["class_name"] = className
        }

        apiService.updateParticipant(token, participantId, updateData)
            .enqueue(object : Callback<ParticipantInfo> {
                override fun onResponse(call: Call<ParticipantInfo>, response: Response<ParticipantInfo>) {
                    if (response.isSuccessful && response.body() != null) {
                        currentParticipant = response.body()
                        uiState = uiState.copy(
                            participantName = "${currentParticipant!!.name} (${currentParticipant!!.className ?: "-"})",
                            verificationParticipantId = null,
                        )
                        loadBalance(uid)
                        loadHoldings(uid)
                    } else {
                        uiState = uiState.copy(
                            isLoading = false,
                            errorMessage = "实名认证失败: ${APIClient.getErrorMessage(response)}",
                        )
                    }
                }

                override fun onFailure(call: Call<ParticipantInfo>, t: Throwable) {
                    Log.e(TAG, "实名认证请求失败", t)
                    uiState = uiState.copy(
                        isLoading = false,
                        errorMessage = "网络错误: ${t.message}",
                    )
                }
            })
    }

    // -------------------------------------------------------------
    // 确认投资：以当前动态股价从主账户购买股票
    // -------------------------------------------------------------
    fun onConfirmInvestment() {
        val uid = uiState.cardUid ?: return
        val booth = uiState.selectedBooth ?: return
        val shares = uiState.sharesInput.toIntOrNull() ?: return
        if (shares <= 0) return

        // 浮动买入价 = 当前动态股价
        val pricePerShare = getCurrentPrice(booth.id)
        val totalYuan = shares * pricePerShare

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
                    // 刷新持仓
                    loadHoldings(uid)
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

    // -------------------------------------------------------------
    // 确认抛售：以当前股价卖出
    // -------------------------------------------------------------
    fun onConfirmSell() {
        val uid = uiState.cardUid ?: return
        val holding = uiState.selectedHolding ?: return
        val shares = uiState.sellSharesInput.toIntOrNull() ?: return
        if (shares <= 0) return

        if (shares > holding.shares) {
            uiState = uiState.copy(errorMessage = "卖出股数不能超过持仓数量(${holding.shares}股)")
            return
        }

        uiState = uiState.copy(isLoading = true, errorMessage = null)

        viewModelScope.launch(Dispatchers.IO) {
            performSellStock(uid, holding.boothId, shares)
        }
    }

    private fun performSellStock(uid: String, boothId: Int, shares: Int) {
        val token = sessionManager.authHeader ?: run {
            uiState = uiState.copy(isLoading = false, errorMessage = "登录已过期，请重新登录")
            return
        }
        val request = StockSellRequest(uid, eventId, boothId, shares)
        apiService.sellStock(token, request).enqueue(object : Callback<StockSellResponse> {
            override fun onResponse(call: Call<StockSellResponse>, response: Response<StockSellResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val body = response.body()!!
                    uiState = uiState.copy(
                        isLoading = false,
                        accountBalance = body.newBalanceYuan,
                        sellSharesInput = "",
                        selectedHolding = null,
                        successMessage = "✓ 抛售成功：${body.boothName} ${body.sharesSold}股，到账¥%.2f".format(body.totalAmountYuan),
                    )
                    // 刷新持仓
                    loadHoldings(uid)
                } else {
                    uiState = uiState.copy(
                        isLoading = false,
                        errorMessage = "抛售失败: ${APIClient.getErrorMessage(response)}",
                    )
                }
            }

            override fun onFailure(call: Call<StockSellResponse>, t: Throwable) {
                Log.e(TAG, "抛售股票失败", t)
                uiState = uiState.copy(isLoading = false, errorMessage = "网络错误: ${t.message}")
            }
        })
    }
}
