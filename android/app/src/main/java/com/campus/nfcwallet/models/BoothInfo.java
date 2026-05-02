package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Booth information model.
 */
public class BoothInfo {
    @SerializedName("id")
    private int id;
    
    @SerializedName("event_id")
    private int eventId;
    
    @SerializedName("name")
    private String name;
    
    @SerializedName("class_name")
    private String className;
    
    @SerializedName("status")
    private String status;
    
    @SerializedName("created_at")
    private String createdAt;
    
    public int getId() {
        return id;
    }
    
    public int getEventId() {
        return eventId;
    }
    
    public String getName() {
        return name;
    }
    
    public String getClassName() {
        return className;
    }
    
    public String getStatus() {
        return status;
    }
    
    public String getCreatedAt() {
        return createdAt;
    }
    
    public boolean isActive() {
        return "active".equals(status);
    }
}
