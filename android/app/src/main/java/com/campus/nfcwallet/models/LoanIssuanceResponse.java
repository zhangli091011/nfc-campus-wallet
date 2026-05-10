package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Response model for bank loan issuance.
 */
public class LoanIssuanceResponse {
    @SerializedName("success")
    private boolean success;

    @SerializedName("loan_id")
    private int loanId;

    @SerializedName("principal_amount")
    private double principalAmount;

    @SerializedName("fee_amount")
    private double feeAmount;

    @SerializedName("disbursed_amount")
    private double disbursedAmount;

    @SerializedName("new_balance")
    private double newBalance;

    @SerializedName("message")
    private String message;

    public boolean isSuccess() { return success; }
    public int getLoanId() { return loanId; }
    public double getPrincipalAmount() { return principalAmount; }
    public double getFeeAmount() { return feeAmount; }
    public double getDisbursedAmount() { return disbursedAmount; }
    public double getNewBalance() { return newBalance; }
    public String getMessage() { return message; }
}
