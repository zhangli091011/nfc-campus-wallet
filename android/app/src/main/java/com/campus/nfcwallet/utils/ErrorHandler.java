package com.campus.nfcwallet.utils;

import android.content.Context;

import com.campus.nfcwallet.R;
import com.campus.nfcwallet.models.ErrorResponse;
import com.google.gson.Gson;

import retrofit2.Response;

/**
 * Centralized error handling utility.
 */
public class ErrorHandler {
    
    /**
     * Parse error from API response.
     */
    public static String parseError(Response<?> response) {
        return getErrorMessage(response);
    }
    
    /**
     * Get error message from API response.
     */
    public static String getErrorMessage(Response<?> response) {
        if (response.isSuccessful()) {
            return "操作成功";
        }
        
        try {
            if (response.errorBody() != null) {
                String errorJson = response.errorBody().string();
                Gson gson = new Gson();
                ErrorResponse errorResponse = gson.fromJson(errorJson, ErrorResponse.class);
                
                if (errorResponse != null && errorResponse.getMessage() != null) {
                    return errorResponse.getMessage();
                }
            }
        } catch (Exception e) {
            // Ignore parsing errors
        }
        
        // Fallback to HTTP status
        switch (response.code()) {
            case 400:
                return "请求参数错误";
            case 401:
                return "未登录或登录已过期";
            case 403:
                return "权限不足";
            case 404:
                return "资源不存在";
            case 500:
                return "服务器错误";
            default:
                return "操作失败 (HTTP " + response.code() + ")";
        }
    }
    
    /**
     * Get detailed error message from API response (for debugging).
     */
    public static String getDetailedErrorMessage(Response<?> response) {
        StringBuilder sb = new StringBuilder();
        
        // Add HTTP status
        sb.append("HTTP ").append(response.code()).append(": ");
        sb.append(response.message()).append("\n");
        
        // Add URL
        sb.append("URL: ").append(response.raw().request().url()).append("\n");
        
        // Try to parse error body
        try {
            if (response.errorBody() != null) {
                String errorJson = response.errorBody().string();
                sb.append("Response: ").append(errorJson).append("\n");
                
                Gson gson = new Gson();
                ErrorResponse errorResponse = gson.fromJson(errorJson, ErrorResponse.class);
                
                if (errorResponse != null) {
                    if (errorResponse.getErrorCode() != null) {
                        sb.append("Error Code: ").append(errorResponse.getErrorCode()).append("\n");
                    }
                    if (errorResponse.getMessage() != null) {
                        sb.append("Message: ").append(errorResponse.getMessage());
                    }
                }
            }
        } catch (Exception e) {
            sb.append("Error parsing response: ").append(e.getMessage());
        }
        
        return sb.toString();
    }
    
    /**
     * Get user-friendly error message based on error code.
     */
    public static String getErrorMessage(Context context, String errorCode) {
        if (errorCode == null) {
            return context.getString(R.string.error_unknown);
        }
        
        switch (errorCode) {
            // Authentication errors
            case "AUTH_ERROR":
            case "INVALID_CREDENTIALS":
                return context.getString(R.string.error_invalid_credentials);
            case "TOKEN_EXPIRED":
                return context.getString(R.string.error_token_expired);
            case "TOKEN_INVALID":
            case "TOKEN_MISSING":
                return context.getString(R.string.error_token_invalid);
            case "AUTHENTICATION_REQUIRED":
                return context.getString(R.string.error_auth_required);
            
            // Authorization errors
            case "PERMISSION_DENIED":
                return context.getString(R.string.error_permission_denied);
            case "BOOTH_ACCESS_DENIED":
                return context.getString(R.string.error_booth_access_denied);
            case "ROLE_NOT_ALLOWED":
                return context.getString(R.string.error_role_not_allowed);
            
            // Validation errors
            case "INSUFFICIENT_FUNDS":
                return context.getString(R.string.error_insufficient_funds);
            case "EVENT_INACTIVE":
                return context.getString(R.string.error_event_inactive);
            case "BOOTH_INACTIVE":
                return context.getString(R.string.error_booth_inactive);
            case "PRODUCT_DISABLED":
                return context.getString(R.string.error_product_disabled);
            case "INSUFFICIENT_STOCK":
                return context.getString(R.string.error_insufficient_stock);
            case "USER_BLOCKED":
                return context.getString(R.string.error_user_blocked);
            case "PARTICIPANT_BLOCKED":
                return context.getString(R.string.error_participant_blocked);
            
            // Not found errors
            case "BOOTH_NOT_FOUND":
                return context.getString(R.string.error_booth_not_found);
            case "PRODUCT_NOT_FOUND":
                return context.getString(R.string.error_product_not_found);
            case "PARTICIPANT_NOT_FOUND":
                return context.getString(R.string.error_participant_not_found);
            case "EVENT_NOT_FOUND":
                return context.getString(R.string.error_event_not_found);
            
            // Signature errors
            case "SIGNATURE_VERIFICATION_FAILED":
                return context.getString(R.string.error_signature_failed);
            case "TIMESTAMP_EXPIRED":
                return context.getString(R.string.error_timestamp_expired);
            
            // Network errors
            case "NETWORK_ERROR":
                return context.getString(R.string.error_network);
            
            // Default
            default:
                return context.getString(R.string.error_unknown) + " (" + errorCode + ")";
        }
    }
    
    /**
     * Check if error is authentication related.
     */
    public static boolean isAuthError(String errorCode) {
        return errorCode != null && (
            errorCode.equals("AUTH_ERROR") ||
            errorCode.equals("TOKEN_EXPIRED") ||
            errorCode.equals("TOKEN_INVALID") ||
            errorCode.equals("TOKEN_MISSING") ||
            errorCode.equals("AUTHENTICATION_REQUIRED")
        );
    }
}
