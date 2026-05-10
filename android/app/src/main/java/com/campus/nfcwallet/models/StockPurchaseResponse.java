package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Stock purchase response model - 股票购买响应模型
 */
public class StockPurchaseResponse {
    @SerializedName("success")
    private boolean success;
    
    @SerializedName("purchase_id")
    private int purchaseId;
    
    @SerializedName("stock_id")
    private int stockId;
    
    @SerializedName("booth_name")
    private String boothName;
    
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
    
    @SerializedName("new_balance")
    private int newBalance;  // 单位：分
    
    @SerializedName("new_balance_yuan")
    private double newBalanceYuan;  // 单位：元
    
    @SerializedName("transaction_id")
    private int transactionId;
    
    @SerializedName("message")
    private String message;
    
    // Getters
    public boolean isSuccess() {
        return success;
    }
    
    public int getPurchaseId() {
        return purchaseId;
    }
    
    public int getStockId() {
        return stockId;
    }
    
    public String getBoothName() {
        return boothName;
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
    
    public int getNewBalance() {
        return newBalance;
    }
    
    public double getNewBalanceYuan() {
        return newBalanceYuan;
    }
    
    public int getTransactionId() {
        return transactionId;
    }
    
    public String getMessage() {
        return message;
    }
}
