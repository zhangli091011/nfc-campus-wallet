package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Request model for payment endpoint.
 * 
 * Corresponds to POST /pay API request body.
 */
public class PaymentRequest {
    @SerializedName("uid")
    private String uid;
    
    @SerializedName("amount")
    private double amount;
    
    @SerializedName("timestamp")
    private long timestamp;
    
    @SerializedName("signature")
    private String signature;
    
    @SerializedName("merchant_id")
    private String merchantId;  // Optional
    
    public PaymentRequest() {
    }
    
    public PaymentRequest(String uid, double amount, long timestamp, String signature) {
        this.uid = uid;
        this.amount = amount;
        this.timestamp = timestamp;
        this.signature = signature;
    }
    
    public PaymentRequest(String uid, double amount, long timestamp, String signature, String merchantId) {
        this.uid = uid;
        this.amount = amount;
        this.timestamp = timestamp;
        this.signature = signature;
        this.merchantId = merchantId;
    }
    
    public String getUid() {
        return uid;
    }
    
    public void setUid(String uid) {
        this.uid = uid;
    }
    
    public double getAmount() {
        return amount;
    }
    
    public void setAmount(double amount) {
        this.amount = amount;
    }
    
    public long getTimestamp() {
        return timestamp;
    }
    
    public void setTimestamp(long timestamp) {
        this.timestamp = timestamp;
    }
    
    public String getSignature() {
        return signature;
    }
    
    public void setSignature(String signature) {
        this.signature = signature;
    }
    
    public String getMerchantId() {
        return merchantId;
    }
    
    public void setMerchantId(String merchantId) {
        this.merchantId = merchantId;
    }
    
    @Override
    public String toString() {
        return "PaymentRequest{" +
                "uid='" + uid + '\'' +
                ", amount=" + amount +
                ", timestamp=" + timestamp +
                ", signature='" + signature + '\'' +
                ", merchantId='" + merchantId + '\'' +
                '}';
    }
}
