package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Account transfer request model - 账户互转请求模型
 */
public class AccountTransferRequest {
    @SerializedName("card_uid")
    private String cardUid;
    
    @SerializedName("event_id")
    private int eventId;
    
    @SerializedName("transfer_type")
    private String transferType;  // "to_stock" or "from_stock"
    
    @SerializedName("amount")
    private int amount;  // 单位：分
    
    @SerializedName("timestamp")
    private long timestamp;
    
    @SerializedName("signature")
    private String signature;
    
    public AccountTransferRequest(String cardUid, int eventId, String transferType, 
                                   int amount, long timestamp, String signature) {
        this.cardUid = cardUid;
        this.eventId = eventId;
        this.transferType = transferType;
        this.amount = amount;
        this.timestamp = timestamp;
        this.signature = signature;
    }
    
    // Getters
    public String getCardUid() { return cardUid; }
    public int getEventId() { return eventId; }
    public String getTransferType() { return transferType; }
    public int getAmount() { return amount; }
    public long getTimestamp() { return timestamp; }
    public String getSignature() { return signature; }
}
