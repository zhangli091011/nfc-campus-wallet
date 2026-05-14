package com.campus.nfcwallet.ui.cardReturn

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
import androidx.compose.ui.Modifier
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.campus.nfcwallet.nfc.NFCReader
import com.campus.nfcwallet.ui.LoginActivity
import com.campus.nfcwallet.utils.SessionManager

/**
 * 还款+退卡终端 Activity
 *
 * 供工作人员使用，通过 NFC 识别学生卡片后办理还款或退卡。
 * 支持三种操作模式：
 * 1. 仅还款（不退卡）：从余额中扣除指定金额偿还贷款
 * 2. 余额先偿还贷款再退卡（保留贷款记录用于追偿）
 * 3. 直接全额退还余额，贷款另行偿还（保留贷款记录用于追偿）
 */
class CardReturnActivity : ComponentActivity() {

    private lateinit var sessionManager: SessionManager
    private var nfcAdapter: NfcAdapter? = null
    private var pendingIntent: PendingIntent? = null
    private var intentFilters: Array<IntentFilter>? = null

    private var soundPool: SoundPool? = null
    private var successSoundId: Int = 0

    private val viewModel: CardReturnViewModel by viewModels {
        object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return CardReturnViewModel(SessionManager(this@CardReturnActivity)) as T
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
                    .background(CardReturnColors.DeepBg)
            ) {
                CardReturnScreen(
                    state = viewModel.uiState,
                    onReturnWithRepay = viewModel::onReturnWithRepay,
                    onReturnWithoutRepay = viewModel::onReturnWithoutRepay,
                    onRepayOnly = viewModel::onRepayOnly,
                    onShowRepayDialog = viewModel::onShowRepayDialog,
                    onDismissRepayDialog = viewModel::onDismissRepayDialog,
                    onRepayAmountChange = viewModel::onRepayAmountChange,
                    onReset = viewModel::onReset,
                    onDismissError = viewModel::onDismissError,
                )
            }

            val isSuccess = viewModel.uiState.isSuccess
            androidx.compose.runtime.LaunchedEffect(isSuccess) {
                if (isSuccess) {
                    playSuccessFeedback()
                }
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
                viewModel.onNfcCardDetected(uid)
            }
        }
    }

    private fun initializeSoundPool() {
        val audioAttributes = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_NOTIFICATION)
            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
            .build()

        soundPool = SoundPool.Builder()
            .setMaxStreams(1)
            .setAudioAttributes(audioAttributes)
            .build()

        try {
            val resId = resources.getIdentifier("coin_success", "raw", packageName)
            if (resId != 0) {
                successSoundId = soundPool?.load(this, resId, 1) ?: 0
            }
        } catch (_: Exception) {}
    }

    private fun playSuccessFeedback() {
        if (successSoundId > 0) {
            soundPool?.play(successSoundId, 1.0f, 1.0f, 1, 0, 1.0f)
        }
        triggerVibration()
    }

    private fun triggerVibration() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val vibratorManager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
            vibratorManager?.defaultVibrator?.vibrate(
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

    private fun navigateToLogin() {
        val intent = Intent(this, LoginActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
        startActivity(intent)
        finish()
    }
}
