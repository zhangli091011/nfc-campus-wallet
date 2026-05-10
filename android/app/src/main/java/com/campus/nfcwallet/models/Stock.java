package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Stock model - 股票模型
 */
public class Stock {
    @SerializedName("id")
    private int id;
    
    @SerializedName("booth_id")
    private int boothId;
    
    @SerializedName("event_id")
    private int eventId;
    
    @SerializedName("booth_name")
    private String boothName;
    
    @SerializedName("class_name")
    private String className;
    
    @SerializedName("initial_price")
    private int initialPrice;  // 单位：分
    
    @SerializedName("initial_price_yuan")
    private double initialPriceYuan;  // 单位：元
    
    @SerializedName("total_shares")
    private int totalShares;
    
    @SerializedName("sold_shares")
    private int soldShares;
    
    @SerializedName("available_shares")
    private int availableShares;
    
    @SerializedName("status")
    private String status;
    
    @SerializedName("created_at")
    private String createdAt;
    
    @SerializedName("updated_at")
    private String updatedAt;
    
    // Getters
    public int getId() {
        return id;
    }
    
    public int getBoothId() {
        return boothId;
    }
    
    public int getEventId() {
        return eventId;
    }
    
    public String getBoothName() {
        return boothName;
    }
    
    public String getClassName() {
        return className;
    }
    
    public int getInitialPrice() {
        return initialPrice;
    }
    
    public double getInitialPriceYuan() {
        return initialPriceYuan;
    }
    
    public int getTotalShares() {
        return totalShares;
    }
    
    public int getSoldShares() {
        return soldShares;
    }
    
    public int getAvailableShares() {
        return availableShares;
    }
    
    public String getStatus() {
        return status;
    }
    
    public String getCreatedAt() {
        return createdAt;
    }
    
    public String getUpdatedAt() {
        return updatedAt;
    }
    
    public boolean isAvailable() {
        return "active".equals(status) && availableShares > 0;
    }
}
