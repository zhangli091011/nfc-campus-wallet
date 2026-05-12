package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

import java.util.List;

/**
 * Response model for GET /booths/{booth_id}/transactions.
 * 
 * Backend returns: {"transactions": [...], "total_count": N}
 */
public class BoothTransactionsResponse {
    @SerializedName("transactions")
    private List<Transaction> transactions;
    
    @SerializedName("total_count")
    private int totalCount;
    
    public List<Transaction> getTransactions() {
        return transactions;
    }
    
    public void setTransactions(List<Transaction> transactions) {
        this.transactions = transactions;
    }
    
    public int getTotalCount() {
        return totalCount;
    }
    
    public void setTotalCount(int totalCount) {
        this.totalCount = totalCount;
    }
}
