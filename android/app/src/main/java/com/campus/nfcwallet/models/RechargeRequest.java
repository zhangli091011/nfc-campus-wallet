package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Request model for recharge endpoint.
 * 
 * Supports two modes:
 * 1. Event mode: event_id + card_uid (no signature required)
 * 2. Legacy mode: uid + timestamp + signature
 * 
 * Corresponds to POST /recharge API request body.
 */
public class RechargeRequest {
    // Event mode fields
    @SerializedName("event_id")
    private Integer eventId;
    
    @SerializedName("card_uid")
    private String cardUid;
    
    // Legacy mode fields
    @SerializedName("uid")
    private String uid;
    
    @SerializedName("timestamp")
    private Long timestamp;
    
    @SerializedName("signature")
    private String signature;
    
    // Common fields
    @SerializedName("amount")
    private double amount;
    
    @SerializedName("operator_id")
    private String operatorId;
    
    @SerializedName("remark")
    private String remark;
    
    public RechargeRequest() {
    }
    
    /**
     * Constructor for legacy mode (with signature).
     */
    public RechargeRequest(String uid, double amount, long timestamp, String signature) {
        this.uid = uid;
        this.amount = amount;
        this.timestamp = timestamp;
        this.signature = signature;
    }
    
    /**
     * Constructor for event mode (no signature required).
     */
    public RechargeRequest(int eventId, String cardUid, double amount, String remark) {
        this.eventId = eventId;
        this.cardUid = cardUid;
        this.amount = amount;
        this.remark = remark;
    }
    
    // Getters and setters
    
    public Integer getEventId() {
        return eventId;
    }
    
    public void setEventId(Integer eventId) {
        this.eventId = eventId;
    }
    
    public String getCardUid() {
        return cardUid;
    }
    
    public void setCardUid(String cardUid) {
        this.cardUid = cardUid;
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
    
    public Long getTimestamp() {
        return timestamp;
    }
    
    public void setTimestamp(Long timestamp) {
        this.timestamp = timestamp;
    }
    
    public String getSignature() {
        return signature;
    }
    
    public void setSignature(String signature) {
        this.signature = signature;
    }
    
    public String getOperatorId() {
        return operatorId;
    }
    
    public void setOperatorId(String operatorId) {
        this.operatorId = operatorId;
    }
    
    public String getRemark() {
        return remark;
    }
    
    public void setRemark(String remark) {
        this.remark = remark;
    }
    
    @Override
    public String toString() {
        if (eventId != null && cardUid != null) {
            return "RechargeRequest{" +
                    "eventId=" + eventId +
                    ", cardUid='" + cardUid + '\'' +
                    ", amount=" + amount +
                    ", remark='" + remark + '\'' +
                    '}';
        } else {
            return "RechargeRequest{" +
                    "uid='" + uid + '\'' +
                    ", amount=" + amount +
                    ", timestamp=" + timestamp +
                    ", signature='" + signature + '\'' +
                    '}';
        }
    }
}
