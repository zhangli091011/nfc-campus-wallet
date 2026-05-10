package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * User information model.
 */
public class UserInfo {
    @SerializedName("id")
    private int id;
    
    @SerializedName("username")
    private String username;
    
    @SerializedName("role")
    private String role;
    
    @SerializedName("booth_id")
    private Integer boothId;
    
    @SerializedName("event_id")
    private Integer eventId;
    
    @SerializedName("status")
    private String status;
    
    @SerializedName("created_at")
    private String createdAt;
    
    public int getId() {
        return id;
    }
    
    public String getUsername() {
        return username;
    }
    
    public String getRole() {
        return role;
    }
    
    public Integer getBoothId() {
        return boothId;
    }
    
    public Integer getEventId() {
        return eventId;
    }
    
    public String getStatus() {
        return status;
    }
    
    public String getCreatedAt() {
        return createdAt;
    }
    
    public boolean isBoothCashier() {
        return "booth_cashier".equals(role);
    }
    
    public boolean canRecharge() {
        return "super_admin".equals(role) || 
               "event_admin".equals(role) || 
               "issuer".equals(role);
    }
}
