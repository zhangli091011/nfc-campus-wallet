package com.campus.nfcwallet.ui;

import android.os.Bundle;
import android.util.Log;
import android.view.MenuItem;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.campus.nfcwallet.R;
import com.campus.nfcwallet.api.APIClient;
import com.campus.nfcwallet.api.WalletAPIService;
import com.campus.nfcwallet.models.Transaction;
import com.campus.nfcwallet.models.TransactionHistoryResponse;

import java.util.ArrayList;
import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Activity to display transaction history for a user.
 */
public class TransactionHistoryActivity extends AppCompatActivity {
    private static final String TAG = "TransactionHistory";
    
    private TextView uidText;
    private TextView emptyText;
    private ProgressBar progressBar;
    private RecyclerView recyclerView;
    private TransactionAdapter adapter;
    
    private WalletAPIService apiService;
    private String uid;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_transaction_history);
        
        // Enable back button
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
        }
        
        // Get UID from intent
        uid = getIntent().getStringExtra("uid");
        
        // Initialize views
        uidText = findViewById(R.id.uidText);
        emptyText = findViewById(R.id.emptyText);
        progressBar = findViewById(R.id.progressBar);
        recyclerView = findViewById(R.id.transactionRecyclerView);
        
        // Display UID
        uidText.setText("UID: " + uid);
        
        // Set up RecyclerView
        recyclerView.setLayoutManager(new LinearLayoutManager(this));
        adapter = new TransactionAdapter(new ArrayList<>());
        recyclerView.setAdapter(adapter);
        
        // Initialize API service
        apiService = APIClient.getAPIService();
        
        // Load transaction history
        loadTransactionHistory();
    }
    
    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        if (item.getItemId() == android.R.id.home) {
            finish();
            return true;
        }
        return super.onOptionsItemSelected(item);
    }
    
    /**
     * Load transaction history from backend.
     */
    private void loadTransactionHistory() {
        progressBar.setVisibility(View.VISIBLE);
        emptyText.setVisibility(View.GONE);
        recyclerView.setVisibility(View.GONE);
        
        Call<TransactionHistoryResponse> call = apiService.getTransactionHistory(uid, null, null);
        call.enqueue(new Callback<TransactionHistoryResponse>() {
            @Override
            public void onResponse(Call<TransactionHistoryResponse> call, Response<TransactionHistoryResponse> response) {
                progressBar.setVisibility(View.GONE);
                
                if (response.isSuccessful() && response.body() != null) {
                    List<Transaction> transactions = response.body().getTransactions();
                    
                    if (transactions == null || transactions.isEmpty()) {
                        emptyText.setVisibility(View.VISIBLE);
                    } else {
                        adapter.updateTransactions(transactions);
                        recyclerView.setVisibility(View.VISIBLE);
                    }
                } else {
                    String error = APIClient.getErrorMessage(response);
                    Toast.makeText(TransactionHistoryActivity.this, error, Toast.LENGTH_LONG).show();
                    emptyText.setVisibility(View.VISIBLE);
                }
            }
            
            @Override
            public void onFailure(Call<TransactionHistoryResponse> call, Throwable t) {
                Log.e(TAG, "Failed to load transaction history", t);
                progressBar.setVisibility(View.GONE);
                Toast.makeText(
                    TransactionHistoryActivity.this,
                    getString(R.string.network_error),
                    Toast.LENGTH_LONG
                ).show();
                emptyText.setVisibility(View.VISIBLE);
            }
        });
    }
}
