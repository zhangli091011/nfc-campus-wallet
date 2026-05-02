package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Booth payment request model.
 * 
 * event_id is now optional - if not provided, the backend will use the currently active event.
 */
public class BoothPaymentRequest {
    @SerializedName("event_id")
    private Integer eventId;  // Changed to Integer to allow null
    
    @SerializedName("card_uid")
    private String cardUid;
    
    @SerializedName("amount")
    private double amount;
    
    @SerializedName("product_id")
    private Integer productId;
    
    @SerializedName("remark")
    private String remark;
    
    /**
     * Constructor without event_id - backend will use active event.
     */
    public BoothPaymentRequest(String cardUid, double amount) {
        this.eventId = null;  // Will use active event
        this.cardUid = cardUid;
        this.amount = amount;
    }
    
    /**
     * Constructor with event_id.
     */
    public BoothPaymentRequest(int eventId, String cardUid, double amount) {
        this.eventId = eventId;
        this.cardUid = cardUid;
        this.amount = amount;
    }
    
    /**
     * Full constructor without event_id.
     */
    public BoothPaymentRequest(String cardUid, double amount, Integer productId, String remark) {
        this.eventId = null;  // Will use active event
        this.cardUid = cardUid;
        this.amount = amount;
        this.productId = productId;
        this.remark = remark;
    }
    
    /**
     * Full constructor with event_id.
     */
    public BoothPaymentRequest(int eventId, String cardUid, double amount, Integer productId, String remark) {
        this.eventId = eventId;
        this.cardUid = cardUid;
        this.amount = amount;
        this.productId = productId;
        this.remark = remark;
    }
    
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
    
    public double getAmount() {
        return amount;
    }
    
    public void setAmount(double amount) {
        this.amount = amount;
    }
    
    public Integer getProductId() {
        return productId;
    }
    
    public void setProductId(Integer productId) {
        this.productId = productId;
    }
    
    public String getRemark() {
        return remark;
    }
    
    public void setRemark(String remark) {
        this.remark = remark;
    }
}
