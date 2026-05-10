package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Request model for setting staff name on first login.
 */
public class SetStaffNameRequest {
    @SerializedName("staff_name")
    private String staffName;
    
    public SetStaffNameRequest(String staffName) {
        this.staffName = staffName;
    }
    
    public String getStaffName() {
        return staffName;
    }
    
    public void setStaffName(String staffName) {
        this.staffName = staffName;
    }
}
