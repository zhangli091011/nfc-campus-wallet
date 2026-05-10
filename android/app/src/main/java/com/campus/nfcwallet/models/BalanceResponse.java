package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Response model for balance query endpoint.
 * 
 * Corresponds to GET /balance API response.
 * Balance is returned in yuan (元) as a floating-point number.
 */
public class BalanceResponse {
    @SerializedName("balance")
    private double balance;
    
    public BalanceResponse() {
    }
    
    public BalanceResponse(double balance) {
        this.balance = balance;
    }
    
    public double getBalance() {
        return balance;
    }
    
    public void setBalance(double balance) {
        this.balance = balance;
    }
    
    @Override
    public String toString() {
        return "BalanceResponse{" +
                "balance=" + balance +
                '}';
    }
}
