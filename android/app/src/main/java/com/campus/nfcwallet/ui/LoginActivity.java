package com.campus.nfcwallet.ui;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;

import com.campus.nfcwallet.R;
import com.campus.nfcwallet.api.APIClient;
import com.campus.nfcwallet.api.WalletAPIService;
import com.campus.nfcwallet.models.LoginRequest;
import com.campus.nfcwallet.models.LoginResponse;
import com.campus.nfcwallet.models.SetStaffNameRequest;
import com.campus.nfcwallet.models.SetStaffNameResponse;
import com.campus.nfcwallet.models.UserInfo;
import com.campus.nfcwallet.utils.ErrorHandler;
import com.campus.nfcwallet.utils.SessionManager;
import com.google.android.material.textfield.TextInputEditText;
import com.google.android.material.textfield.TextInputLayout;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * Login activity for booth cashier authentication.
 */
public class LoginActivity extends AppCompatActivity {
    private static final String TAG = "LoginActivity";
    
    private TextInputEditText usernameInput;
    private TextInputEditText passwordInput;
    private Button loginButton;
    private ProgressBar progressBar;
    private TextView errorText;
    
    private WalletAPIService apiService;
    private SessionManager sessionManager;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);
        
        // Initialize views
        usernameInput = findViewById(R.id.usernameInput);
        passwordInput = findViewById(R.id.passwordInput);
        loginButton = findViewById(R.id.loginButton);
        progressBar = findViewById(R.id.progressBar);
        errorText = findViewById(R.id.errorText);
        
        // Initialize API service and session manager
        apiService = APIClient.getAPIService();
        sessionManager = new SessionManager(this);
        
        // Check if already logged in
        if (sessionManager.isLoggedIn()) {
            // Check if staff name still needs to be set
            UserInfo userInfo = sessionManager.getUserInfo();
            if (userInfo != null && userInfo.isStaffNameRequired()) {
                showStaffNameDialog();
            } else {
                navigateToCashier();
            }
            return;
        }
        
        // Set up login button
        loginButton.setOnClickListener(v -> performLogin());
    }
    
    private void performLogin() {
        String username = usernameInput.getText().toString().trim();
        String password = passwordInput.getText().toString().trim();
        
        // Validate input
        if (username.isEmpty()) {
            usernameInput.setError(getString(R.string.error_username_required));
            usernameInput.requestFocus();
            return;
        }
        
        if (password.isEmpty()) {
            passwordInput.setError(getString(R.string.error_password_required));
            passwordInput.requestFocus();
            return;
        }
        
        // Show loading
        setLoading(true);
        errorText.setVisibility(View.GONE);
        
        // Create login request
        LoginRequest request = new LoginRequest(username, password);
        
        // Call API
        Call<LoginResponse> call = apiService.login(request);
        call.enqueue(new Callback<LoginResponse>() {
            @Override
            public void onResponse(Call<LoginResponse> call, Response<LoginResponse> response) {
                setLoading(false);
                
                if (response.isSuccessful() && response.body() != null) {
                    LoginResponse loginResponse = response.body();
                    
                    // Save session
                    sessionManager.saveSession(
                        loginResponse.getAccessToken(),
                        loginResponse.getUser()
                    );
                    
                    Log.i(TAG, "Login successful: " + loginResponse.getUser().getUsername());
                    
                    // Check if staff name needs to be set (first login)
                    UserInfo user = loginResponse.getUser();
                    if (user.isStaffNameRequired()) {
                        showStaffNameDialog();
                    } else {
                        navigateToCashier();
                    }
                } else {
                    String errorMessage = APIClient.getErrorMessage(response);
                    String detailedError = ErrorHandler.getDetailedErrorMessage(response);
                    
                    showError(errorMessage);
                    
                    Log.e(TAG, "Login failed: " + errorMessage);
                    Log.e(TAG, "Detailed error:\n" + detailedError);
                }
            }
            
            @Override
            public void onFailure(Call<LoginResponse> call, Throwable t) {
                setLoading(false);
                
                String errorMsg = getString(R.string.error_network) + ": " + t.getMessage();
                showError(errorMsg);
                
                Log.e(TAG, "Login failed - Network error", t);
                Log.e(TAG, "Error type: " + t.getClass().getName());
                Log.e(TAG, "Error message: " + t.getMessage());
                
                if (t.getCause() != null) {
                    Log.e(TAG, "Caused by: " + t.getCause().getMessage());
                }
            }
        });
    }
    
    private void setLoading(boolean loading) {
        progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        loginButton.setEnabled(!loading);
        usernameInput.setEnabled(!loading);
        passwordInput.setEnabled(!loading);
    }
    
    private void showError(String message) {
        errorText.setText(message);
        errorText.setVisibility(View.VISIBLE);
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }
    
    private void navigateToCashier() {
        // For admin users, show booth selection
        // For booth users, go directly to their assigned booth
        Intent intent = new Intent(this, BoothSelectionActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }
    
    /**
     * Show dialog for staff to enter their real name on first login.
     * This dialog cannot be dismissed without entering a name.
     */
    private void showStaffNameDialog() {
        // Create input layout
        TextInputLayout inputLayout = new TextInputLayout(this);
        inputLayout.setHint("请输入您的真实姓名");
        inputLayout.setPadding(48, 16, 48, 0);
        
        TextInputEditText nameInput = new TextInputEditText(inputLayout.getContext());
        nameInput.setMaxLines(1);
        inputLayout.addView(nameInput);
        
        AlertDialog dialog = new AlertDialog.Builder(this)
            .setTitle("首次登录 - 设置姓名")
            .setMessage("请输入您的真实姓名，该姓名将用于系统记录和显示。")
            .setView(inputLayout)
            .setCancelable(false)
            .setPositiveButton("确认", null) // Set null to override later
            .create();
        
        dialog.show();
        
        // Override positive button to prevent dismiss on empty input
        dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            String staffName = nameInput.getText() != null ? 
                nameInput.getText().toString().trim() : "";
            
            if (staffName.isEmpty()) {
                nameInput.setError("姓名不能为空");
                nameInput.requestFocus();
                return;
            }
            
            if (staffName.length() > 50) {
                nameInput.setError("姓名不能超过50个字符");
                nameInput.requestFocus();
                return;
            }
            
            // Submit staff name to server
            submitStaffName(staffName, dialog);
        });
    }
    
    /**
     * Submit staff name to the server.
     */
    private void submitStaffName(String staffName, AlertDialog dialog) {
        dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(false);
        
        SetStaffNameRequest request = new SetStaffNameRequest(staffName);
        String authHeader = sessionManager.getAuthHeader();
        
        Call<SetStaffNameResponse> call = apiService.setStaffName(authHeader, request);
        call.enqueue(new Callback<SetStaffNameResponse>() {
            @Override
            public void onResponse(Call<SetStaffNameResponse> call, Response<SetStaffNameResponse> response) {
                dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(true);
                
                if (response.isSuccessful() && response.body() != null) {
                    // Update local session with staff name
                    UserInfo userInfo = sessionManager.getUserInfo();
                    if (userInfo != null) {
                        userInfo.setStaffName(response.body().getStaffName());
                        sessionManager.updateUserInfo(userInfo);
                    }
                    
                    Log.i(TAG, "Staff name set successfully: " + staffName);
                    Toast.makeText(LoginActivity.this, 
                        "姓名设置成功：" + staffName, Toast.LENGTH_SHORT).show();
                    
                    dialog.dismiss();
                    navigateToCashier();
                } else {
                    String errorMessage = APIClient.getErrorMessage(response);
                    Toast.makeText(LoginActivity.this, 
                        "设置失败：" + errorMessage, Toast.LENGTH_LONG).show();
                    Log.e(TAG, "Set staff name failed: " + errorMessage);
                }
            }
            
            @Override
            public void onFailure(Call<SetStaffNameResponse> call, Throwable t) {
                dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(true);
                Toast.makeText(LoginActivity.this, 
                    "网络错误，请重试", Toast.LENGTH_LONG).show();
                Log.e(TAG, "Set staff name network error", t);
            }
        });
    }
}
