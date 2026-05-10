package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Response model for refund operations.
 */
public class RefundResponse {
    @SerializedName("success")
    private boolean success;

    @SerializedName("refund_id")
    private int refundId;

    @SerializedName("new_balance")
    private double newBalance;

    @SerializedName("refunded_amount")
    private double refundedAmount;

    @SerializedName("message")
    private String message;

    public RefundResponse() {
    }

    public boolean isSuccess() {
        return success;
    }

    public void setSuccess(boolean success) {
        this.success = success;
    }

    public int getRefundId() {
        return refundId;
    }

    public void setRefundId(int refundId) {
        this.refundId = refundId;
    }

    public double getNewBalance() {
        return newBalance;
    }

    public void setNewBalance(double newBalance) {
        this.newBalance = newBalance;
    }

    public double getRefundedAmount() {
        return refundedAmount;
    }

    public void setRefundedAmount(double refundedAmount) {
        this.refundedAmount = refundedAmount;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }
}
