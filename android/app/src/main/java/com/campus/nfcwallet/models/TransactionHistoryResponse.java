package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

import java.util.List;

/**
 * Response model for transaction history endpoint.
 * 
 * Wraps the list of transactions returned by the backend.
 */
public class TransactionHistoryResponse {
    
    @SerializedName("transactions")
    private List<Transaction> transactions;
    
    public TransactionHistoryResponse() {
    }
    
    public TransactionHistoryResponse(List<Transaction> transactions) {
        this.transactions = transactions;
    }
    
    public List<Transaction> getTransactions() {
        return transactions;
    }
    
    public void setTransactions(List<Transaction> transactions) {
        this.transactions = transactions;
    }
}
