package com.campus.nfcwallet.ui.bankTeller

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.media.AudioAttributes
import android.media.SoundPool
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
import com.campus.nfcwallet.nfc.NFCReader
import com.campus.nfcwallet.ui.LoginActivity
import com.campus.nfcwallet.utils.SessionManager

/**
 * 银行柜员操作终端 Activity
 *
 * 官方中央银行 - 信用垫资发行终端
 * 供银行工作人员使用，通过 NFC 识别学生卡片后发行信用额度。
 */
class BankTellerActivity : ComponentActivity() {

    private lateinit var sessionManager: SessionManager
    private var nfcAdapter: NfcAdapter? = null
    private var pendingIntent: PendingIntent? = null
    private var intentFilters: Array<IntentFilter>? = null

    // 音效
    private var soundPool: SoundPool? = null
    private var successSoundId: Int = 0

    private val viewModel: BankTellerViewModel by viewModels {
        object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return BankTellerViewModel(SessionManager(this@BankTellerActivity)) as T
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
        initializeSoundPool()

        setContent {
            androidx.compose.foundation.layout.Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(BankColors.NavyDeep)
            ) {
                BankTellerScreen(
                    state = viewModel.uiState,
                    onAmountSelected = viewModel::onAmountSelected,
                    onPaperworkChecked = viewModel::onPaperworkChecked,
                    onConfirmIssuance = {
                        viewModel.onConfirmIssuance()
                        // 成功后的反馈在观察 state 变化时触发
                    },
                    onReset = viewModel::onReset,
                    onDismissError = viewModel::onDismissError,
                    onLogout = { logout() },
                )
            }

            // 监听成功状态，播放音效和震动
            val isSuccess = viewModel.uiState.isSuccess
            androidx.compose.runtime.LaunchedEffect(isSuccess) {
                if (isSuccess) {
                    playSuccessFeedback()
                }
            }
        }
    }

    // -----------------------------------------------------------------
    // NFC 初始化
    // -----------------------------------------------------------------
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
                viewModel.onNfcCardDetected(uid)
            }
        }
    }

    // -----------------------------------------------------------------
    // 音效与震动反馈
    // -----------------------------------------------------------------
    private fun initializeSoundPool() {
        val audioAttributes = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_NOTIFICATION)
            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
            .build()

        soundPool = SoundPool.Builder()
            .setMaxStreams(1)
            .setAudioAttributes(audioAttributes)
            .build()

        // 加载成功音效（需要在 res/raw/ 下放置 coin_success.mp3）
        try {
            val resId = resources.getIdentifier("coin_success", "raw", packageName)
            if (resId != 0) {
                successSoundId = soundPool?.load(this, resId, 1) ?: 0
            }
        } catch (e: Exception) {
            // 音效资源不存在时静默处理
        }
    }

    private fun playSuccessFeedback() {
        // 播放音效
        if (successSoundId > 0) {
            soundPool?.play(successSoundId, 1.0f, 1.0f, 1, 0, 1.0f)
        }

        // 震动反馈
        triggerVibration()
    }

    private fun triggerVibration() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val vibratorManager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
            val vibrator = vibratorManager?.defaultVibrator
            vibrator?.vibrate(
                VibrationEffect.createOneShot(200, VibrationEffect.DEFAULT_AMPLITUDE)
            )
        } else {
            @Suppress("DEPRECATION")
            val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator?.vibrate(
                    VibrationEffect.createOneShot(200, VibrationEffect.DEFAULT_AMPLITUDE)
                )
            } else {
                @Suppress("DEPRECATION")
                vibrator?.vibrate(200)
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        soundPool?.release()
        soundPool = null
    }

    // -----------------------------------------------------------------
    // 导航
    // -----------------------------------------------------------------
    private fun logout() {
        sessionManager.clearSession()
        navigateToLogin()
    }

    private fun navigateToLogin() {
        val intent = Intent(this, LoginActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
        startActivity(intent)
        finish()
    }
}
