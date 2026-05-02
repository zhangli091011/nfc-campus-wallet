package com.campus.nfcwallet.ui;

import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.campus.nfcwallet.R;
import com.campus.nfcwallet.api.APIClient;
import com.campus.nfcwallet.api.WalletAPIService;
import com.campus.nfcwallet.models.BalanceResponse;
import com.campus.nfcwallet.models.PaymentRequest;
import com.campus.nfcwallet.models.RechargeRequest;
import com.campus.nfcwallet.models.TransactionResponse;
import com.campus.nfcwallet.nfc.NFCReader;
import com.campus.nfcwallet.signature.SignatureGenerator;
import com.google.android.material.textfield.TextInputEditText;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Main activity for NFC Campus E-Wallet.
 * 
 * Handles NFC card detection, balance queries, and transactions.
 */
public class MainActivity extends AppCompatActivity {
    private static final String TAG = "MainActivity";
    
    // Secret key for signature generation (must match backend .env file)
    private static final String SECRET_KEY = "dev_secret_key_change_this_in_production_12345678";
    
    // UI Components
    private TextView nfcPromptText;
    private TextView uidLabel;
    private TextView uidText;
    private TextView balanceLabel;
    private TextView balanceText;
    private TextInputEditText amountInput;
    private Button payButton;
    private Button rechargeButton;
    private Button viewHistoryButton;
    private Button clearButton;
    private TextView statusText;
    private ProgressBar progressBar;
    private View amountInputLayout;
    
    // NFC and API
    private NFCReader nfcReader;
    private WalletAPIService apiService;
    
    // Current state
    private String currentUid;
    private double currentBalance;
    private UIState currentState = UIState.IDLE;
    
    private enum UIState {
        IDLE,           // Waiting for card
        READING,        // Reading card
        PROCESSING,     // API call in progress
        SUCCESS,        // Operation successful
        ERROR           // Error occurred
    }
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        // Initialize UI components
        initializeViews();
        
        // Initialize API service
        apiService = APIClient.getAPIService();
        
        // Initialize NFC reader
        try {
            nfcReader = new NFCReader(this);
        } catch (NFCReader.NFCNotSupportedException e) {
            showError(getString(R.string.nfc_not_supported));
            finish();
            return;
        } catch (NFCReader.NFCDisabledException e) {
            showError(getString(R.string.nfc_disabled));
            finish();
            return;
        }
        
        // Set up button listeners
        setupButtonListeners();
    }
    
    private void initializeViews() {
        nfcPromptText = findViewById(R.id.nfcPromptText);
        uidLabel = findViewById(R.id.uidLabel);
        uidText = findViewById(R.id.uidText);
        balanceLabel = findViewById(R.id.balanceLabel);
        balanceText = findViewById(R.id.balanceText);
        amountInputLayout = findViewById(R.id.amountInputLayout);
        amountInput = findViewById(R.id.amountInput);
        payButton = findViewById(R.id.payButton);
        rechargeButton = findViewById(R.id.rechargeButton);
        viewHistoryButton = findViewById(R.id.viewHistoryButton);
        clearButton = findViewById(R.id.clearButton);
        statusText = findViewById(R.id.statusText);
        progressBar = findViewById(R.id.progressBar);
    }
    
    private void setupButtonListeners() {
        payButton.setOnClickListener(v -> processPayment());
        rechargeButton.setOnClickListener(v -> processRecharge());
        viewHistoryButton.setOnClickListener(v -> viewTransactionHistory());
        clearButton.setOnClickListener(v -> clearDisplay());
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
     * Handle NFC card detection.
     */
    private void handleCardDetected(String uid) {
        Log.d(TAG, "Card detected: " + uid);
        
        currentUid = uid;
        updateUIState(UIState.READING);
        
        // Display UID
        uidText.setText(uid);
        uidLabel.setVisibility(View.VISIBLE);
        uidText.setVisibility(View.VISIBLE);
        
        // Query balance
        queryBalance(uid);
    }
    
    /**
     * Query user balance from backend.
     */
    private void queryBalance(String uid) {
        updateUIState(UIState.PROCESSING);
        
        long timestamp = SignatureGenerator.getCurrentTimestamp();
        String signature = SignatureGenerator.generateBalanceSignature(uid, timestamp, SECRET_KEY);
        
        Call<BalanceResponse> call = apiService.getBalance(uid, timestamp, signature);
        call.enqueue(new Callback<BalanceResponse>() {
            @Override
            public void onResponse(Call<BalanceResponse> call, Response<BalanceResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    currentBalance = response.body().getBalance();
                    displayBalance(currentBalance);
                    updateUIState(UIState.SUCCESS);
                } else {
                    String error = APIClient.getErrorMessage(response);
                    showError(error);
                    updateUIState(UIState.ERROR);
                }
            }
            
            @Override
            public void onFailure(Call<BalanceResponse> call, Throwable t) {
                Log.e(TAG, "Balance query failed", t);
                showError(getString(R.string.network_error));
                updateUIState(UIState.ERROR);
            }
        });
    }
    
    /**
     * Display balance and show transaction controls.
     */
    private void displayBalance(double balance) {
        balanceText.setText(String.format("¥%.2f", balance));
        balanceLabel.setVisibility(View.VISIBLE);
        balanceText.setVisibility(View.VISIBLE);
        
        // Show transaction controls
        amountInputLayout.setVisibility(View.VISIBLE);
        payButton.setVisibility(View.VISIBLE);
        rechargeButton.setVisibility(View.VISIBLE);
        viewHistoryButton.setVisibility(View.VISIBLE);
        clearButton.setVisibility(View.VISIBLE);
    }
    
    /**
     * Process payment transaction.
     */
    private void processPayment() {
        String amountStr = amountInput.getText().toString().trim();
        
        if (amountStr.isEmpty()) {
            showError(getString(R.string.invalid_amount));
            return;
        }
        
        double amount;
        try {
            amount = Double.parseDouble(amountStr);
        } catch (NumberFormatException e) {
            showError(getString(R.string.invalid_amount));
            return;
        }
        
        if (amount <= 0) {
            showError(getString(R.string.invalid_amount));
            return;
        }
        
        if (amount > 10000) {
            showError(getString(R.string.amount_too_large));
            return;
        }
        
        updateUIState(UIState.PROCESSING);
        
        long timestamp = SignatureGenerator.getCurrentTimestamp();
        String signature = SignatureGenerator.generateTransactionSignature(
            currentUid, amount, timestamp, SECRET_KEY
        );
        
        PaymentRequest request = new PaymentRequest(currentUid, amount, timestamp, signature);
        
        Call<TransactionResponse> call = apiService.processPayment(request);
        call.enqueue(new Callback<TransactionResponse>() {
            @Override
            public void onResponse(Call<TransactionResponse> call, Response<TransactionResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    TransactionResponse result = response.body();
                    currentBalance = result.getNewBalance();
                    displayTransactionSuccess("payment", result.getNewBalance());
                    amountInput.setText("");
                } else {
                    String error = APIClient.getErrorMessage(response);
                    showError(error);
                    updateUIState(UIState.ERROR);
                }
            }
            
            @Override
            public void onFailure(Call<TransactionResponse> call, Throwable t) {
                Log.e(TAG, "Payment failed", t);
                showError(getString(R.string.network_error));
                updateUIState(UIState.ERROR);
            }
        });
    }
    
    /**
     * Process recharge transaction.
     */
    private void processRecharge() {
        String amountStr = amountInput.getText().toString().trim();
        
        if (amountStr.isEmpty()) {
            showError(getString(R.string.invalid_amount));
            return;
        }
        
        double amount;
        try {
            amount = Double.parseDouble(amountStr);
        } catch (NumberFormatException e) {
            showError(getString(R.string.invalid_amount));
            return;
        }
        
        if (amount <= 0) {
            showError(getString(R.string.invalid_amount));
            return;
        }
        
        if (amount > 10000) {
            showError(getString(R.string.amount_too_large));
            return;
        }
        
        updateUIState(UIState.PROCESSING);
        
        long timestamp = SignatureGenerator.getCurrentTimestamp();
        String signature = SignatureGenerator.generateTransactionSignature(
            currentUid, amount, timestamp, SECRET_KEY
        );
        
        RechargeRequest request = new RechargeRequest(currentUid, amount, timestamp, signature);
        
        Call<TransactionResponse> call = apiService.processRecharge(request);
        call.enqueue(new Callback<TransactionResponse>() {
            @Override
            public void onResponse(Call<TransactionResponse> call, Response<TransactionResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    TransactionResponse result = response.body();
                    currentBalance = result.getNewBalance();
                    displayTransactionSuccess("recharge", result.getNewBalance());
                    amountInput.setText("");
                } else {
                    String error = APIClient.getErrorMessage(response);
                    showError(error);
                    updateUIState(UIState.ERROR);
                }
            }
            
            @Override
            public void onFailure(Call<TransactionResponse> call, Throwable t) {
                Log.e(TAG, "Recharge failed", t);
                showError(getString(R.string.network_error));
                updateUIState(UIState.ERROR);
            }
        });
    }
    
    /**
     * Display transaction success message.
     */
    private void displayTransactionSuccess(String type, double newBalance) {
        updateUIState(UIState.SUCCESS);
        
        String message = type.equals("payment") ? 
            getString(R.string.payment_success) : 
            getString(R.string.recharge_success);
        
        statusText.setText(message + "\n" + String.format(getString(R.string.new_balance), newBalance));
        statusText.setTextColor(getColor(R.color.success_green));
        statusText.setVisibility(View.VISIBLE);
        
        // Update balance display
        balanceText.setText(String.format("¥%.2f", newBalance));
        
        // Auto-clear after 5 seconds
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            if (currentState == UIState.SUCCESS) {
                statusText.setVisibility(View.GONE);
            }
        }, 5000);
    }
    
    /**
     * Show error message.
     */
    private void showError(String message) {
        statusText.setText(message);
        statusText.setTextColor(getColor(R.color.error_red));
        statusText.setVisibility(View.VISIBLE);
        
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
        
        // Auto-clear after 5 seconds
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            if (currentState == UIState.ERROR) {
                statusText.setVisibility(View.GONE);
            }
        }, 5000);
    }
    
    /**
     * View transaction history.
     */
    private void viewTransactionHistory() {
        Intent intent = new Intent(this, TransactionHistoryActivity.class);
        intent.putExtra("uid", currentUid);
        startActivity(intent);
    }
    
    /**
     * Clear display and reset to idle state.
     */
    private void clearDisplay() {
        currentUid = null;
        currentBalance = 0;
        
        uidLabel.setVisibility(View.GONE);
        uidText.setVisibility(View.GONE);
        balanceLabel.setVisibility(View.GONE);
        balanceText.setVisibility(View.GONE);
        amountInputLayout.setVisibility(View.GONE);
        payButton.setVisibility(View.GONE);
        rechargeButton.setVisibility(View.GONE);
        viewHistoryButton.setVisibility(View.GONE);
        clearButton.setVisibility(View.GONE);
        statusText.setVisibility(View.GONE);
        progressBar.setVisibility(View.GONE);
        
        amountInput.setText("");
        
        updateUIState(UIState.IDLE);
    }
    
    /**
     * Update UI state.
     */
    private void updateUIState(UIState newState) {
        currentState = newState;
        
        switch (newState) {
            case IDLE:
                nfcPromptText.setText(R.string.tap_card_prompt);
                nfcPromptText.setTextColor(getColor(R.color.primary_blue));
                progressBar.setVisibility(View.GONE);
                break;
                
            case READING:
                nfcPromptText.setText(R.string.reading_card);
                nfcPromptText.setTextColor(getColor(R.color.warning_orange));
                progressBar.setVisibility(View.VISIBLE);
                break;
                
            case PROCESSING:
                nfcPromptText.setText(R.string.processing);
                nfcPromptText.setTextColor(getColor(R.color.warning_orange));
                progressBar.setVisibility(View.VISIBLE);
                payButton.setEnabled(false);
                rechargeButton.setEnabled(false);
                break;
                
            case SUCCESS:
                nfcPromptText.setText(R.string.tap_card_prompt);
                nfcPromptText.setTextColor(getColor(R.color.success_green));
                progressBar.setVisibility(View.GONE);
                payButton.setEnabled(true);
                rechargeButton.setEnabled(true);
                break;
                
            case ERROR:
                nfcPromptText.setText(R.string.tap_card_prompt);
                nfcPromptText.setTextColor(getColor(R.color.error_red));
                progressBar.setVisibility(View.GONE);
                payButton.setEnabled(true);
                rechargeButton.setEnabled(true);
                break;
        }
    }
}
