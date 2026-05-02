package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Participant information model.
 */
public class ParticipantInfo {
    @SerializedName("id")
    private int id;
    
    @SerializedName("name")
    private String name;
    
    @SerializedName("card_uid")
    private String cardUid;
    
    @SerializedName("class_name")
    private String className;
    
    @SerializedName("student_no")
    private String studentNo;
    
    @SerializedName("status")
    private String status;
    
    @SerializedName("created_at")
    private String createdAt;
    
    public int getId() {
        return id;
    }
    
    public String getName() {
        return name;
    }
    
    public String getCardUid() {
        return cardUid;
    }
    
    public String getClassName() {
        return className;
    }
    
    public String getStudentNo() {
        return studentNo;
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
    
    public boolean isBlocked() {
        return "blocked".equals(status);
    }
}
