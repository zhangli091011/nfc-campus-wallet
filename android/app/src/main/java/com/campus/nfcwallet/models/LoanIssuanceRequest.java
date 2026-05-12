package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Request model for bank loan issuance.
 * 
 * POST /api/bank/issue_loan
 */
public class LoanIssuanceRequest {
    @SerializedName("card_uid")
    private String cardUid;

    @SerializedName("principal_amount")
    private int principalAmount;

    @SerializedName("event_id")
    private int eventId;

    @SerializedName("deposit_card_fee")
    private Double depositCardFee;

    @SerializedName("timestamp")
    private long timestamp;

    @SerializedName("signature")
    private String signature;

    public LoanIssuanceRequest(String cardUid, int principalAmount, int eventId, long timestamp, String signature) {
        this.cardUid = cardUid;
        this.principalAmount = principalAmount;
        this.eventId = eventId;
        this.timestamp = timestamp;
        this.signature = signature;
        this.depositCardFee = null;
    }

    public LoanIssuanceRequest(String cardUid, int principalAmount, int eventId, Double depositCardFee, long timestamp, String signature) {
        this.cardUid = cardUid;
        this.principalAmount = principalAmount;
        this.eventId = eventId;
        this.depositCardFee = depositCardFee;
        this.timestamp = timestamp;
        this.signature = signature;
    }

    public String getCardUid() { return cardUid; }
    public int getPrincipalAmount() { return principalAmount; }
    public int getEventId() { return eventId; }
    public Double getDepositCardFee() { return depositCardFee; }
    public void setDepositCardFee(Double depositCardFee) { this.depositCardFee = depositCardFee; }
    public long getTimestamp() { return timestamp; }
    public String getSignature() { return signature; }
}
