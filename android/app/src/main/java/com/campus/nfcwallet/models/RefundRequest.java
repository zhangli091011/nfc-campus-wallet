package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Request model for refund operations.
 *
 * POST /booths/{booth_id}/refund
 */
public class RefundRequest {
    @SerializedName("transaction_id")
    private int transactionId;

    @SerializedName("booth_id")
    private int boothId;

    @SerializedName("card_uid")
    private String cardUid;

    @SerializedName("amount")
    private double amount;

    @SerializedName("admin_code")
    private String adminCode;

    @SerializedName("reason")
    private String reason;

    public RefundRequest() {
    }

    public RefundRequest(int transactionId, int boothId, String cardUid, double amount, String adminCode, String reason) {
        this.transactionId = transactionId;
        this.boothId = boothId;
        this.cardUid = cardUid;
        this.amount = amount;
        this.adminCode = adminCode;
        this.reason = reason;
    }

    public int getTransactionId() {
        return transactionId;
    }

    public void setTransactionId(int transactionId) {
        this.transactionId = transactionId;
    }

    public int getBoothId() {
        return boothId;
    }

    public void setBoothId(int boothId) {
        this.boothId = boothId;
    }

    public String getCardUid() {
        return cardUid;
    }

    public void setCardUid(String cardUid) {
        this.cardUid = cardUid;
    }

    public double getAmount() {
        return amount;
    }

    public void setAmount(double amount) {
        this.amount = amount;
    }

    public String getAdminCode() {
        return adminCode;
    }

    public void setAdminCode(String adminCode) {
        this.adminCode = adminCode;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }
}
