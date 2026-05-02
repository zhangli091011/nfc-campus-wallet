package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Booth payment request model.
 */
public class BoothPaymentRequest {
    @SerializedName("event_id")
    private int eventId;
    
    @SerializedName("card_uid")
    private String cardUid;
    
    @SerializedName("amount")
    private double amount;
    
    @SerializedName("product_id")
    private Integer productId;
    
    @SerializedName("remark")
    private String remark;
    
    public BoothPaymentRequest(int eventId, String cardUid, double amount) {
        this.eventId = eventId;
        this.cardUid = cardUid;
        this.amount = amount;
    }
    
    public BoothPaymentRequest(int eventId, String cardUid, double amount, Integer productId, String remark) {
        this.eventId = eventId;
        this.cardUid = cardUid;
        this.amount = amount;
        this.productId = productId;
        this.remark = remark;
    }
    
    public int getEventId() {
        return eventId;
    }
    
    public void setEventId(int eventId) {
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
