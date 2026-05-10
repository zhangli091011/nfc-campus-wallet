package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Stock sell response model - 抛售股票响应模型
 * 
 * 所有金额以"元"为单位。
 */
public class StockSellResponse {
    @SerializedName("success")
    private boolean success;
    
    @SerializedName("booth_id")
    private int boothId;
    
    @SerializedName("booth_name")
    private String boothName;
    
    @SerializedName("shares_sold")
    private int sharesSold;
    
    @SerializedName("sell_price")
    private double sellPrice;
    
    @SerializedName("sell_price_yuan")
    private double sellPriceYuan;
    
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
    public int getBoothId() { return boothId; }
    public String getBoothName() { return boothName; }
    public int getSharesSold() { return sharesSold; }
    public double getSellPrice() { return sellPrice; }
    public double getSellPriceYuan() { return sellPriceYuan; }
    public double getTotalAmount() { return totalAmount; }
    public double getTotalAmountYuan() { return totalAmountYuan; }
    public double getNewBalance() { return newBalance; }
    public double getNewBalanceYuan() { return newBalanceYuan; }
    public String getMessage() { return message; }
}
