package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Stock holding info model - 持仓信息模型（按摊位聚合）
 */
public class StockHoldingInfo {
    @SerializedName("booth_id")
    private int boothId;
    
    @SerializedName("booth_name")
    private String boothName;
    
    @SerializedName("class_name")
    private String className;
    
    @SerializedName("shares")
    private int shares;
    
    @SerializedName("total_cost")
    private double totalCost;
    
    @SerializedName("current_price")
    private double currentPrice;
    
    @SerializedName("market_value")
    private double marketValue;
    
    // Getters
    public int getBoothId() { return boothId; }
    public String getBoothName() { return boothName; }
    public String getClassName() { return className; }
    public int getShares() { return shares; }
    public double getTotalCost() { return totalCost; }
    public double getCurrentPrice() { return currentPrice; }
    public double getMarketValue() { return marketValue; }
}
