package com.campus.nfcwallet.ui;

import android.app.PendingIntent;
import android.content.Intent;
import android.content.IntentFilter;
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.campus.nfcwallet.R;
import com.campus.nfcwallet.api.APIClient;
import com.campus.nfcwallet.api.WalletAPIService;
import com.campus.nfcwallet.models.BalanceResponse;
import com.campus.nfcwallet.models.ParticipantInfo;
import com.campus.nfcwallet.models.Stock;
import com.campus.nfcwallet.models.StockPurchaseRequest;
import com.campus.nfcwallet.models.StockPurchaseResponse;
import com.campus.nfcwallet.nfc.NFCReader;
import com.campus.nfcwallet.signature.SignatureGenerator;
import com.campus.nfcwallet.utils.ErrorHandler;
import com.campus.nfcwallet.utils.SessionManager;

import java.util.ArrayList;
import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Stock Investment Activity - 股票投资办理端
 * 
 * 功能：
 * 1. NFC读卡识别参与者
 * 2. 显示可购买股票列表
 * 3. 选择股票和数量
 * 4. 确认购买并扣除余额
 */
public class StockInvestmentActivity extends AppCompatActivity {
    
    private static final String TAG = "StockInvestment";
    
    // UI Components
    private TextView tvNfcStatus;
    private TextView tvParticipantInfo;
    private TextView tvBalance;
    private RecyclerView rvStocks;
    private ProgressBar progressBar;
    private Button btnRefresh;
    
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
    private double currentBalance;
    private List<Stock> stockList = new ArrayList<>();
    private StockListAdapter stockAdapter;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_stock_investment);
        
        // Initialize
        sessionManager = new SessionManager(this);
        apiService = APIClient.getAPIService();
        
        // Get event ID from intent or session
        eventId = getIntent().getIntExtra("event_id", sessionManager.getEventId());
        
        // Initialize UI
        initializeUI();
        
        // Initialize NFC
        initializeNFC();
        
        // Load stocks
        loadStocks();
    }
    
    private void initializeUI() {
        tvNfcStatus = findViewById(R.id.tv_nfc_status);
        tvParticipantInfo = findViewById(R.id.tv_participant_info);
        tvBalance = findViewById(R.id.tv_balance);
        rvStocks = findViewById(R.id.rv_stocks);
        progressBar = findViewById(R.id.progress_bar);
        btnRefresh = findViewById(R.id.btn_refresh);
        
        // Setup RecyclerView
        rvStocks.setLayoutManager(new LinearLayoutManager(this));
        stockAdapter = new StockListAdapter(stockList, this::onStockSelected);
        rvStocks.setAdapter(stockAdapter);
        
        // Refresh button
        btnRefresh.setOnClickListener(v -> loadStocks());
        
        // Initial status
        tvNfcStatus.setText("请刷NFC卡");
        tvParticipantInfo.setText("等待读卡...");
        tvBalance.setText("余额: --");
    }
    
    private void initializeNFC() {
        nfcAdapter = NfcAdapter.getDefaultAdapter(this);
        
        if (nfcAdapter == null) {
            Toast.makeText(this, "设备不支持NFC", Toast.LENGTH_LONG).show();
            finish();
            return;
        }
        
        if (!nfcAdapter.isEnabled()) {
            Toast.makeText(this, "请在设置中启用NFC", Toast.LENGTH_LONG).show();
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
    
    private void handleNFCTag(Tag tag) {
        String cardUid = NFCReader.bytesToHex(tag.getId());
        Log.d(TAG, "NFC卡读取成功: " + cardUid);
        
        currentCardUid = cardUid;
        tvNfcStatus.setText("卡号: " + cardUid);
        
        // Query participant info
        loadParticipantInfo(cardUid);
    }
    
    private void loadParticipantInfo(String cardUid) {
        progressBar.setVisibility(View.VISIBLE);
        
        apiService.getParticipantByCard(cardUid).enqueue(new Callback<ParticipantInfo>() {
            @Override
            public void onResponse(Call<ParticipantInfo> call, Response<ParticipantInfo> response) {
                progressBar.setVisibility(View.GONE);
                
                if (response.isSuccessful() && response.body() != null) {
                    currentParticipant = response.body();
                    tvParticipantInfo.setText(String.format(
                        "%s (%s)",
                        currentParticipant.getName(),
                        currentParticipant.getClassName()
                    ));
                    
                    // Load balance
                    loadBalance(cardUid);
                } else {
                    String error = ErrorHandler.parseError(response);
                    Toast.makeText(
                        StockInvestmentActivity.this,
                        "查询参与者失败: " + error,
                        Toast.LENGTH_SHORT
                    ).show();
                    tvParticipantInfo.setText("参与者不存在");
                }
            }
            
            @Override
            public void onFailure(Call<ParticipantInfo> call, Throwable t) {
                progressBar.setVisibility(View.GONE);
                Log.e(TAG, "查询参与者失败", t);
                Toast.makeText(
                    StockInvestmentActivity.this,
                    "网络错误: " + t.getMessage(),
                    Toast.LENGTH_SHORT
                ).show();
            }
        });
    }
    
    private void loadBalance(String cardUid) {
        apiService.getBalanceByEvent(eventId, cardUid).enqueue(new Callback<BalanceResponse>() {
            @Override
            public void onResponse(Call<BalanceResponse> call, Response<BalanceResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    currentBalance = response.body().getBalance();
                    tvBalance.setText(String.format(
                        "余额: ¥%.2f",
                        currentBalance
                    ));
                } else {
                    tvBalance.setText("余额: 查询失败");
                }
            }
            
            @Override
            public void onFailure(Call<BalanceResponse> call, Throwable t) {
                Log.e(TAG, "查询余额失败", t);
                tvBalance.setText("余额: 网络错误");
            }
        });
    }
    
    private void loadStocks() {
        progressBar.setVisibility(View.VISIBLE);
        
        String token = "Bearer " + sessionManager.getToken();
        
        apiService.getStocks(token, eventId, "active").enqueue(new Callback<List<Stock>>() {
            @Override
            public void onResponse(Call<List<Stock>> call, Response<List<Stock>> response) {
                progressBar.setVisibility(View.GONE);
                
                if (response.isSuccessful() && response.body() != null) {
                    stockList.clear();
                    stockList.addAll(response.body());
                    stockAdapter.notifyDataSetChanged();
                    
                    if (stockList.isEmpty()) {
                        Toast.makeText(
                            StockInvestmentActivity.this,
                            "暂无可购买的股票",
                            Toast.LENGTH_SHORT
                        ).show();
                    }
                } else {
                    String error = ErrorHandler.parseError(response);
                    Toast.makeText(
                        StockInvestmentActivity.this,
                        "加载股票失败: " + error,
                        Toast.LENGTH_SHORT
                    ).show();
                }
            }
            
            @Override
            public void onFailure(Call<List<Stock>> call, Throwable t) {
                progressBar.setVisibility(View.GONE);
                Log.e(TAG, "加载股票失败", t);
                Toast.makeText(
                    StockInvestmentActivity.this,
                    "网络错误: " + t.getMessage(),
                    Toast.LENGTH_SHORT
                ).show();
            }
        });
    }
    
    private void onStockSelected(Stock stock) {
        if (currentCardUid == null || currentParticipant == null) {
            Toast.makeText(this, "请先刷NFC卡", Toast.LENGTH_SHORT).show();
            return;
        }
        
        if (!stock.isAvailable()) {
            Toast.makeText(this, "该股票不可购买", Toast.LENGTH_SHORT).show();
            return;
        }
        
        // Show purchase dialog
        showPurchaseDialog(stock);
    }
    
    private void showPurchaseDialog(Stock stock) {
        View dialogView = getLayoutInflater().inflate(R.layout.dialog_stock_purchase, null);
        
        TextView tvStockInfo = dialogView.findViewById(R.id.tv_stock_info);
        TextView tvPrice = dialogView.findViewById(R.id.tv_price);
        TextView tvAvailable = dialogView.findViewById(R.id.tv_available);
        EditText etQuantity = dialogView.findViewById(R.id.et_quantity);
        TextView tvTotalAmount = dialogView.findViewById(R.id.tv_total_amount);
        
        tvStockInfo.setText(String.format(
            "%s - %s",
            stock.getBoothName(),
            stock.getClassName()
        ));
        tvPrice.setText(String.format("单价: ¥%.2f", stock.getInitialPriceYuan()));
        tvAvailable.setText(String.format("剩余: %d股", stock.getAvailableShares()));
        
        // Calculate total amount on quantity change
        etQuantity.addTextChangedListener(new android.text.TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            
            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                try {
                    int quantity = Integer.parseInt(s.toString());
                    double total = quantity * stock.getInitialPriceYuan();
                    tvTotalAmount.setText(String.format("总金额: ¥%.2f", total));
                } catch (NumberFormatException e) {
                    tvTotalAmount.setText("总金额: ¥0.00");
                }
            }
            
            @Override
            public void afterTextChanged(android.text.Editable s) {}
        });
        
        new AlertDialog.Builder(this)
            .setTitle("购买股票")
            .setView(dialogView)
            .setPositiveButton("确认购买", (dialog, which) -> {
                String quantityStr = etQuantity.getText().toString();
                if (quantityStr.isEmpty()) {
                    Toast.makeText(this, "请输入购买数量", Toast.LENGTH_SHORT).show();
                    return;
                }
                
                int quantity = Integer.parseInt(quantityStr);
                if (quantity <= 0) {
                    Toast.makeText(this, "购买数量必须大于0", Toast.LENGTH_SHORT).show();
                    return;
                }
                
                if (quantity > stock.getAvailableShares()) {
                    Toast.makeText(this, "购买数量超过剩余股数", Toast.LENGTH_SHORT).show();
                    return;
                }
                
                int totalAmount = stock.getInitialPrice() * quantity;
                double totalAmountYuan = totalAmount / 100.0;
                if (totalAmountYuan > currentBalance) {
                    Toast.makeText(this, "余额不足", Toast.LENGTH_SHORT).show();
                    return;
                }
                
                // Process purchase
                processPurchase(stock, quantity);
            })
            .setNegativeButton("取消", null)
            .show();
    }
    
    private void processPurchase(Stock stock, int quantity) {
        progressBar.setVisibility(View.VISIBLE);
        
        // Generate signature
        long timestamp = System.currentTimeMillis() / 1000;
        int amount = stock.getInitialPrice() * quantity;
        String signature = SignatureGenerator.generateSignature(
            currentCardUid,
            amount,
            timestamp
        );
        
        // Create request
        StockPurchaseRequest request = new StockPurchaseRequest(
            currentCardUid,
            stock.getId(),
            quantity,
            timestamp,
            signature
        );
        
        apiService.purchaseStock(request).enqueue(new Callback<StockPurchaseResponse>() {
            @Override
            public void onResponse(Call<StockPurchaseResponse> call, Response<StockPurchaseResponse> response) {
                progressBar.setVisibility(View.GONE);
                
                if (response.isSuccessful() && response.body() != null) {
                    StockPurchaseResponse result = response.body();
                    
                    // Update balance (use yuan value)
                    currentBalance = result.getNewBalanceYuan();
                    tvBalance.setText(String.format("余额: ¥%.2f", result.getNewBalanceYuan()));
                    
                    // Show success message
                    new AlertDialog.Builder(StockInvestmentActivity.this)
                        .setTitle("购买成功")
                        .setMessage(String.format(
                            "%s\n\n" +
                            "购买数量: %d股\n" +
                            "购买单价: ¥%.2f\n" +
                            "购买总额: ¥%.2f\n" +
                            "剩余余额: ¥%.2f",
                            result.getMessage(),
                            result.getQuantity(),
                            result.getPurchasePriceYuan(),
                            result.getTotalAmountYuan(),
                            result.getNewBalanceYuan()
                        ))
                        .setPositiveButton("确定", null)
                        .show();
                    
                    // Reload stocks
                    loadStocks();
                } else {
                    String error = ErrorHandler.parseError(response);
                    Toast.makeText(
                        StockInvestmentActivity.this,
                        "购买失败: " + error,
                        Toast.LENGTH_LONG
                    ).show();
                }
            }
            
            @Override
            public void onFailure(Call<StockPurchaseResponse> call, Throwable t) {
                progressBar.setVisibility(View.GONE);
                Log.e(TAG, "购买股票失败", t);
                Toast.makeText(
                    StockInvestmentActivity.this,
                    "网络错误: " + t.getMessage(),
                    Toast.LENGTH_SHORT
                ).show();
            }
        });
    }
}
