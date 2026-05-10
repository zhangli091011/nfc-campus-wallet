package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Stock holding model - 股票持仓模型
 */
public class StockHolding {
    @SerializedName("id")
    private int id;
    
    @SerializedName("stock_id")
    private int stockId;
    
    @SerializedName("booth_name")
    private String boothName;
    
    @SerializedName("class_name")
    private String className;
    
    @SerializedName("quantity")
    private int quantity;
    
    @SerializedName("purchase_price")
    private int purchasePrice;  // 单位：分
    
    @SerializedName("purchase_price_yuan")
    private double purchasePriceYuan;  // 单位：元
    
    @SerializedName("total_amount")
    private int totalAmount;  // 单位：分
    
    @SerializedName("total_amount_yuan")
    private double totalAmountYuan;  // 单位：元
    
    @SerializedName("status")
    private String status;
    
    @SerializedName("settlement_price")
    private Integer settlementPrice;  // 单位：分，可为null
    
    @SerializedName("settlement_price_yuan")
    private Double settlementPriceYuan;  // 单位：元，可为null
    
    @SerializedName("settlement_amount")
    private Integer settlementAmount;  // 单位：分，可为null
    
    @SerializedName("settlement_amount_yuan")
    private Double settlementAmountYuan;  // 单位：元，可为null
    
    @SerializedName("profit_loss")
    private Integer profitLoss;  // 单位：分，可为null
    
    @SerializedName("profit_loss_yuan")
    private Double profitLossYuan;  // 单位：元，可为null
    
    @SerializedName("created_at")
    private String createdAt;
    
    @SerializedName("settled_at")
    private String settledAt;
    
    // Getters
    public int getId() {
        return id;
    }
    
    public int getStockId() {
        return stockId;
    }
    
    public String getBoothName() {
        return boothName;
    }
    
    public String getClassName() {
        return className;
    }
    
    public int getQuantity() {
        return quantity;
    }
    
    public int getPurchasePrice() {
        return purchasePrice;
    }
    
    public double getPurchasePriceYuan() {
        return purchasePriceYuan;
    }
    
    public int getTotalAmount() {
        return totalAmount;
    }
    
    public double getTotalAmountYuan() {
        return totalAmountYuan;
    }
    
    public String getStatus() {
        return status;
    }
    
    public Integer getSettlementPrice() {
        return settlementPrice;
    }
    
    public Double getSettlementPriceYuan() {
        return settlementPriceYuan;
    }
    
    public Integer getSettlementAmount() {
        return settlementAmount;
    }
    
    public Double getSettlementAmountYuan() {
        return settlementAmountYuan;
    }
    
    public Integer getProfitLoss() {
        return profitLoss;
    }
    
    public Double getProfitLossYuan() {
        return profitLossYuan;
    }
    
    public String getCreatedAt() {
        return createdAt;
    }
    
    public String getSettledAt() {
        return settledAt;
    }
    
    public boolean isSettled() {
        return "settled".equals(status);
    }
    
    public boolean isProfitable() {
        return profitLoss != null && profitLoss > 0;
    }
}
