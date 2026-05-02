package com.campus.nfcwallet.ui;

import android.content.Intent;
import android.os.Bundle;
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
import com.campus.nfcwallet.models.LoginRequest;
import com.campus.nfcwallet.models.LoginResponse;
import com.campus.nfcwallet.utils.ErrorHandler;
import com.campus.nfcwallet.utils.SessionManager;
import com.google.android.material.textfield.TextInputEditText;

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
            navigateToCashier();
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
                    
                    // Navigate to cashier activity
                    navigateToCashier();
                } else {
                    String errorMessage = APIClient.getErrorMessage(response);
                    showError(errorMessage);
                }
            }
            
            @Override
            public void onFailure(Call<LoginResponse> call, Throwable t) {
                setLoading(false);
                Log.e(TAG, "Login failed", t);
                showError(getString(R.string.error_network));
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
}
