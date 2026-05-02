package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Event information model.
 */
public class EventInfo {
    @SerializedName("id")
    private int id;
    
    @SerializedName("name")
    private String name;
    
    @SerializedName("start_time")
    private String startTime;
    
    @SerializedName("end_time")
    private String endTime;
    
    @SerializedName("status")
    private String status;
    
    @SerializedName("recharge_enabled")
    private boolean rechargeEnabled;
    
    @SerializedName("consume_enabled")
    private boolean consumeEnabled;
    
    public int getId() {
        return id;
    }
    
    public String getName() {
        return name;
    }
    
    public String getStartTime() {
        return startTime;
    }
    
    public String getEndTime() {
        return endTime;
    }
    
    public String getStatus() {
        return status;
    }
    
    public boolean isRechargeEnabled() {
        return rechargeEnabled;
    }
    
    public boolean isConsumeEnabled() {
        return consumeEnabled;
    }
    
    public boolean isActive() {
        return "active".equals(status);
    }
}
