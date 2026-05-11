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
    private double price; // Price in yuan (元)
    
    @SerializedName("cost_price")
    private Double costPrice; // Cost price in yuan (元)
    
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
    
    public double getPrice() {
        return price;
    }
    
    public double getPriceInYuan() {
        return price;
    }
    
    public Double getCostPrice() {
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
