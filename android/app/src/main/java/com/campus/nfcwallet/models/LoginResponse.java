package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Login response model.
 */
public class LoginResponse {
    @SerializedName("access_token")
    private String accessToken;
    
    @SerializedName("token_type")
    private String tokenType;
    
    @SerializedName("user")
    private UserInfo user;
    
    public String getAccessToken() {
        return accessToken;
    }
    
    public String getTokenType() {
        return tokenType;
    }
    
    public UserInfo getUser() {
        return user;
    }
}
