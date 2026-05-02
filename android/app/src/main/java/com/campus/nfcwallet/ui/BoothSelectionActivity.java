package com.campus.nfcwallet.ui;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
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
import com.campus.nfcwallet.models.BoothInfo;
import com.campus.nfcwallet.utils.ErrorHandler;
import com.campus.nfcwallet.utils.SessionManager;

import java.util.ArrayList;
import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Activity for selecting booth to operate.
 */
public class BoothSelectionActivity extends AppCompatActivity {
    private static final String TAG = "BoothSelectionActivity";
    
    private RecyclerView boothsRecyclerView;
    private ProgressBar progressBar;
    private TextView errorText;
    private BoothListAdapter adapter;
    
    private WalletAPIService apiService;
    private SessionManager sessionManager;
    private List<BoothInfo> booths = new ArrayList<>();
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_booth_selection);
        
        // Initialize views
        boothsRecyclerView = findViewById(R.id.boothsRecyclerView);
        progressBar = findViewById(R.id.progressBar);
        errorText = findViewById(R.id.errorText);
        
        // Initialize services
        apiService = APIClient.getAPIService();
        sessionManager = new SessionManager(this);
        
        // Check login
        if (!sessionManager.isLoggedIn()) {
            navigateToLogin();
            return;
        }
        
        // Setup RecyclerView
        boothsRecyclerView.setLayoutManager(new LinearLayoutManager(this));
        adapter = new BoothListAdapter(booths, this::onBoothSelected);
        boothsRecyclerView.setAdapter(adapter);
        
        // Load booths
        loadBooths();
    }
    
    private void loadBooths() {
        // For now, we'll need to get booth list from user's assigned booths
        // This is a simplified version - you may need to add an API endpoint
        // to get booths for current user
        
        // Temporary: Navigate directly to cashier with booth_id from intent or default
        int boothId = getIntent().getIntExtra("booth_id", 1);
        navigateToCashier(boothId);
    }
    
    private void onBoothSelected(BoothInfo booth) {
        navigateToCashier(booth.getId());
    }
    
    private void navigateToCashier(int boothId) {
        Intent intent = new Intent(this, CashierActivity.class);
        intent.putExtra("booth_id", boothId);
        startActivity(intent);
        finish();
    }
    
    private void navigateToLogin() {
        Intent intent = new Intent(this, LoginActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }
}
