package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Stock buy response model - 购买股票响应模型
 * 
 * 所有金额以"元"为单位。
 */
public class StockBuyResponse {
    @SerializedName("success")
    private boolean success;
    
    @SerializedName("order_id")
    private int orderId;
    
    @SerializedName("booth_id")
    private int boothId;
    
    @SerializedName("booth_name")
    private String boothName;
    
    @SerializedName("shares")
    private int shares;
    
    @SerializedName("buy_price")
    private double buyPrice;
    
    @SerializedName("buy_price_yuan")
    private double buyPriceYuan;
    
    @SerializedName("total_amount")
    private double totalAmount;
    
    @SerializedName("total_amount_yuan")
    private double totalAmountYuan;
    
    @SerializedName("new_balance")
    private double newBalance;
    
    @SerializedName("new_balance_yuan")
    private double newBalanceYuan;
    
    @SerializedName("message")
    private String message;
    
    // Getters
    public boolean isSuccess() { return success; }
    public int getOrderId() { return orderId; }
    public int getBoothId() { return boothId; }
    public String getBoothName() { return boothName; }
    public int getShares() { return shares; }
    public double getBuyPrice() { return buyPrice; }
    public double getBuyPriceYuan() { return buyPriceYuan; }
    public double getTotalAmount() { return totalAmount; }
    public double getTotalAmountYuan() { return totalAmountYuan; }
    public double getNewBalance() { return newBalance; }
    public double getNewBalanceYuan() { return newBalanceYuan; }
    public String getMessage() { return message; }
}
