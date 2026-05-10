package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Account transfer response model - 账户互转响应模型
 */
public class AccountTransferResponse {
    @SerializedName("success")
    private boolean success;
    
    @SerializedName("transfer_id")
    private int transferId;
    
    @SerializedName("transfer_type")
    private String transferType;
    
    @SerializedName("amount")
    private int amount;
    
    @SerializedName("amount_yuan")
    private double amountYuan;
    
    @SerializedName("account_balance")
    private int accountBalance;
    
    @SerializedName("account_balance_yuan")
    private double accountBalanceYuan;
    
    @SerializedName("stock_balance")
    private int stockBalance;
    
    @SerializedName("stock_balance_yuan")
    private double stockBalanceYuan;
    
    @SerializedName("message")
    private String message;
    
    // Getters
    public boolean isSuccess() { return success; }
    public int getTransferId() { return transferId; }
    public String getTransferType() { return transferType; }
    public int getAmount() { return amount; }
    public double getAmountYuan() { return amountYuan; }
    public int getAccountBalance() { return accountBalance; }
    public double getAccountBalanceYuan() { return accountBalanceYuan; }
    public int getStockBalance() { return stockBalance; }
    public double getStockBalanceYuan() { return stockBalanceYuan; }
    public String getMessage() { return message; }
}
