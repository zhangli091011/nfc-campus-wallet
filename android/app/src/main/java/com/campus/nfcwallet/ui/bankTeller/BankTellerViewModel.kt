package com.campus.nfcwallet.ui.bankTeller

import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.campus.nfcwallet.api.APIClient
import com.campus.nfcwallet.api.WalletAPIService
import com.campus.nfcwallet.models.LoanIssuanceRequest
import com.campus.nfcwallet.models.LoanIssuanceResponse
import com.campus.nfcwallet.models.ParticipantInfo
import com.campus.nfcwallet.signature.SignatureGenerator
import com.campus.nfcwallet.utils.SessionManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import kotlin.coroutines.resume

/**
 * 银行柜员操作终端 ViewModel
 *
 * 管理信用垫资发行的完整业务流程：
 * 1. NFC 识别学生卡片
 * 2. 查询持卡人信息
 * 3. 选择放款金额（预设面额）
 * 4. 确认纸质承诺书签署
 * 5. 调用 API 发行信用额度
 */
class BankTellerViewModel(
    private val sessionManager: SessionManager,
) : ViewModel() {

    private val TAG = "BankTellerViewModel"
    private val apiService: WalletAPIService = APIClient.getAPIService()

    var uiState by mutableStateOf(BankTellerUiState())
        private set

    private var eventId: Int = -1

    fun init(eventId: Int) {
        this.eventId = eventId
    }

    // -----------------------------------------------------------------
    // NFC 卡片检测回调
    // -----------------------------------------------------------------
    fun onNfcCardDetected(uid: String) {
        if (uiState.isLoading || uiState.isSuccess) return

        uiState = uiState.copy(
            cardUid = uid,
            participantName = null,
            participantId = null,
            selectedAmount = null,
            paperworkConfirmed = false,
            isSuccess = false,
            errorMessage = null,
        )

        // 查询持卡人信息
        lookupParticipant(uid)
    }

    // -----------------------------------------------------------------
    // 查询持卡人
    // -----------------------------------------------------------------
    private fun lookupParticipant(cardUid: String) {
        apiService.getParticipantByCard(cardUid).enqueue(object : Callback<ParticipantInfo> {
            override fun onResponse(
                call: Call<ParticipantInfo>,
                response: Response<ParticipantInfo>,
            ) {
                if (response.isSuccessful && response.body() != null) {
                    val participant = response.body()!!
                    if (participant.isBlocked) {
                        uiState = uiState.copy(
                            errorMessage = "该卡片已被冻结，无法办理信用垫资",
                            cardUid = null,
                        )
                        return
                    }
                    if (!participant.isVerified) {
                        uiState = uiState.copy(
                            errorMessage = "该卡片持有者未完成实名认证（需填写班级或学号），无法办理信用垫资",
                            cardUid = null,
                        )
                        return
                    }
                    uiState = uiState.copy(
                        participantName = participant.name,
                        participantId = participant.id,
                    )
                } else {
                    uiState = uiState.copy(
                        errorMessage = "未找到该卡片对应的学生信息 (UID: $cardUid)",
                        cardUid = null,
                    )
                }
            }

            override fun onFailure(call: Call<ParticipantInfo>, t: Throwable) {
                Log.e(TAG, "查询持卡人失败", t)
                uiState = uiState.copy(
                    errorMessage = "网络错误：${t.message}",
                    cardUid = null,
                )
            }
        })
    }

    // -----------------------------------------------------------------
    // 选择放款金额
    // -----------------------------------------------------------------
    fun onAmountSelected(amount: Int) {
        uiState = uiState.copy(selectedAmount = amount)
    }

    // -----------------------------------------------------------------
    // 纸质承诺书确认
    // -----------------------------------------------------------------
    fun onPaperworkChecked(checked: Boolean) {
        uiState = uiState.copy(paperworkConfirmed = checked)
    }

    // -----------------------------------------------------------------
    // 确认发行信用额度
    // -----------------------------------------------------------------
    fun onConfirmIssuance() {
        val cardUid = uiState.cardUid ?: return
        val amount = uiState.selectedAmount ?: return
        if (!uiState.paperworkConfirmed) return
        if (uiState.isLoading) return

        uiState = uiState.copy(isLoading = true, errorMessage = null)

        viewModelScope.launch(Dispatchers.IO) {
            try {
                val result = issueLoan(cardUid, amount)
                if (result != null && result.isSuccess) {
                    uiState = uiState.copy(
                        isLoading = false,
                        isSuccess = true,
                        resultDisbursedAmount = result.disbursedAmount,
                        resultNewBalance = result.newBalance,
                    )
                } else {
                    uiState = uiState.copy(
                        isLoading = false,
                        errorMessage = result?.message ?: "发行失败，请重试",
                    )
                }
            } catch (e: Exception) {
                Log.e(TAG, "发行信用额度异常", e)
                uiState = uiState.copy(
                    isLoading = false,
                    errorMessage = "系统异常：${e.message}",
                )
            }
        }
    }

    // -----------------------------------------------------------------
    // 调用后端 API
    // -----------------------------------------------------------------
    private suspend fun issueLoan(cardUid: String, principalAmount: Int): LoanIssuanceResponse? {
        val token = sessionManager.authHeader ?: run {
            uiState = uiState.copy(
                isLoading = false,
                errorMessage = "登录已过期，请重新登录",
            )
            return null
        }

        val timestamp = System.currentTimeMillis() / 1000
        val signature = SignatureGenerator.generateTransactionSignature(
            cardUid,
            principalAmount.toDouble(),
            timestamp,
            "your_secret_key_here", // TODO: 从配置读取
        )

        val request = LoanIssuanceRequest(
            cardUid,
            principalAmount,
            eventId,
            timestamp,
            signature,
        )

        return suspendCancellableCoroutine { continuation ->
            val call = apiService.issueLoan(token, request)
            continuation.invokeOnCancellation { call.cancel() }

            call.enqueue(object : Callback<LoanIssuanceResponse> {
                override fun onResponse(
                    call: Call<LoanIssuanceResponse>,
                    response: Response<LoanIssuanceResponse>,
                ) {
                    if (response.isSuccessful && response.body() != null) {
                        continuation.resume(response.body())
                    } else {
                        val errorMsg = APIClient.getErrorMessage(response)
                            ?: "服务器返回错误 (${response.code()})"
                        uiState = uiState.copy(
                            isLoading = false,
                            errorMessage = errorMsg,
                        )
                        continuation.resume(null)
                    }
                }

                override fun onFailure(call: Call<LoanIssuanceResponse>, t: Throwable) {
                    Log.e(TAG, "API 调用失败", t)
                    continuation.resume(null)
                }
            })
        }
    }

    // -----------------------------------------------------------------
    // 重置状态（办理下一笔）
    // -----------------------------------------------------------------
    fun onReset() {
        uiState = BankTellerUiState()
    }

    // -----------------------------------------------------------------
    // 关闭错误提示
    // -----------------------------------------------------------------
    fun onDismissError() {
        uiState = uiState.copy(errorMessage = null)
    }
}
