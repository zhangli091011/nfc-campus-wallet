package com.campus.nfcwallet.ui.investment

import android.app.PendingIntent
import android.content.Intent
import android.content.IntentFilter
import android.nfc.NfcAdapter
import android.nfc.Tag
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.campus.nfcwallet.nfc.NFCReader
import com.campus.nfcwallet.ui.LoginActivity
import com.campus.nfcwallet.utils.SessionManager

/**
 * Investment Activity (Compose version).
 *
 * 官方中央银行 - 模拟投资办理终端
 */
class InvestmentComposeActivity : ComponentActivity() {

    private lateinit var sessionManager: SessionManager
    private var nfcAdapter: NfcAdapter? = null
    private var pendingIntent: PendingIntent? = null
    private var intentFilters: Array<IntentFilter>? = null

    private val viewModel: InvestmentViewModel by viewModels {
        object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return InvestmentViewModel(SessionManager(this@InvestmentComposeActivity)) as T
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
            .let { if (it <= 0) 2 else it } // 默认活动ID为2（按add_investment_system.py输出）
        viewModel.init(eventId)

        initializeNFC()

        setContent {
            val state by androidx.compose.runtime.remember(viewModel) {
                androidx.compose.runtime.derivedStateOf { viewModel.uiState }
            }
            androidx.compose.foundation.layout.Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(InvestmentColors.Background)
            ) {
                InvestmentScreen(
                    state = viewModel.uiState,
                    onBoothSelected = viewModel::onBoothSelected,
                    onSharesChanged = viewModel::onSharesChanged,
                    onConfirmInvestment = viewModel::onConfirmInvestment,
                    onDismissMessage = viewModel::onDismissMessage,
                    onLogout = { logout() },
                    onTabChanged = viewModel::onTabChanged,
                    onHoldingSelected = viewModel::onHoldingSelected,
                    onSellSharesChanged = viewModel::onSellSharesChanged,
                    onConfirmSell = viewModel::onConfirmSell,
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
                viewModel.onNfcCardDetected(uid)
            }
        }
    }

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
