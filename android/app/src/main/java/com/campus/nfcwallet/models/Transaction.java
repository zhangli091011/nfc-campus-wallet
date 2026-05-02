package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Model for transaction history entry.
 * 
 * Corresponds to transaction objects in GET /transactions API response.
 */
public class Transaction {
    @SerializedName("id")
    private int id;
    
    @SerializedName("type")
    private String type;  // "payment" or "recharge"
    
    @SerializedName("amount")
    private double amount;
    
    @SerializedName("balance_after")
    private double balanceAfter;
    
    @SerializedName("created_at")
    private String createdAt;
    
    @SerializedName("merchant_id")
    private String merchantId;  // Optional, only for payments
    
    public Transaction() {
    }
    
    public Transaction(int id, String type, double amount, double balanceAfter, String createdAt) {
        this.id = id;
        this.type = type;
        this.amount = amount;
        this.balanceAfter = balanceAfter;
        this.createdAt = createdAt;
    }
    
    public int getId() {
        return id;
    }
    
    public void setId(int id) {
        this.id = id;
    }
    
    public String getType() {
        return type;
    }
    
    public void setType(String type) {
        this.type = type;
    }
    
    public double getAmount() {
        return amount;
    }
    
    public void setAmount(double amount) {
        this.amount = amount;
    }
    
    public double getBalanceAfter() {
        return balanceAfter;
    }
    
    public void setBalanceAfter(double balanceAfter) {
        this.balanceAfter = balanceAfter;
    }
    
    public String getCreatedAt() {
        return createdAt;
    }
    
    public void setCreatedAt(String createdAt) {
        this.createdAt = createdAt;
    }
    
    public String getMerchantId() {
        return merchantId;
    }
    
    public void setMerchantId(String merchantId) {
        this.merchantId = merchantId;
    }
    
    @Override
    public String toString() {
        return "Transaction{" +
                "id=" + id +
                ", type='" + type + '\'' +
                ", amount=" + amount +
                ", balanceAfter=" + balanceAfter +
                ", createdAt='" + createdAt + '\'' +
                ", merchantId='" + merchantId + '\'' +
                '}';
    }
}
