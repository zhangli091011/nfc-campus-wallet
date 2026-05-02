package com.campus.nfcwallet.models;

import com.google.gson.annotations.SerializedName;

/**
 * Product model.
 */
public class Product {
    @SerializedName("id")
    private int id;
    
    @SerializedName("booth_id")
    private int boothId;
    
    @SerializedName("name")
    private String name;
    
    @SerializedName("price")
    private int price; // Price in cents
    
    @SerializedName("cost_price")
    private Integer costPrice; // Cost price in cents
    
    @SerializedName("stock")
    private Integer stock;
    
    @SerializedName("enabled")
    private boolean enabled;
    
    @SerializedName("created_at")
    private String createdAt;
    
    public int getId() {
        return id;
    }
    
    public int getBoothId() {
        return boothId;
    }
    
    public String getName() {
        return name;
    }
    
    public int getPrice() {
        return price;
    }
    
    public double getPriceInYuan() {
        return price / 100.0;
    }
    
    public Integer getCostPrice() {
        return costPrice;
    }
    
    public Integer getStock() {
        return stock;
    }
    
    public boolean isEnabled() {
        return enabled;
    }
    
    public String getCreatedAt() {
        return createdAt;
    }
    
    public boolean hasStock() {
        return stock == null || stock > 0;
    }
    
    public boolean isAvailable() {
        return enabled && hasStock();
    }
}
