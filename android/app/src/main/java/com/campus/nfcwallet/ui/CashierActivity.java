package com.campus.nfcwallet.ui;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.GridLayoutManager;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.campus.nfcwallet.R;
import com.campus.nfcwallet.api.APIClient;
import com.campus.nfcwallet.api.WalletAPIService;
import com.campus.nfcwallet.models.BalanceResponse;
import com.campus.nfcwallet.models.BoothInfo;
import com.campus.nfcwallet.models.BoothPaymentRequest;
import com.campus.nfcwallet.models.CartItem;
import com.campus.nfcwallet.models.EventInfo;
import com.campus.nfcwallet.models.ParticipantInfo;
import com.campus.nfcwallet.models.Product;
import com.campus.nfcwallet.models.RechargeRequest;
import com.campus.nfcwallet.models.TransactionResponse;
import com.campus.nfcwallet.models.UserInfo;
import com.campus.nfcwallet.nfc.NFCReader;
import com.campus.nfcwallet.signature.SignatureGenerator;
import com.campus.nfcwallet.utils.ErrorHandler;
import com.campus.nfcwallet.utils.SessionManager;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Cashier terminal activity for booth operations.
 * 
 * Features:
 * - NFC card reading
 * - Participant info display
 * - Product selection with shopping cart
 * - Custom amount input
 * - Balance query
 * - Payment processing
 * - Recharge (if authorized)
 */
public class CashierActivity extends AppCompatActivity {
    private static final String TAG = "CashierActivity";
    private static final String SECRET_KEY = "your_secret_key_here_change_this_in_production";
    
    // UI Components - Header
    private TextView eventNameText;
    private TextView boothNameText;
    private TextView cashierNameText;
    
    // UI Components - Card Info
    private View cardInfoSection;
    private TextView cardUidText;
    private TextView participantNameText;
    private TextView balanceText;
    private ProgressBar cardLoadingProgress;
    
    // UI Components - Products
    private View productsSection;
    private RecyclerView productsRecyclerView;
    private ProductAdapter productAdapter;
    private List<Product> productList = new ArrayList<>();
    
    // UI Components - Shopping Cart
    private View cartSection;
    private RecyclerView cartRecyclerView;
    private CartAdapter cartAdapter;
    private List<CartItem> cartItems = new ArrayList<>();
    private TextView cartTotalText;
    
    // UI Components - Custom Amount
    private View customAmountSection;
    private EditText customAmountInput;
    private EditText customRemarkInput;
    
    // UI Components - Actions
    private Button queryBalanceButton;
    private Button payButton;
    private Button rechargeButton;
    private Button clearButton;
    
    // UI Components - Status
    private TextView statusText;
    private ProgressBar actionProgress;
    
    // NFC and API
    private NFCReader nfcReader;
    private WalletAPIService apiService;
    private SessionManager sessionManager;
    
    // Current state
    private String currentCardUid;
    private ParticipantInfo currentParticipant;
    private double currentBalance;
    private EventInfo currentEvent;
    private BoothInfo currentBooth;
    private UserInfo currentUser;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_cashier);
        
        // Initialize components
        initializeViews();
        initializeServices();
        
        // Check login status
        if (!sessionManager.isLoggedIn()) {
            showError("请先登录");
            finish();
            return;
        }
        
        // Initialize NFC
        try {
            nfcReader = new NFCReader(this);
        } catch (NFCReader.NFCNotSupportedException e) {
            showError("设备不支持 NFC");
            finish();
            return;
        } catch (NFCReader.NFCDisabledException e) {
            showError("请在设置中启用 NFC");
            finish();
            return;
        }
        
        // Load initial data
        loadUserInfo();
        loadBoothInfo();
    }
    
    private void initializeViews() {
        // Header
        eventNameText = findViewById(R.id.eventNameText);
        boothNameText = findViewById(R.id.boothNameText);
        cashierNameText = findViewById(R.id.cashierNameText);
        
        // Card Info
        cardInfoSection = findViewById(R.id.cardInfoSection);
        cardUidText = findViewById(R.id.cardUidText);
        participantNameText = findViewById(R.id.participantNameText);
        balanceText = findViewById(R.id.balanceText);
        cardLoadingProgress = findViewById(R.id.cardLoadingProgress);
        
        // Products
        productsSection = findViewById(R.id.productsSection);
        productsRecyclerView = findViewById(R.id.productsRecyclerView);
        productsRecyclerView.setLayoutManager(new GridLayoutManager(this, 3));
        productAdapter = new ProductAdapter(productList, this::onProductClick);
        productsRecyclerView.setAdapter(productAdapter);
        
        // Shopping Cart
        cartSection = findViewById(R.id.cartSection);
        cartRecyclerView = findViewById(R.id.cartRecyclerView);
        cartRecyclerView.setLayoutManager(new LinearLayoutManager(this));
        cartAdapter = new CartAdapter(cartItems, this::onCartItemChange, this::onCartItemRemove);
        cartRecyclerView.setAdapter(cartAdapter);
        cartTotalText = findViewById(R.id.cartTotalText);
        
        // Custom Amount
        customAmountSection = findViewById(R.id.customAmountSection);
        customAmountInput = findViewById(R.id.customAmountInput);
        customRemarkInput = findViewById(R.id.customRemarkInput);
        
        // Actions
        queryBalanceButton = findViewById(R.id.queryBalanceButton);
        payButton = findViewById(R.id.payButton);
        rechargeButton = findViewById(R.id.rechargeButton);
        clearButton = findViewById(R.id.clearButton);
        
        // Status
        statusText = findViewById(R.id.statusText);
        actionProgress = findViewById(R.id.actionProgress);
        
        // Set button listeners
        queryBalanceButton.setOnClickListener(v -> queryBalance());
        payButton.setOnClickListener(v -> processPayment());
        rechargeButton.setOnClickListener(v -> processRecharge());
        clearButton.setOnClickListener(v -> clearCard());
        
        // Initially hide sections
        cardInfoSection.setVisibility(View.GONE);
        productsSection.setVisibility(View.GONE);
        cartSection.setVisibility(View.GONE);
        customAmountSection.setVisibility(View.GONE);
    }
    
    private void initializeServices() {
        apiService = APIClient.getAPIService();
        sessionManager = new SessionManager(this);
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        
        // Enable NFC reader
        if (nfcReader != null) {
            nfcReader.enableReaderMode(this, new NFCReader.NFCCallback() {
                @Override
                public void onCardDetected(String uid) {
                    runOnUiThread(() -> handleCardDetected(uid));
                }
                
                @Override
                public void onError(String error) {
                    runOnUiThread(() -> showError(error));
                }
            });
        }
    }
    
    @Override
    protected void onPause() {
        super.onPause();
        
        // Disable NFC reader
        if (nfcReader != null) {
            nfcReader.disableReaderMode(this);
        }
    }
    
    /**
     * Load current user info.
     */
    private void loadUserInfo() {
        currentUser = sessionManager.getUserInfo();
        if (currentUser != null) {
            cashierNameText.setText(currentUser.getUsername());
        }
    }
    
    /**
     * Load booth info and products.
     */
    private void loadBoothInfo() {
        // Get booth_id from intent or session
        int boothId = getIntent().getIntExtra("booth_id", 0);
        if (boothId == 0) {
            showError("未指定摊位");
            return;
        }
        
        String authHeader = sessionManager.getAuthHeader();
        if (authHeader == null) {
            showError("未登录");
            return;
        }
        
        // Load booth info
        Call<BoothInfo> boothCall = apiService.getBooth(authHeader, boothId);
        boothCall.enqueue(new Callback<BoothInfo>() {
            @Override
            public void onResponse(Call<BoothInfo> call, Response<BoothInfo> response) {
                if (response.isSuccessful() && response.body() != null) {
                    currentBooth = response.body();
                    boothNameText.setText(currentBooth.getName());
                    
                    // Load event info
                    loadEventInfo(currentBooth.getEventId());
                    
                    // Load products
                    loadProducts(boothId);
                } else {
                    String error = ErrorHandler.getErrorMessage(response);
                    showError(error);
                }
            }
            
            @Override
            public void onFailure(Call<BoothInfo> call, Throwable t) {
                Log.e(TAG, "Failed to load booth info", t);
                showError("加载摊位信息失败");
            }
        });
    }
    
    /**
     * Load event info.
     */
    private void loadEventInfo(int eventId) {
        Call<EventInfo> call = apiService.getEvent(eventId);
        call.enqueue(new Callback<EventInfo>() {
            @Override
            public void onResponse(Call<EventInfo> call, Response<EventInfo> response) {
                if (response.isSuccessful() && response.body() != null) {
                    currentEvent = response.body();
                    eventNameText.setText(currentEvent.getName());
                }
            }
            
            @Override
            public void onFailure(Call<EventInfo> call, Throwable t) {
                Log.e(TAG, "Failed to load event info", t);
            }
        });
    }
    
    /**
     * Load products for booth.
     */
    private void loadProducts(int boothId) {
        String authHeader = sessionManager.getAuthHeader();
        if (authHeader == null) return;
        
        Call<List<Product>> call = apiService.getProducts(authHeader, boothId, true);
        call.enqueue(new Callback<List<Product>>() {
            @Override
            public void onResponse(Call<List<Product>> call, Response<List<Product>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    productList.clear();
                    productList.addAll(response.body());
                    productAdapter.notifyDataSetChanged();
                    
                    if (!productList.isEmpty()) {
                        productsSection.setVisibility(View.VISIBLE);
                    }
                }
            }
            
            @Override
            public void onFailure(Call<List<Product>> call, Throwable t) {
                Log.e(TAG, "Failed to load products", t);
            }
        });
    }
    
    /**
     * Handle NFC card detected.
     */
    private void handleCardDetected(String uid) {
        Log.d(TAG, "Card detected: " + uid);
        
        currentCardUid = uid;
        cardUidText.setText(uid);
        cardInfoSection.setVisibility(View.VISIBLE);
        cardLoadingProgress.setVisibility(View.VISIBLE);
        
        // Clear previous data
        participantNameText.setText("查询中...");
        balanceText.setText("--");
        
        // Query participant info
        queryParticipant(uid);
    }
    
    /**
     * Query participant by card UID.
     */
    private void queryParticipant(String cardUid) {
        Call<ParticipantInfo> call = apiService.getParticipantByCard(cardUid);
        call.enqueue(new Callback<ParticipantInfo>() {
            @Override
            public void onResponse(Call<ParticipantInfo> call, Response<ParticipantInfo> response) {
                if (response.isSuccessful() && response.body() != null) {
                    currentParticipant = response.body();
                    participantNameText.setText(currentParticipant.getName());
                    
                    // Auto query balance
                    queryBalance();
                } else {
                    cardLoadingProgress.setVisibility(View.GONE);
                    
                    // Check if participant not found (404 or specific error code)
                    if (response.code() == 400 || response.code() == 404) {
                        // Show dialog to create new participant
                        participantNameText.setText("未绑定");
                        showCreateParticipantDialog(cardUid);
                    } else {
                        String error = ErrorHandler.getErrorMessage(response);
                        participantNameText.setText("查询失败");
                        showError(error);
                    }
                }
            }
            
            @Override
            public void onFailure(Call<ParticipantInfo> call, Throwable t) {
                cardLoadingProgress.setVisibility(View.GONE);
                Log.e(TAG, "Failed to query participant", t);
                participantNameText.setText("查询失败");
                showError("网络错误");
            }
        });
    }
    
    /**
     * Query balance using event mode.
     */
    private void queryBalance() {
        if (currentCardUid == null) {
            showError("请先刷卡");
            return;
        }
        
        if (currentEvent == null) {
            showError("活动信息未加载");
            return;
        }
        
        cardLoadingProgress.setVisibility(View.VISIBLE);
        
        // Use new event mode API
        Call<BalanceResponse> call = apiService.getBalanceByEvent(
            currentEvent.getId(),
            currentCardUid
        );
        
        call.enqueue(new Callback<BalanceResponse>() {
            @Override
            public void onResponse(Call<BalanceResponse> call, Response<BalanceResponse> response) {
                cardLoadingProgress.setVisibility(View.GONE);
                
                if (response.isSuccessful() && response.body() != null) {
                    currentBalance = response.body().getBalance();
                    balanceText.setText(String.format("¥%.2f", currentBalance));
                    
                    // Show action sections
                    customAmountSection.setVisibility(View.VISIBLE);
                    
                    // Show recharge button only if user has permission
                    updateRechargeButtonVisibility();
                } else {
                    String error = ErrorHandler.getErrorMessage(response);
                    showError(error);
                }
            }
            
            @Override
            public void onFailure(Call<BalanceResponse> call, Throwable t) {
                cardLoadingProgress.setVisibility(View.GONE);
                Log.e(TAG, "Failed to query balance", t);
                showError("网络错误");
            }
        });
    }
    
    /**
     * Handle product click.
     */
    private void onProductClick(Product product) {
        if (!product.isAvailable()) {
            showError("商品不可用");
            return;
        }
        
        // Check if product already in cart
        for (CartItem item : cartItems) {
            if (item.getProduct().getId() == product.getId()) {
                item.setQuantity(item.getQuantity() + 1);
                cartAdapter.notifyDataSetChanged();
                updateCartTotal();
                return;
            }
        }
        
        // Add new item to cart
        CartItem newItem = new CartItem(product, 1);
        cartItems.add(newItem);
        cartAdapter.notifyDataSetChanged();
        cartSection.setVisibility(View.VISIBLE);
        updateCartTotal();
    }
    
    /**
     * Handle cart item quantity change.
     */
    private void onCartItemChange(CartItem item, int newQuantity) {
        if (newQuantity <= 0) {
            cartItems.remove(item);
        } else {
            item.setQuantity(newQuantity);
        }
        cartAdapter.notifyDataSetChanged();
        updateCartTotal();
        
        if (cartItems.isEmpty()) {
            cartSection.setVisibility(View.GONE);
        }
    }
    
    /**
     * Handle cart item remove.
     */
    private void onCartItemRemove(CartItem item) {
        cartItems.remove(item);
        cartAdapter.notifyDataSetChanged();
        updateCartTotal();
        
        if (cartItems.isEmpty()) {
            cartSection.setVisibility(View.GONE);
        }
    }
    
    /**
     * Update cart total.
     */
    private void updateCartTotal() {
        int totalCents = 0;
        for (CartItem item : cartItems) {
            totalCents += item.getTotalPrice();
        }
        cartTotalText.setText(String.format("合计: ¥%.2f", totalCents / 100.0));
    }
    
    /**
     * Process payment.
     */
    private void processPayment() {
        if (currentCardUid == null || currentParticipant == null) {
            showError("请先刷卡");
            return;
        }
        
        // Calculate total amount
        int totalCents = 0;
        String remark = "";
        
        if (!cartItems.isEmpty()) {
            // Cart mode
            for (CartItem item : cartItems) {
                totalCents += item.getTotalPrice();
            }
        } else {
            // Custom amount mode
            String amountStr = customAmountInput.getText().toString().trim();
            if (amountStr.isEmpty()) {
                showError("请输入金额或选择商品");
                return;
            }
            
            try {
                double amount = Double.parseDouble(amountStr);
                totalCents = (int) (amount * 100);
                remark = customRemarkInput.getText().toString().trim();
            } catch (NumberFormatException e) {
                showError("金额格式错误");
                return;
            }
        }
        
        if (totalCents <= 0) {
            showError("金额必须大于 0");
            return;
        }
        
        // Check balance
        if (totalCents > currentBalance * 100) {
            showError("余额不足");
            return;
        }
        
        // Make variables effectively final for lambda
        final int finalTotalCents = totalCents;
        final String finalRemark = remark;
        
        // Confirm payment
        double totalYuan = totalCents / 100.0;
        new AlertDialog.Builder(this)
            .setTitle("确认支付")
            .setMessage(String.format("支付金额: ¥%.2f\n当前余额: ¥%.2f", totalYuan, currentBalance))
            .setPositiveButton("确认", (dialog, which) -> executePayment(finalTotalCents, finalRemark))
            .setNegativeButton("取消", null)
            .show();
    }
    
    /**
     * Execute payment.
     */
    private void executePayment(int amountCents, String remark) {
        String authHeader = sessionManager.getAuthHeader();
        if (authHeader == null) {
            showError("未登录");
            return;
        }
        
        actionProgress.setVisibility(View.VISIBLE);
        payButton.setEnabled(false);
        
        // Calculate total amount in yuan
        double totalAmount = amountCents / 100.0;
        
        // For cart items, we'll use the first product's ID if available
        Integer productId = null;
        if (!cartItems.isEmpty()) {
            productId = cartItems.get(0).getProduct().getId();
        }
        
        BoothPaymentRequest request = new BoothPaymentRequest(
            currentBooth.getEventId(),
            currentCardUid,
            totalAmount,
            productId,
            remark.isEmpty() ? null : remark
        );
        
        Call<TransactionResponse> call = apiService.processBoothPayment(
            authHeader,
            currentBooth.getId(),
            request
        );
        
        call.enqueue(new Callback<TransactionResponse>() {
            @Override
            public void onResponse(Call<TransactionResponse> call, Response<TransactionResponse> response) {
                actionProgress.setVisibility(View.GONE);
                payButton.setEnabled(true);
                
                if (response.isSuccessful() && response.body() != null) {
                    TransactionResponse result = response.body();
                    currentBalance = result.getNewBalance();
                    balanceText.setText(String.format("¥%.2f", currentBalance));
                    
                    showSuccess(String.format("支付成功\n新余额: ¥%.2f", currentBalance));
                    
                    // Clear cart and input
                    cartItems.clear();
                    cartAdapter.notifyDataSetChanged();
                    cartSection.setVisibility(View.GONE);
                    customAmountInput.setText("");
                    customRemarkInput.setText("");
                } else {
                    String error = ErrorHandler.getErrorMessage(response);
                    showError(error);
                }
            }
            
            @Override
            public void onFailure(Call<TransactionResponse> call, Throwable t) {
                actionProgress.setVisibility(View.GONE);
                payButton.setEnabled(true);
                Log.e(TAG, "Payment failed", t);
                showError("网络错误");
            }
        });
    }
    
    /**
     * Process recharge.
     */
    private void processRecharge() {
        if (currentCardUid == null) {
            showError("请先刷卡");
            return;
        }
        
        String amountStr = customAmountInput.getText().toString().trim();
        if (amountStr.isEmpty()) {
            showError("请输入充值金额");
            return;
        }
        
        double amount;
        try {
            amount = Double.parseDouble(amountStr);
        } catch (NumberFormatException e) {
            showError("金额格式错误");
            return;
        }
        
        if (amount <= 0) {
            showError("金额必须大于 0");
            return;
        }
        
        // Confirm recharge
        new AlertDialog.Builder(this)
            .setTitle("确认充值")
            .setMessage(String.format("充值金额: ¥%.2f", amount))
            .setPositiveButton("确认", (dialog, which) -> executeRecharge(amount))
            .setNegativeButton("取消", null)
            .show();
    }
    
    /**
     * Execute recharge.
     */
    private void executeRecharge(double amount) {
        actionProgress.setVisibility(View.VISIBLE);
        rechargeButton.setEnabled(false);
        
        long timestamp = SignatureGenerator.getCurrentTimestamp();
        String signature = SignatureGenerator.generateTransactionSignature(
            currentCardUid, amount, timestamp, SECRET_KEY
        );
        
        RechargeRequest request = new RechargeRequest(currentCardUid, amount, timestamp, signature);
        
        Call<TransactionResponse> call = apiService.processRecharge(request);
        call.enqueue(new Callback<TransactionResponse>() {
            @Override
            public void onResponse(Call<TransactionResponse> call, Response<TransactionResponse> response) {
                actionProgress.setVisibility(View.GONE);
                rechargeButton.setEnabled(true);
                
                if (response.isSuccessful() && response.body() != null) {
                    TransactionResponse result = response.body();
                    currentBalance = result.getNewBalance();
                    balanceText.setText(String.format("¥%.2f", currentBalance));
                    
                    showSuccess(String.format("充值成功\n新余额: ¥%.2f", currentBalance));
                    customAmountInput.setText("");
                } else {
                    String error = ErrorHandler.getErrorMessage(response);
                    showError(error);
                }
            }
            
            @Override
            public void onFailure(Call<TransactionResponse> call, Throwable t) {
                actionProgress.setVisibility(View.GONE);
                rechargeButton.setEnabled(true);
                Log.e(TAG, "Recharge failed", t);
                showError("网络错误");
            }
        });
    }
    
    /**
     * Clear card info.
     */
    private void clearCard() {
        currentCardUid = null;
        currentParticipant = null;
        currentBalance = 0;
        
        cardInfoSection.setVisibility(View.GONE);
        productsSection.setVisibility(View.VISIBLE);
        cartSection.setVisibility(View.GONE);
        customAmountSection.setVisibility(View.GONE);
        
        cartItems.clear();
        cartAdapter.notifyDataSetChanged();
        customAmountInput.setText("");
        customRemarkInput.setText("");
        statusText.setVisibility(View.GONE);
    }
    
    /**
     * Update recharge button visibility based on user permissions.
     */
    private void updateRechargeButtonVisibility() {
        if (currentUser != null && "admin".equals(currentUser.getRole())) {
            rechargeButton.setVisibility(View.VISIBLE);
        } else {
            rechargeButton.setVisibility(View.GONE);
        }
    }
    
    /**
     * Show dialog to create new participant.
     */
    private void showCreateParticipantDialog(String cardUid) {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("新卡片");
        builder.setMessage("卡片 " + cardUid + " 未绑定，是否创建新参与者？");
        
        // Create input layout
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(50, 40, 50, 10);
        
        // Name input
        final EditText nameInput = new EditText(this);
        nameInput.setHint("姓名（必填）");
        layout.addView(nameInput);
        
        // Class name input
        final EditText classInput = new EditText(this);
        classInput.setHint("班级（可选）");
        layout.addView(classInput);
        
        // Student number input
        final EditText studentNoInput = new EditText(this);
        studentNoInput.setHint("学号（可选）");
        layout.addView(studentNoInput);
        
        builder.setView(layout);
        
        builder.setPositiveButton("创建", (dialog, which) -> {
            String name = nameInput.getText().toString().trim();
            String className = classInput.getText().toString().trim();
            String studentNo = studentNoInput.getText().toString().trim();
            
            if (name.isEmpty()) {
                showError("姓名不能为空");
                return;
            }
            
            createParticipant(cardUid, name, className, studentNo);
        });
        
        builder.setNegativeButton("取消", (dialog, which) -> {
            dialog.dismiss();
            // Clear card info
            currentCardUid = null;
            currentParticipant = null;
            cardInfoSection.setVisibility(View.GONE);
        });
        
        builder.setCancelable(false);
        builder.show();
    }
    
    /**
     * Create new participant via API.
     */
    private void createParticipant(String cardUid, String name, String className, String studentNo) {
        String authHeader = sessionManager.getAuthHeader();
        if (authHeader == null) {
            showError("未登录");
            return;
        }
        
        cardLoadingProgress.setVisibility(View.VISIBLE);
        participantNameText.setText("创建中...");
        
        // Create request body
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("name", name);
        requestBody.put("card_uid", cardUid);
        requestBody.put("status", "active");
        
        if (!className.isEmpty()) {
            requestBody.put("class_name", className);
        }
        if (!studentNo.isEmpty()) {
            requestBody.put("student_no", studentNo);
        }
        
        // Make API call
        Call<ParticipantInfo> call = apiService.createParticipant(authHeader, requestBody);
        call.enqueue(new Callback<ParticipantInfo>() {
            @Override
            public void onResponse(Call<ParticipantInfo> call, Response<ParticipantInfo> response) {
                cardLoadingProgress.setVisibility(View.GONE);
                
                if (response.isSuccessful() && response.body() != null) {
                    currentParticipant = response.body();
                    participantNameText.setText(currentParticipant.getName());
                    showSuccess("参与者创建成功");
                    
                    // Query balance
                    queryBalance();
                } else {
                    String error = ErrorHandler.getErrorMessage(response);
                    participantNameText.setText("创建失败");
                    showError("创建失败: " + error);
                }
            }
            
            @Override
            public void onFailure(Call<ParticipantInfo> call, Throwable t) {
                cardLoadingProgress.setVisibility(View.GONE);
                Log.e(TAG, "Failed to create participant", t);
                participantNameText.setText("创建失败");
                showError("网络错误");
            }
        });
    }
    
    /**
     * Show error message.
     */
    private void showError(String message) {
        statusText.setText(message);
        statusText.setTextColor(getColor(R.color.error_red));
        statusText.setVisibility(View.VISIBLE);
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
        
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            statusText.setVisibility(View.GONE);
        }, 3000);
    }
    
    /**
     * Show success message.
     */
    private void showSuccess(String message) {
        statusText.setText(message);
        statusText.setTextColor(getColor(R.color.success_green));
        statusText.setVisibility(View.VISIBLE);
        
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            statusText.setVisibility(View.GONE);
        }, 3000);
    }
}
