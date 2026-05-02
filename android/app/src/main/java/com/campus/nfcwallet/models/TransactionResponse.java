package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Response model for payment and recharge endpoints.
 * 
 * Corresponds to POST /pay and POST /recharge API responses.
 */
public class TransactionResponse {
    @SerializedName("success")
    private boolean success;
    
    @SerializedName("new_balance")
    private double newBalance;
    
    @SerializedName("transaction_id")
    private int transactionId;
    
    public TransactionResponse() {
    }
    
    public TransactionResponse(boolean success, double newBalance, int transactionId) {
        this.success = success;
        this.newBalance = newBalance;
        this.transactionId = transactionId;
    }
    
    public boolean isSuccess() {
        return success;
    }
    
    public void setSuccess(boolean success) {
        this.success = success;
    }
    
    public double getNewBalance() {
        return newBalance;
    }
    
    public void setNewBalance(double newBalance) {
        this.newBalance = newBalance;
    }
    
    public int getTransactionId() {
        return transactionId;
    }
    
    public void setTransactionId(int transactionId) {
        this.transactionId = transactionId;
    }
    
    @Override
    public String toString() {
        return "TransactionResponse{" +
                "success=" + success +
                ", newBalance=" + newBalance +
                ", transactionId=" + transactionId +
                '}';
    }
}
