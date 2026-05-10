package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Response model for set staff name API.
 */
public class SetStaffNameResponse {
    @SerializedName("message")
    private String message;
    
    @SerializedName("staff_name")
    private String staffName;
    
    public String getMessage() {
        return message;
    }
    
    public String getStaffName() {
        return staffName;
    }
}
