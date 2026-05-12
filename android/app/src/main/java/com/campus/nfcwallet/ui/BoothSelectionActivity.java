package com.campus.nfcwallet.ui;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
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
import com.campus.nfcwallet.models.BoothInfo;
import com.campus.nfcwallet.models.UserInfo;
import com.campus.nfcwallet.ui.investment.InvestmentComposeActivity;
import com.campus.nfcwallet.ui.bankTeller.BankTellerActivity;
import com.campus.nfcwallet.ui.refund.RefundManagerActivity;
import com.campus.nfcwallet.utils.ErrorHandler;
import com.campus.nfcwallet.utils.SessionManager;

import java.util.ArrayList;
import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Activity for selecting booth to operate.
 * 
 * For super_admin users: shows a role selection dialog first, allowing them
 * to enter the system as any role (cashier, bank_clerk, etc.)
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
    
    // Role selection items for super_admin
    private static final String[] ROLE_LABELS = {
        "🏪 摊位收银员（选择摊位）",
        "🏦 投资办理员（官方中央银行）",
        "💳 信用垫资发行（银行放贷）",
        "💰 充值员（官方中央银行）",
        "🔄 退款管理（摊位售后）",
        "📋 摊位列表（管理员视角）",
    };
    
    private static final String[] ROLE_KEYS = {
        "booth_cashier",
        "bank_clerk",
        "bank_teller",
        "issuer",
        "refund_manager",
        "admin_browse",
    };
    
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
        
        // Route based on role
        routeByRole();
    }
    
    /**
     * Route the user based on their role.
     * super_admin gets a role selection dialog.
     * Other roles go directly to their designated screen.
     */
    private void routeByRole() {
        if (sessionManager.getUserInfo() == null) {
            navigateToLogin();
            return;
        }
        
        String role = sessionManager.getUserInfo().getRole();
        Integer boothId = sessionManager.getUserInfo().getBoothId();
        
        switch (role) {
            case "super_admin":
                // Super admin can choose which role to enter as
                showRoleSelectionDialog();
                break;
                
            case "bank_clerk":
                // Investment counter operator
                Log.i(TAG, "Bank clerk role detected, navigating to Investment Screen");
                navigateToInvestment();
                break;
                
            case "issuer":
                // 充值员 - 直接进入官方中央银行摊位（带充值权限）
                Log.i(TAG, "Issuer role detected, navigating to Central Bank booth");
                navigateToCentralBankBooth();
                break;
                
            case "booth_cashier":
                // Booth cashier with assigned booth
                if (boothId != null && boothId > 0) {
                    Log.i(TAG, "Booth cashier with assigned booth " + boothId);
                    navigateToCashier(boothId);
                } else {
                    // No booth assigned, show booth list
                    loadBooths();
                }
                break;
                
            default:
                // event_admin, reviewer - show booth list
                loadBooths();
                break;
        }
    }
    
    /**
     * Show role selection dialog for super_admin users.
     */
    private void showRoleSelectionDialog() {
        new AlertDialog.Builder(this)
            .setTitle("选择进入模式")
            .setItems(ROLE_LABELS, (dialog, which) -> {
                String selectedRole = ROLE_KEYS[which];
                Log.i(TAG, "Super admin selected role: " + selectedRole);
                
                switch (selectedRole) {
                    case "booth_cashier":
                        // Show booth list for selection
                        loadBooths();
                        break;
                        
                    case "bank_clerk":
                        // Go to investment screen
                        navigateToInvestment();
                        break;
                        
                    case "bank_teller":
                        // Go to bank teller (credit advance) screen
                        navigateToBankTeller();
                        break;
                        
                    case "issuer":
                        // Go to Central Bank booth as recharger
                        navigateToCentralBankBooth();
                        break;
                        
                    case "refund_manager":
                        // Show booth list, then navigate to refund manager
                        loadBoothsForRefund();
                        break;
                        
                    case "admin_browse":
                        // Show booth list in browse mode (no auto-navigate)
                        loadBoothsForBrowse();
                        break;
                }
            })
            .setCancelable(false)
            .show();
    }
    
    /**
     * Load booths and auto-navigate if only one exists.
     */
    private void loadBooths() {
        String authHeader = sessionManager.getAuthHeader();
        if (authHeader == null) {
            navigateToLogin();
            return;
        }
        
        progressBar.setVisibility(View.VISIBLE);
        errorText.setVisibility(View.GONE);
        
        apiService.getBooths(authHeader, "active").enqueue(new Callback<List<BoothInfo>>() {
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
                        navigateToCashier(booths.get(0).getId());
                    }
                } else {
                    handleLoadError(response);
                }
            }
            
            @Override
            public void onFailure(Call<List<BoothInfo>> call, Throwable t) {
                handleNetworkError(t);
            }
        });
    }
    
    /**
     * Load booths for browsing (no auto-navigate, always show list).
     */
    private void loadBoothsForBrowse() {
        String authHeader = sessionManager.getAuthHeader();
        if (authHeader == null) {
            navigateToLogin();
            return;
        }
        
        progressBar.setVisibility(View.VISIBLE);
        errorText.setVisibility(View.GONE);
        
        apiService.getBooths(authHeader, "active").enqueue(new Callback<List<BoothInfo>>() {
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
                    }
                    // Always show list, don't auto-navigate
                } else {
                    handleLoadError(response);
                }
            }
            
            @Override
            public void onFailure(Call<List<BoothInfo>> call, Throwable t) {
                handleNetworkError(t);
            }
        });
    }
    
    private void handleLoadError(Response<List<BoothInfo>> response) {
        String error = ErrorHandler.getErrorMessage(response);
        String detailedError = ErrorHandler.getDetailedErrorMessage(response);
        
        errorText.setText("加载摊位失败:\n" + error);
        errorText.setVisibility(View.VISIBLE);
        
        Log.e(TAG, "Failed to load booths: " + error);
        Log.e(TAG, "Detailed error:\n" + detailedError);
        
        Toast.makeText(this, "错误详情已记录到日志", Toast.LENGTH_SHORT).show();
    }
    
    private void handleNetworkError(Throwable t) {
        progressBar.setVisibility(View.GONE);
        
        String errorMsg = "网络错误: " + t.getMessage();
        errorText.setText(errorMsg);
        errorText.setVisibility(View.VISIBLE);
        
        Log.e(TAG, "Failed to load booths - Network error", t);
        
        if (t.getMessage() != null && t.getMessage().contains("Expected BEGIN_ARRAY")) {
            errorText.setText("服务器返回了错误的数据格式\n可能是服务器内部错误\n请联系管理员检查服务器日志");
            Toast.makeText(this, "服务器错误，请检查服务器状态", Toast.LENGTH_LONG).show();
        } else {
            Toast.makeText(this, "网络连接失败，请检查网络设置", Toast.LENGTH_LONG).show();
        }
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
    
    private void navigateToInvestment() {
        Intent intent = new Intent(this, InvestmentComposeActivity.class);
        startActivity(intent);
        finish();
    }
    
    /**
     * Navigate issuer (充值员) directly to the Central Bank booth (官方中央银行).
     * Queries the booth list and finds the booth named "官方中央银行",
     * then enters CashierActivity with recharge permission.
     */
    private void navigateToCentralBankBooth() {
        String authHeader = sessionManager.getAuthHeader();
        if (authHeader == null) {
            navigateToLogin();
            return;
        }
        
        progressBar.setVisibility(View.VISIBLE);
        errorText.setVisibility(View.GONE);
        
        apiService.getBooths(authHeader, "active").enqueue(new Callback<List<BoothInfo>>() {
            @Override
            public void onResponse(Call<List<BoothInfo>> call, Response<List<BoothInfo>> response) {
                progressBar.setVisibility(View.GONE);
                
                if (response.isSuccessful() && response.body() != null) {
                    // Find the Central Bank booth
                    BoothInfo centralBankBooth = null;
                    for (BoothInfo booth : response.body()) {
                        if ("官方中央银行".equals(booth.getName())) {
                            centralBankBooth = booth;
                            break;
                        }
                    }
                    
                    if (centralBankBooth != null) {
                        Log.i(TAG, "Found Central Bank booth: ID=" + centralBankBooth.getId());
                        navigateToCashier(centralBankBooth.getId());
                    } else {
                        // Central Bank booth not found, fall back to booth list
                        Log.w(TAG, "Central Bank booth not found, showing booth list");
                        errorText.setText("未找到「官方中央银行」摊位\n请联系管理员创建");
                        errorText.setVisibility(View.VISIBLE);
                        
                        // Show all booths as fallback
                        booths.clear();
                        booths.addAll(response.body());
                        adapter.notifyDataSetChanged();
                    }
                } else {
                    handleLoadError(response);
                }
            }
            
            @Override
            public void onFailure(Call<List<BoothInfo>> call, Throwable t) {
                handleNetworkError(t);
            }
        });
    }
    
    private void navigateToBankTeller() {
        Intent intent = new Intent(this, BankTellerActivity.class);
        startActivity(intent);
        finish();
    }
    
    private void navigateToRefundManager(int boothId) {
        Intent intent = new Intent(this, RefundManagerActivity.class);
        intent.putExtra("booth_id", boothId);
        startActivity(intent);
        finish();
    }
    
    /**
     * Load booths for refund manager selection.
     */
    private void loadBoothsForRefund() {
        String authHeader = sessionManager.getAuthHeader();
        if (authHeader == null) {
            navigateToLogin();
            return;
        }
        
        progressBar.setVisibility(View.VISIBLE);
        errorText.setVisibility(View.GONE);
        
        apiService.getBooths(authHeader, "active").enqueue(new Callback<List<BoothInfo>>() {
            @Override
            public void onResponse(Call<List<BoothInfo>> call, Response<List<BoothInfo>> response) {
                progressBar.setVisibility(View.GONE);
                
                if (response.isSuccessful() && response.body() != null) {
                    List<BoothInfo> boothList = response.body();
                    if (boothList.isEmpty()) {
                        errorText.setText("没有可用的摊位");
                        errorText.setVisibility(View.VISIBLE);
                    } else if (boothList.size() == 1) {
                        navigateToRefundManager(boothList.get(0).getId());
                    } else {
                        // Show booth selection for refund
                        booths.clear();
                        booths.addAll(boothList);
                        adapter = new BoothListAdapter(booths, booth -> navigateToRefundManager(booth.getId()));
                        boothsRecyclerView.setAdapter(adapter);
                    }
                } else {
                    handleLoadError(response);
                }
            }
            
            @Override
            public void onFailure(Call<List<BoothInfo>> call, Throwable t) {
                handleNetworkError(t);
            }
        });
    }
    
    private void navigateToLogin() {
        Intent intent = new Intent(this, LoginActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }
    

}
