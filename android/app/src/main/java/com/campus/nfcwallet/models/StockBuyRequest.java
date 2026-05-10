package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Stock buy request model - 购买股票请求模型
 * 
 * 直接从主账户扣款，不再需要 timestamp/signature（走JWT认证）。
 */
public class StockBuyRequest {
    @SerializedName("card_uid")
    private String cardUid;
    
    @SerializedName("event_id")
    private int eventId;
    
    @SerializedName("booth_id")
    private int boothId;
    
    @SerializedName("shares")
    private int shares;
    
    public StockBuyRequest(String cardUid, int eventId, int boothId, int shares) {
        this.cardUid = cardUid;
        this.eventId = eventId;
        this.boothId = boothId;
        this.shares = shares;
    }
    
    // Getters
    public String getCardUid() { return cardUid; }
    public int getEventId() { return eventId; }
    public int getBoothId() { return boothId; }
    public int getShares() { return shares; }
}
