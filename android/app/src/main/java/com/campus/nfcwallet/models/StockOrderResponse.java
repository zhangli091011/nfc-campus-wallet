package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Stock order response model - 股票订单响应模型
 */
public class StockOrderResponse {
    @SerializedName("id")
    private int id;
    
    @SerializedName("event_id")
    private int eventId;
    
    @SerializedName("participant_id")
    private int participantId;
    
    @SerializedName("booth_id")
    private int boothId;
    
    @SerializedName("booth_name")
    private String boothName;
    
    @SerializedName("class_name")
    private String className;
    
    @SerializedName("shares")
    private int shares;
    
    @SerializedName("buy_price")
    private int buyPrice;
    
    @SerializedName("buy_price_yuan")
    private double buyPriceYuan;
    
    @SerializedName("total_amount")
    private int totalAmount;
    
    @SerializedName("total_amount_yuan")
    private double totalAmountYuan;
    
    @SerializedName("status")
    private String status;
    
    @SerializedName("settlement_price")
    private Integer settlementPrice;
    
    @SerializedName("settlement_price_yuan")
    private Double settlementPriceYuan;
    
    @SerializedName("settlement_amount")
    private Integer settlementAmount;
    
    @SerializedName("settlement_amount_yuan")
    private Double settlementAmountYuan;
    
    @SerializedName("profit_loss")
    private Integer profitLoss;
    
    @SerializedName("profit_loss_yuan")
    private Double profitLossYuan;
    
    @SerializedName("created_at")
    private String createdAt;
    
    @SerializedName("settled_at")
    private String settledAt;
    
    // Getters
    public int getId() { return id; }
    public int getEventId() { return eventId; }
    public int getParticipantId() { return participantId; }
    public int getBoothId() { return boothId; }
    public String getBoothName() { return boothName; }
    public String getClassName() { return className; }
    public int getShares() { return shares; }
    public int getBuyPrice() { return buyPrice; }
    public double getBuyPriceYuan() { return buyPriceYuan; }
    public int getTotalAmount() { return totalAmount; }
    public double getTotalAmountYuan() { return totalAmountYuan; }
    public String getStatus() { return status; }
    public Integer getSettlementPrice() { return settlementPrice; }
    public Double getSettlementPriceYuan() { return settlementPriceYuan; }
    public Integer getSettlementAmount() { return settlementAmount; }
    public Double getSettlementAmountYuan() { return settlementAmountYuan; }
    public Integer getProfitLoss() { return profitLoss; }
    public Double getProfitLossYuan() { return profitLossYuan; }
    public String getCreatedAt() { return createdAt; }
    public String getSettledAt() { return settledAt; }
    
    public boolean isSettled() {
        return "settled".equals(status);
    }
    
    public boolean isProfitable() {
        return profitLoss != null && profitLoss > 0;
    }
}
