package com.campus.nfcwallet.ui;

import android.animation.ObjectAnimator;
import android.animation.ValueAnimator;
import android.app.PendingIntent;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Color;
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.view.animation.AccelerateDecelerateInterpolator;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.cardview.widget.CardView;

import com.campus.nfcwallet.R;
import com.campus.nfcwallet.api.APIClient;
import com.campus.nfcwallet.api.WalletAPIService;
import com.campus.nfcwallet.models.BalanceResponse;
import com.campus.nfcwallet.models.BoothInfo;
import com.campus.nfcwallet.models.ParticipantInfo;
import com.campus.nfcwallet.models.StockBuyRequest;
import com.campus.nfcwallet.models.StockBuyResponse;
import com.campus.nfcwallet.nfc.NFCReader;
import com.campus.nfcwallet.utils.ErrorHandler;
import com.campus.nfcwallet.utils.SessionManager;

import java.util.ArrayList;
import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Investment Activity - 官方中央银行投资办理终端
 * 
 * 高科技感黑金配色界面，用于办理模拟股票投资业务
 */
public class InvestmentActivity extends AppCompatActivity {
    
    private static final String TAG = "InvestmentActivity";
    
    // UI Components
    private TextView tvTitle;
    private CardView cardNfcArea;
    private ImageView ivNfcIcon;
    private TextView tvNfcStatus;
    private TextView tvCardUid;
    private CardView cardParticipantInfo;
    private TextView tvParticipantName;
    private TextView tvAccountBalance;
    private TextView tvStockBalance;
    private CardView cardInvestmentForm;
    private Spinner spinnerBooth;
    private EditText etShares;
    private TextView tvTotalAmount;
    private Button btnConfirmInvestment;
    private ProgressBar progressBar;
    
    // NFC
    private NfcAdapter nfcAdapter;
    private PendingIntent pendingIntent;
    private IntentFilter[] intentFilters;
    
    // Data
    private SessionManager sessionManager;
    private WalletAPIService apiService;
    private int eventId;
    private String currentCardUid;
    private ParticipantInfo currentParticipant;
    private double accountBalance;  // 活动账户余额（元）
    private double stockBalance;    // 投资币余额（元）
    private List<BoothInfo> boothList = new ArrayList<>();
    private BoothInfo selectedBooth;
    
    // Animation
    private ObjectAnimator pulseAnimator;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_investment);
        
        // Initialize
        sessionManager = new SessionManager(this);
        apiService = APIClient.getAPIService();
        eventId = getIntent().getIntExtra("event_id", sessionManager.getEventId());
        
        // Initialize UI
        initializeUI();
        
        // Initialize NFC
        initializeNFC();
        
        // Load booths
        loadBooths();
        
        // Start NFC animation
        startNfcAnimation();
    }
    
    private void initializeUI() {
        tvTitle = findViewById(R.id.tv_title);
        cardNfcArea = findViewById(R.id.card_nfc_area);
        ivNfcIcon = findViewById(R.id.iv_nfc_icon);
        tvNfcStatus = findViewById(R.id.tv_nfc_status);
        tvCardUid = findViewById(R.id.tv_card_uid);
        cardParticipantInfo = findViewById(R.id.card_participant_info);
        tvParticipantName = findViewById(R.id.tv_participant_name);
        tvAccountBalance = findViewById(R.id.tv_account_balance);
        tvStockBalance = findViewById(R.id.tv_stock_balance);
        cardInvestmentForm = findViewById(R.id.card_investment_form);
        spinnerBooth = findViewById(R.id.spinner_booth);
        etShares = findViewById(R.id.et_shares);
        tvTotalAmount = findViewById(R.id.tv_total_amount);
        btnConfirmInvestment = findViewById(R.id.btn_confirm_investment);
        progressBar = findViewById(R.id.progress_bar);
        
        // Initial state
        cardParticipantInfo.setVisibility(View.GONE);
        cardInvestmentForm.setVisibility(View.GONE);
        
        // Calculate total amount on shares change
        etShares.addTextChangedListener(new android.text.TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            
            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                calculateTotalAmount();
            }
            
            @Override
            public void afterTextChanged(android.text.Editable s) {}
        });
        
        // Booth selection listener
        spinnerBooth.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(android.widget.AdapterView<?> parent, View view, int position, long id) {
                if (position >= 0 && position < boothList.size()) {
                    selectedBooth = boothList.get(position);
                    calculateTotalAmount();
                }
            }
            
            @Override
            public void onNothingSelected(android.widget.AdapterView<?> parent) {
                selectedBooth = null;
            }
        });
        
        // Confirm button
        btnConfirmInvestment.setOnClickListener(v -> confirmInvestment());
    }
    
    private void initializeNFC() {
        nfcAdapter = NfcAdapter.getDefaultAdapter(this);
        
        if (nfcAdapter == null) {
            showHighTechToast("设备不支持NFC", false);
            finish();
            return;
        }
        
        if (!nfcAdapter.isEnabled()) {
            showHighTechToast("请在设置中启用NFC", false);
        }
        
        // Setup NFC intent
        Intent intent = new Intent(this, getClass())
            .addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
        pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_MUTABLE
        );
        
        IntentFilter nfcFilter = new IntentFilter(NfcAdapter.ACTION_TAG_DISCOVERED);
        intentFilters = new IntentFilter[]{nfcFilter};
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        if (nfcAdapter != null) {
            nfcAdapter.enableForegroundDispatch(
                this, pendingIntent, intentFilters, null
            );
        }
    }
    
    @Override
    protected void onPause() {
        super.onPause();
        if (nfcAdapter != null) {
            nfcAdapter.disableForegroundDispatch(this);
        }
        if (pulseAnimator != null) {
            pulseAnimator.cancel();
        }
    }
    
    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        
        if (NfcAdapter.ACTION_TAG_DISCOVERED.equals(intent.getAction())) {
            Tag tag = intent.getParcelableExtra(NfcAdapter.EXTRA_TAG);
            if (tag != null) {
                handleNFCTag(tag);
            }
        }
    }
    
    private void startNfcAnimation() {
        // Pulse animation for NFC icon
        pulseAnimator = ObjectAnimator.ofFloat(ivNfcIcon, "alpha", 1.0f, 0.3f, 1.0f);
        pulseAnimator.setDuration(2000);
        pulseAnimator.setRepeatCount(ValueAnimator.INFINITE);
        pulseAnimator.setInterpolator(new AccelerateDecelerateInterpolator());
        pulseAnimator.start();
    }
    
    private void handleNFCTag(Tag tag) {
        String cardUid = NFCReader.bytesToHex(tag.getId());
        Log.d(TAG, "NFC卡读取成功: " + cardUid);
        
        // Stop animation
        if (pulseAnimator != null) {
            pulseAnimator.cancel();
            ivNfcIcon.setAlpha(1.0f);
        }
        
        currentCardUid = cardUid;
        tvCardUid.setText("卡号: " + cardUid);
        tvNfcStatus.setText("✓ 识别成功");
        tvNfcStatus.setTextColor(Color.parseColor("#FFD700"));  // Gold
        
        // Load participant info
        loadParticipantInfo(cardUid);
    }
    
    private void loadBooths() {
        String token = "Bearer " + sessionManager.getToken();
        
        apiService.getBooths(token, "active").enqueue(new Callback<List<BoothInfo>>() {
            @Override
            public void onResponse(Call<List<BoothInfo>> call, Response<List<BoothInfo>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    boothList.clear();
                    boothList.addAll(response.body());
                    
                    // Setup spinner
                    List<String> boothNames = new ArrayList<>();
                    for (BoothInfo booth : boothList) {
                        boothNames.add(booth.getName() + " - " + booth.getClassName());
                    }
                    
                    ArrayAdapter<String> adapter = new ArrayAdapter<>(
                        InvestmentActivity.this,
                        android.R.layout.simple_spinner_item,
                        boothNames
                    );
                    adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
                    spinnerBooth.setAdapter(adapter);
                }
            }
            
            @Override
            public void onFailure(Call<List<BoothInfo>> call, Throwable t) {
                Log.e(TAG, "加载摊位失败", t);
            }
        });
    }
    
    private void loadParticipantInfo(String cardUid) {
        progressBar.setVisibility(View.VISIBLE);
        
        apiService.getParticipantByCard(cardUid).enqueue(new Callback<ParticipantInfo>() {
            @Override
            public void onResponse(Call<ParticipantInfo> call, Response<ParticipantInfo> response) {
                if (response.isSuccessful() && response.body() != null) {
                    currentParticipant = response.body();
                    tvParticipantName.setText(String.format(
                        "%s (%s)",
                        currentParticipant.getName(),
                        currentParticipant.getClassName()
                    ));
                    
                    // Load balances
                    loadBalances(cardUid);
                } else {
                    progressBar.setVisibility(View.GONE);
                    showHighTechToast("参与者不存在", false);
                }
            }
            
            @Override
            public void onFailure(Call<ParticipantInfo> call, Throwable t) {
                progressBar.setVisibility(View.GONE);
                Log.e(TAG, "查询参与者失败", t);
                showHighTechToast("网络错误", false);
            }
        });
    }
    
    private void loadBalances(String cardUid) {
        // Load account balance
        apiService.getBalanceByEvent(eventId, cardUid).enqueue(new Callback<BalanceResponse>() {
            @Override
            public void onResponse(Call<BalanceResponse> call, Response<BalanceResponse> response) {
                progressBar.setVisibility(View.GONE);
                
                if (response.isSuccessful() && response.body() != null) {
                    accountBalance = response.body().getBalance();
                    stockBalance = 0;  // TODO: Load stock balance from API
                    
                    tvAccountBalance.setText(String.format("活动余额: ¥%.2f", accountBalance));
                    tvStockBalance.setText(String.format("投资币: ¥%.2f", stockBalance));
                    
                    // Show participant info and form
                    cardParticipantInfo.setVisibility(View.VISIBLE);
                    cardInvestmentForm.setVisibility(View.VISIBLE);
                    
                    // Animate in
                    cardParticipantInfo.setAlpha(0f);
                    cardInvestmentForm.setAlpha(0f);
                    cardParticipantInfo.animate().alpha(1f).setDuration(500).start();
                    cardInvestmentForm.animate().alpha(1f).setDuration(500).setStartDelay(200).start();
                }
            }
            
            @Override
            public void onFailure(Call<BalanceResponse> call, Throwable t) {
                progressBar.setVisibility(View.GONE);
                Log.e(TAG, "查询余额失败", t);
            }
        });
    }
    
    private void calculateTotalAmount() {
        String sharesStr = etShares.getText().toString();
        if (sharesStr.isEmpty() || selectedBooth == null) {
            tvTotalAmount.setText("总金额: ¥0.00");
            return;
        }
        
        try {
            int shares = Integer.parseInt(sharesStr);
            double pricePerShare = 5.0;  // 固定单价5元
            double total = shares * pricePerShare;
            tvTotalAmount.setText(String.format("总金额: ¥%.2f", total));
            tvTotalAmount.setTextColor(Color.parseColor("#FFD700"));  // Gold
        } catch (NumberFormatException e) {
            tvTotalAmount.setText("总金额: ¥0.00");
        }
    }
    
    private void confirmInvestment() {
        if (currentCardUid == null || currentParticipant == null) {
            showHighTechToast("请先刷NFC卡", false);
            return;
        }
        
        if (selectedBooth == null) {
            showHighTechToast("请选择投资摊位", false);
            return;
        }
        
        String sharesStr = etShares.getText().toString();
        if (sharesStr.isEmpty()) {
            showHighTechToast("请输入购买股数", false);
            return;
        }
        
        int shares;
        try {
            shares = Integer.parseInt(sharesStr);
            if (shares <= 0) {
                showHighTechToast("股数必须大于0", false);
                return;
            }
        } catch (NumberFormatException e) {
            showHighTechToast("请输入有效的股数", false);
            return;
        }
        
        int totalAmountCents = 500 * shares;  // 5元 = 500分
        double totalAmountYuan = shares * 5.0;  // 5元/股
        
        // Check stock balance (both in yuan)
        if (stockBalance < totalAmountYuan) {
            showHighTechToast("投资币余额不足", false);
            return;
        }
        
        // Show confirmation dialog
        showConfirmationDialog(shares, totalAmountCents);
    }
    
    private void showConfirmationDialog(int shares, int totalAmount) {
        new AlertDialog.Builder(this)
            .setTitle("确认投资")
            .setMessage(String.format(
                "投资摊位: %s\n" +
                "购买股数: %d股\n" +
                "单价: ¥5.00/股\n" +
                "总金额: ¥%.2f\n\n" +
                "确认购买？",
                selectedBooth.getName(),
                shares,
                totalAmount / 100.0
            ))
            .setPositiveButton("确认", (dialog, which) -> processBuyStock(shares))
            .setNegativeButton("取消", null)
            .show();
    }
    
    private void processBuyStock(int shares) {
        progressBar.setVisibility(View.VISIBLE);
        btnConfirmInvestment.setEnabled(false);
        
        String authHeader = sessionManager.getAuthHeader();
        if (authHeader == null) {
            showHighTechToast("登录已过期，请重新登录", false);
            progressBar.setVisibility(View.GONE);
            btnConfirmInvestment.setEnabled(true);
            return;
        }
        
        // Create request (JWT auth, no signature needed)
        StockBuyRequest request = new StockBuyRequest(
            currentCardUid,
            eventId,
            selectedBooth.getId(),
            shares
        );
        
        apiService.buyStock(authHeader, request).enqueue(new Callback<StockBuyResponse>() {
            @Override
            public void onResponse(Call<StockBuyResponse> call, Response<StockBuyResponse> response) {
                progressBar.setVisibility(View.GONE);
                btnConfirmInvestment.setEnabled(true);
                
                if (response.isSuccessful() && response.body() != null) {
                    StockBuyResponse result = response.body();
                    
                    // Update stock balance (use yuan value)
                    stockBalance = result.getNewBalanceYuan();
                    tvStockBalance.setText(String.format("投资币: ¥%.2f", result.getNewBalanceYuan()));
                    
                    // Show success dialog
                    showSuccessDialog(result);
                    
                    // Clear form
                    etShares.setText("");
                    spinnerBooth.setSelection(0);
                } else {
                    String error = ErrorHandler.parseError(response);
                    showHighTechToast("购买失败: " + error, false);
                }
            }
            
            @Override
            public void onFailure(Call<StockBuyResponse> call, Throwable t) {
                progressBar.setVisibility(View.GONE);
                btnConfirmInvestment.setEnabled(true);
                Log.e(TAG, "购买股票失败", t);
                showHighTechToast("网络错误", false);
            }
        });
    }
    
    private void showSuccessDialog(StockBuyResponse result) {
        new AlertDialog.Builder(this)
            .setTitle("✓ 投资成功")
            .setMessage(String.format(
                "%s\n\n" +
                "投资摊位: %s\n" +
                "购买股数: %d股\n" +
                "购买单价: ¥%.2f\n" +
                "购买总额: ¥%.2f\n" +
                "剩余投资币: ¥%.2f",
                result.getMessage(),
                result.getBoothName(),
                result.getShares(),
                result.getBuyPriceYuan(),
                result.getTotalAmountYuan(),
                result.getNewBalanceYuan()
            ))
            .setPositiveButton("确定", null)
            .show();
    }
    
    private void showHighTechToast(String message, boolean success) {
        Toast toast = Toast.makeText(this, message, Toast.LENGTH_SHORT);
        toast.show();
    }
}
