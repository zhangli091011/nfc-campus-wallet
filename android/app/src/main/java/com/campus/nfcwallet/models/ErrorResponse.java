package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Error response model for API error responses.
 * 
 * All API errors return this structure.
 */
public class ErrorResponse {
    @SerializedName("error_code")
    private String errorCode;
    
    @SerializedName("message")
    private String message;
    
    @SerializedName("field")
    private String field;  // Optional, for validation errors
    
    public ErrorResponse() {
    }
    
    public ErrorResponse(String errorCode, String message) {
        this.errorCode = errorCode;
        this.message = message;
    }
    
    public String getErrorCode() {
        return errorCode;
    }
    
    public void setErrorCode(String errorCode) {
        this.errorCode = errorCode;
    }
    
    public String getMessage() {
        return message;
    }
    
    public void setMessage(String message) {
        this.message = message;
    }
    
    public String getField() {
        return field;
    }
    
    public void setField(String field) {
        this.field = field;
    }
    
    @Override
    public String toString() {
        return "ErrorResponse{" +
                "errorCode='" + errorCode + '\'' +
                ", message='" + message + '\'' +
                ", field='" + field + '\'' +
                '}';
    }
}
