package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Stock sell request model - 抛售股票请求模型
 * 
 * 以当前股价卖出持仓股票，资金返回主账户。
 */
public class StockSellRequest {
    @SerializedName("card_uid")
    private String cardUid;
    
    @SerializedName("event_id")
    private int eventId;
    
    @SerializedName("booth_id")
    private int boothId;
    
    @SerializedName("shares")
    private int shares;
    
    public StockSellRequest(String cardUid, int eventId, int boothId, int shares) {
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
