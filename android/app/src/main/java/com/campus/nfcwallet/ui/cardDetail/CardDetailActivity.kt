package com.campus.nfcwallet.ui.cardDetail

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
import androidx.compose.ui.Modifier
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.campus.nfcwallet.nfc.NFCReader
import com.campus.nfcwallet.ui.LoginActivity
import com.campus.nfcwallet.utils.SessionManager

/**
 * 刷卡查看用户明细 Activity
 *
 * 通过 NFC 识别学生卡片后，展示该用户的全部信息：
 * - 基本信息（姓名、班级、学号）
 * - 账户余额和信贷信息
 * - 贷款摘要
 * - 股票持仓
 * - 最近交易流水
 */
class CardDetailActivity : ComponentActivity() {

    private lateinit var sessionManager: SessionManager
    private var nfcAdapter: NfcAdapter? = null
    private var pendingIntent: PendingIntent? = null
    private var intentFilters: Array<IntentFilter>? = null

    private val viewModel: CardDetailViewModel by viewModels {
        object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return CardDetailViewModel(SessionManager(this@CardDetailActivity)) as T
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

        val eventId = intent.getIntExtra("event_id", sessionManager.eventId)
            .let { if (it <= 0) 2 else it }
        viewModel.init(eventId)

        initializeNFC()

        setContent {
            androidx.compose.foundation.layout.Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(CardDetailColors.Background)
            ) {
                CardDetailScreen(
                    state = viewModel.uiState,
                    onReset = viewModel::onReset,
                    onDismissError = viewModel::onDismissError,
                )
            }
        }
    }

    private fun initializeNFC() {
        nfcAdapter = NfcAdapter.getDefaultAdapter(this)
        if (nfcAdapter == null) {
            Toast.makeText(this, "设备不支持NFC", Toast.LENGTH_LONG).show()
            return
        }
        if (!nfcAdapter!!.isEnabled) {
            Toast.makeText(this, "请在系统设置中启用NFC", Toast.LENGTH_LONG).show()
        }

        val intent = Intent(this, this::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
        pendingIntent = PendingIntent.getActivity(
            this, 0, intent, PendingIntent.FLAG_MUTABLE,
        )
        val nfcFilter = IntentFilter(NfcAdapter.ACTION_TAG_DISCOVERED)
        intentFilters = arrayOf(nfcFilter)
    }

    override fun onResume() {
        super.onResume()
        nfcAdapter?.enableForegroundDispatch(this, pendingIntent, intentFilters, null)
    }

    override fun onPause() {
        super.onPause()
        nfcAdapter?.disableForegroundDispatch(this)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        if (NfcAdapter.ACTION_TAG_DISCOVERED == intent.action) {
            val tag = intent.getParcelableExtra<Tag>(NfcAdapter.EXTRA_TAG)
            tag?.let {
                val uid = NFCReader.bytesToHex(it.id)
                vibrateOnDetect()
                viewModel.onNfcCardDetected(uid)
            }
        }
    }

    private fun vibrateOnDetect() {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vibratorManager =
                    getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
                vibratorManager?.defaultVibrator?.vibrate(
                    VibrationEffect.createOneShot(100, VibrationEffect.DEFAULT_AMPLITUDE)
                )
            } else {
                @Suppress("DEPRECATION")
                val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    vibrator?.vibrate(
                        VibrationEffect.createOneShot(100, VibrationEffect.DEFAULT_AMPLITUDE)
                    )
                } else {
                    @Suppress("DEPRECATION")
                    vibrator?.vibrate(100)
                }
            }
        } catch (_: Exception) {}
    }

    private fun navigateToLogin() {
        val intent = Intent(this, LoginActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
        startActivity(intent)
        finish()
    }
}
