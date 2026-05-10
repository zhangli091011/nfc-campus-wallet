package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Stock purchase request model - 股票购买请求模型
 */
public class StockPurchaseRequest {
    @SerializedName("card_uid")
    private String cardUid;
    
    @SerializedName("stock_id")
    private int stockId;
    
    @SerializedName("quantity")
    private int quantity;
    
    @SerializedName("timestamp")
    private long timestamp;
    
    @SerializedName("signature")
    private String signature;
    
    public StockPurchaseRequest(String cardUid, int stockId, int quantity, long timestamp, String signature) {
        this.cardUid = cardUid;
        this.stockId = stockId;
        this.quantity = quantity;
        this.timestamp = timestamp;
        this.signature = signature;
    }
    
    // Getters
    public String getCardUid() {
        return cardUid;
    }
    
    public int getStockId() {
        return stockId;
    }
    
    public int getQuantity() {
        return quantity;
    }
    
    public long getTimestamp() {
        return timestamp;
    }
    
    public String getSignature() {
        return signature;
    }
}
