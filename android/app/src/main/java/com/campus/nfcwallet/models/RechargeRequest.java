package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Request model for recharge endpoint.
 * 
 * Corresponds to POST /recharge API request body.
 */
public class RechargeRequest {
    @SerializedName("uid")
    private String uid;
    
    @SerializedName("amount")
    private double amount;
    
    @SerializedName("timestamp")
    private long timestamp;
    
    @SerializedName("signature")
    private String signature;
    
    public RechargeRequest() {
    }
    
    public RechargeRequest(String uid, double amount, long timestamp, String signature) {
        this.uid = uid;
        this.amount = amount;
        this.timestamp = timestamp;
        this.signature = signature;
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
    
    @Override
    public String toString() {
        return "RechargeRequest{" +
                "uid='" + uid + '\'' +
                ", amount=" + amount +
                ", timestamp=" + timestamp +
                ", signature='" + signature + '\'' +
                '}';
    }
}
