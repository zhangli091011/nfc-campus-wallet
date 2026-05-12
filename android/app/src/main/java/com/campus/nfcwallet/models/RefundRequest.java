package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Request model for refund operations.
 *
 * POST /api/trade/refund
 */
public class RefundRequest {
    @SerializedName("original_transaction_id")
    private int originalTransactionId;

    @SerializedName("reason")
    private String reason;

    public RefundRequest() {
    }

    public RefundRequest(int originalTransactionId, String reason) {
        this.originalTransactionId = originalTransactionId;
        this.reason = reason;
    }

    public int getOriginalTransactionId() {
        return originalTransactionId;
    }

    public void setOriginalTransactionId(int originalTransactionId) {
        this.originalTransactionId = originalTransactionId;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }
}
