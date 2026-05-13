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
    
    @SerializedName("discount_applied")
    private boolean discountApplied;
    
    @SerializedName("discount_amount")
    private Double discountAmount;
    
    @SerializedName("original_amount")
    private Double originalAmount;
    
    @SerializedName("actual_amount")
    private Double actualAmount;
    
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
    
    public boolean isDiscountApplied() {
        return discountApplied;
    }
    
    public void setDiscountApplied(boolean discountApplied) {
        this.discountApplied = discountApplied;
    }
    
    public Double getDiscountAmount() {
        return discountAmount;
    }
    
    public void setDiscountAmount(Double discountAmount) {
        this.discountAmount = discountAmount;
    }
    
    public Double getOriginalAmount() {
        return originalAmount;
    }
    
    public void setOriginalAmount(Double originalAmount) {
        this.originalAmount = originalAmount;
    }
    
    public Double getActualAmount() {
        return actualAmount;
    }
    
    public void setActualAmount(Double actualAmount) {
        this.actualAmount = actualAmount;
    }
    
    @Override
    public String toString() {
        return "TransactionResponse{" +
                "success=" + success +
                ", newBalance=" + newBalance +
                ", transactionId=" + transactionId +
                ", discountApplied=" + discountApplied +
                ", discountAmount=" + discountAmount +
                ", originalAmount=" + originalAmount +
                ", actualAmount=" + actualAmount +
                '}';
    }
}
