package com.campus.nfcwallet.utils;

import android.content.Context;
import android.content.SharedPreferences;

import com.campus.nfcwallet.models.UserInfo;
import com.google.gson.Gson;

/**
 * Session manager for handling user authentication state.
 */
public class SessionManager {
    private static final String PREF_NAME = "NFCWalletSession";
    private static final String KEY_TOKEN = "access_token";
    private static final String KEY_USER_INFO = "user_info";
    private static final String KEY_IS_LOGGED_IN = "is_logged_in";
    
    private SharedPreferences prefs;
    private SharedPreferences.Editor editor;
    private Gson gson;
    
    public SessionManager(Context context) {
        prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        editor = prefs.edit();
        gson = new Gson();
    }
    
    /**
     * Save login session.
     */
    public void saveSession(String token, UserInfo userInfo) {
        editor.putString(KEY_TOKEN, token);
        editor.putString(KEY_USER_INFO, gson.toJson(userInfo));
        editor.putBoolean(KEY_IS_LOGGED_IN, true);
        editor.apply();
    }
    
    /**
     * Get access token.
     */
    public String getToken() {
        return prefs.getString(KEY_TOKEN, null);
    }
    
    /**
     * Get user info.
     */
    public UserInfo getUserInfo() {
        String userInfoJson = prefs.getString(KEY_USER_INFO, null);
        if (userInfoJson != null) {
            return gson.fromJson(userInfoJson, UserInfo.class);
        }
        return null;
    }
    
    /**
     * Check if user is logged in.
     */
    public boolean isLoggedIn() {
        return prefs.getBoolean(KEY_IS_LOGGED_IN, false);
    }
    
    /**
     * Clear session (logout).
     */
    public void clearSession() {
        editor.clear();
        editor.apply();
    }
    
    /**
     * Update stored user info (e.g., after setting staff name).
     */
    public void updateUserInfo(UserInfo userInfo) {
        editor.putString(KEY_USER_INFO, gson.toJson(userInfo));
        editor.apply();
    }
    
    /**
     * Get staff name from stored user info.
     */
    public String getStaffName() {
        UserInfo userInfo = getUserInfo();
        if (userInfo != null) {
            return userInfo.getStaffName();
        }
        return null;
    }
    
    /**
     * Get authorization header value.
     */
    public String getAuthHeader() {
        String token = getToken();
        if (token != null) {
            return "Bearer " + token;
        }
        return null;
    }
    
    /**
     * Get event ID from user info.
     */
    public int getEventId() {
        UserInfo userInfo = getUserInfo();
        if (userInfo != null && userInfo.getEventId() != null) {
            return userInfo.getEventId();
        }
        return 0;
    }
}
