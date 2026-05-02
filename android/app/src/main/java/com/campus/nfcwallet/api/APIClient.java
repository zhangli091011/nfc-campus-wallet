package com.campus.nfcwallet.api;

import android.util.Log;

import com.campus.nfcwallet.models.ErrorResponse;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.IOException;
import java.util.concurrent.TimeUnit;

import okhttp3.OkHttpClient;
import okhttp3.logging.HttpLoggingInterceptor;
import retrofit2.Response;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

/**
 * API client for NFC Campus E-Wallet backend.
 * 
 * Provides configured Retrofit instance and error handling utilities.
 */
public class APIClient {
    private static final String TAG = "APIClient";
    
    // TODO: Replace with your actual backend URL
    private static final String BASE_URL = "http://49.235.143.45:8001/";  // Android emulator localhost
    // For physical device, use: "http://YOUR_COMPUTER_IP:8000/"
    
    private static Retrofit retrofit = null;
    private static WalletAPIService apiService = null;
    
    /**
     * Get configured Retrofit instance.
     * 
     * @return Retrofit instance
     */
    public static Retrofit getRetrofitInstance() {
        if (retrofit == null) {
            // Configure HTTP logging
            HttpLoggingInterceptor loggingInterceptor = new HttpLoggingInterceptor();
            loggingInterceptor.setLevel(HttpLoggingInterceptor.Level.BODY);
            
            // Configure OkHttp client
            OkHttpClient okHttpClient = new OkHttpClient.Builder()
                .addInterceptor(loggingInterceptor)
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .build();
            
            // Configure Gson
            Gson gson = new GsonBuilder()
                .setLenient()
                .create();
            
            // Build Retrofit instance
            retrofit = new Retrofit.Builder()
                .baseUrl(BASE_URL)
                .client(okHttpClient)
                .addConverterFactory(GsonConverterFactory.create(gson))
                .build();
        }
        
        return retrofit;
    }
    
    /**
     * Get API service instance.
     * 
     * @return WalletAPIService instance
     */
    public static WalletAPIService getAPIService() {
        if (apiService == null) {
            apiService = getRetrofitInstance().create(WalletAPIService.class);
        }
        return apiService;
    }
    
    /**
     * Parse error response from API.
     * 
     * @param response Failed response
     * @return ErrorResponse object or null if parsing fails
     */
    public static ErrorResponse parseErrorResponse(Response<?> response) {
        if (response.errorBody() != null) {
            try {
                String errorBody = response.errorBody().string();
                Gson gson = new Gson();
                return gson.fromJson(errorBody, ErrorResponse.class);
            } catch (IOException e) {
                Log.e(TAG, "Failed to parse error response", e);
            }
        }
        return null;
    }
    
    /**
     * Get user-friendly error message from response.
     * 
     * @param response Failed response
     * @return User-friendly error message
     */
    public static String getErrorMessage(Response<?> response) {
        ErrorResponse errorResponse = parseErrorResponse(response);
        
        if (errorResponse != null && errorResponse.getMessage() != null) {
            return errorResponse.getMessage();
        }
        
        // Fallback error messages based on HTTP status code
        switch (response.code()) {
            case 400:
                return "Invalid request. Please check your input.";
            case 401:
                return "Authentication failed. Please try again.";
            case 404:
                return "User not found.";
            case 500:
                return "Server error. Please try again later.";
            default:
                return "An error occurred. Please try again.";
        }
    }
    
    /**
     * Result wrapper for API calls.
     * 
     * @param <T> Response data type
     */
    public static class Result<T> {
        private T data;
        private String error;
        private boolean success;
        
        private Result(T data, String error, boolean success) {
            this.data = data;
            this.error = error;
            this.success = success;
        }
        
        public static <T> Result<T> success(T data) {
            return new Result<>(data, null, true);
        }
        
        public static <T> Result<T> error(String error) {
            return new Result<>(null, error, false);
        }
        
        public T getData() {
            return data;
        }
        
        public String getError() {
            return error;
        }
        
        public boolean isSuccess() {
            return success;
        }
    }
}
