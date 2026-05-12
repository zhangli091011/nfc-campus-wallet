package com.campus.nfcwallet.ui.refund

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.nfc.NfcAdapter
import android.nfc.Tag
import android.os.Build
import android.os.Bundle
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.campus.nfcwallet.ui.LoginActivity
import com.campus.nfcwallet.utils.SessionManager

/**
 * 退款管理终端 Activity
 *
 * 收银端退款管理界面，支持：
 * - 查看本摊位最近交易流水
 * - NFC 贴卡查询该卡在本摊位的历史订单
 * - 选择订单发起退款（需管理员授权码）
 */
class RefundManagerActivity : ComponentActivity() {

    private lateinit var sessionManager: SessionManager
    private var nfcAdapter: NfcAdapter? = null
    private var pendingIntent: PendingIntent? = null
    private var intentFilters: Array<IntentFilter>? = null

    private val viewModel: RefundManagerViewModel by viewModels {
        object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return RefundManagerViewModel(
                    sessionManager = SessionManager(this@RefundManagerActivity),
                    onRefundSuccess = { vibrateOnRefundSuccess() },
                ) as T
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        sessionManager = SessionManager(this)

        if (!sessionManager.isLoggedIn) {
            navigateToLogin()
            return
        }

        val boothId = intent.getIntExtra("booth_id", sessionManager.userInfo?.boothId ?: -1)
        if (boothId <= 0) {
            Toast.makeText(this, "未找到摊位信息", Toast.LENGTH_SHORT).show()
            finish()
            return
        }

        viewModel.init(boothId)
        initializeNFC()

        setContent {
            androidx.compose.foundation.layout.Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(RefundColors.Background),
            ) {
                RefundManagerScreen(
                    state = viewModel.uiState,
                    onTransactionSelected = viewModel::selectTransaction,
                    onInitiateRefund = viewModel::showRefundConfirmation,
                    onConfirmRefund = viewModel::confirmRefund,
                    onDismissRefundDialog = viewModel::dismissRefundDialog,
                    onClearCardFilter = viewModel::clearCardFilter,
                    onClearSelection = viewModel::clearSelection,
                    onDismissError = viewModel::dismissError,
                    onDismissSuccess = viewModel::dismissSuccess,
                    onLogout = { logout() },
                )
            }
        }
    }

    // -----------------------------------------------------------------
    // NFC 初始化
    // -----------------------------------------------------------------
    private fun initializeNFC() {
        nfcAdapter = NfcAdapter.getDefaultAdapter(this)
        if (nfcAdapter == null) {
            Toast.makeText(this, "设备不支持 NFC", Toast.LENGTH_SHORT).show()
            return
        }

        pendingIntent = PendingIntent.getActivity(
            this, 0,
            Intent(this, javaClass).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP),
            PendingIntent.FLAG_MUTABLE,
        )

        val techFilter = IntentFilter(NfcAdapter.ACTION_TECH_DISCOVERED)
        intentFilters = arrayOf(techFilter)
    }

    override fun onResume() {
        super.onResume()
        nfcAdapter?.enableForegroundDispatch(this, pendingIntent, intentFilters, arrayOf(
            arrayOf("android.nfc.tech.NfcA"),
            arrayOf("android.nfc.tech.NfcB"),
            arrayOf("android.nfc.tech.IsoDep"),
        ))
    }

    override fun onPause() {
        super.onPause()
        nfcAdapter?.disableForegroundDispatch(this)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleNfcIntent(intent)
    }

    private fun handleNfcIntent(intent: Intent) {
        val tag: Tag? = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            intent.getParcelableExtra(NfcAdapter.EXTRA_TAG, Tag::class.java)
        } else {
            @Suppress("DEPRECATION")
            intent.getParcelableExtra(NfcAdapter.EXTRA_TAG)
        }

        tag?.let {
            val uid = it.id.joinToString("") { byte -> "%02X".format(byte) }
            vibrateOnDetect()
            viewModel.onNfcCardDetected(uid)
        }
    }

    // -----------------------------------------------------------------
    // 震动反馈 — NFC 检测（短促）
    // -----------------------------------------------------------------
    private fun vibrateOnDetect() {
        performVibration(100)
    }

    // -----------------------------------------------------------------
    // 震动反馈 — 退款成功（双段震动，强调危险操作已完成）
    // -----------------------------------------------------------------
    private fun vibrateOnRefundSuccess() {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vibratorManager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
                val vibrator = vibratorManager.defaultVibrator
                // 双段震动: 0ms等待, 150ms震动, 100ms暂停, 300ms震动
                vibrator.vibrate(
                    VibrationEffect.createWaveform(longArrayOf(0, 150, 100, 300), -1)
                )
            } else {
                @Suppress("DEPRECATION")
                val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    vibrator.vibrate(
                        VibrationEffect.createWaveform(longArrayOf(0, 150, 100, 300), -1)
                    )
                } else {
                    @Suppress("DEPRECATION")
                    vibrator.vibrate(longArrayOf(0, 150, 100, 300), -1)
                }
            }
        } catch (_: Exception) {
            // 忽略震动失败
        }
    }

    private fun performVibration(durationMs: Long) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vibratorManager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
                val vibrator = vibratorManager.defaultVibrator
                vibrator.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    vibrator.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
                } else {
                    @Suppress("DEPRECATION")
                    vibrator.vibrate(durationMs)
                }
            }
        } catch (_: Exception) {
            // 忽略震动失败
        }
    }

    // -----------------------------------------------------------------
    // 导航
    // -----------------------------------------------------------------
    private fun navigateToLogin() {
        startActivity(Intent(this, LoginActivity::class.java))
        finish()
    }

    private fun logout() {
        sessionManager.clearSession()
        navigateToLogin()
    }
}
