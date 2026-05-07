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
        String authHeader = sessionManager.getAuthHeader();
        if (authHeader == null) {
            navigateToLogin();
            return;
        }
        
        progressBar.setVisibility(View.VISIBLE);
        errorText.setVisibility(View.GONE);
        
        // Load all active booths
        Call<List<BoothInfo>> call = apiService.getBooths(authHeader, "active");
        call.enqueue(new Callback<List<BoothInfo>>() {
            @Override
            public void onResponse(Call<List<BoothInfo>> call, Response<List<BoothInfo>> response) {
                progressBar.setVisibility(View.GONE);
                
                if (response.isSuccessful() && response.body() != null) {
                    booths.clear();
                    booths.addAll(response.body());
                    adapter.notifyDataSetChanged();
                    
                    if (booths.isEmpty()) {
                        errorText.setText("没有可用的摊位");
                        errorText.setVisibility(View.VISIBLE);
                    } else if (booths.size() == 1) {
                        // If only one booth, go directly to it
                        navigateToCashier(booths.get(0).getId());
                    }
                } else {
                    String error = ErrorHandler.getErrorMessage(response);
                    String detailedError = ErrorHandler.getDetailedErrorMessage(response);
                    
                    errorText.setText("加载摊位失败:\n" + error);
                    errorText.setVisibility(View.VISIBLE);
                    
                    Log.e(TAG, "Failed to load booths: " + error);
                    Log.e(TAG, "Detailed error:\n" + detailedError);
                    
                    Toast.makeText(BoothSelectionActivity.this, 
                        "错误详情已记录到日志", Toast.LENGTH_SHORT).show();
                }
            }
            
            @Override
            public void onFailure(Call<List<BoothInfo>> call, Throwable t) {
                progressBar.setVisibility(View.GONE);
                
                String errorMsg = "网络错误: " + t.getMessage();
                errorText.setText(errorMsg);
                errorText.setVisibility(View.VISIBLE);
                
                Log.e(TAG, "Failed to load booths - Network error", t);
                Log.e(TAG, "Error type: " + t.getClass().getName());
                Log.e(TAG, "Error message: " + t.getMessage());
                
                if (t.getCause() != null) {
                    Log.e(TAG, "Caused by: " + t.getCause().getMessage());
                }
                
                // Check if it's a JSON parsing error
                if (t.getMessage() != null && t.getMessage().contains("Expected BEGIN_ARRAY")) {
                    errorText.setText("服务器返回了错误的数据格式\n可能是服务器内部错误\n请联系管理员检查服务器日志");
                    Log.e(TAG, "JSON parsing error - server returned non-array response");
                    Log.e(TAG, "This usually means the server returned an error page or error message instead of JSON array");
                    Toast.makeText(BoothSelectionActivity.this, 
                        "服务器错误，请检查服务器状态", Toast.LENGTH_LONG).show();
                } else {
                    Toast.makeText(BoothSelectionActivity.this, 
                        "网络连接失败，请检查网络设置", Toast.LENGTH_LONG).show();
                }
            }
        });
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
