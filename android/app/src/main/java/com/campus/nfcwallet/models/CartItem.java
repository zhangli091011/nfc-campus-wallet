package com.campus.nfcwallet.models;

/**
 * Shopping cart item model.
 */
public class CartItem {
    private Product product;
    private int quantity;
    
    public CartItem(Product product, int quantity) {
        this.product = product;
        this.quantity = quantity;
    }
    
    public Product getProduct() {
        return product;
    }
    
    public void setProduct(Product product) {
        this.product = product;
    }
    
    public int getQuantity() {
        return quantity;
    }
    
    public void setQuantity(int quantity) {
        this.quantity = quantity;
    }
    
    public void incrementQuantity() {
        this.quantity++;
    }
    
    public void decrementQuantity() {
        if (this.quantity > 0) {
            this.quantity--;
        }
    }
    
    public double getTotalPrice() {
        return product.getPriceInYuan() * quantity;
    }
    
    /**
     * Get total price in cents (分) for payment API.
     * Since price is now in yuan, multiply by 100 to get cents.
     */
    public int getTotalPriceInCents() {
        return (int) Math.round(product.getPrice() * 100) * quantity;
    }
}
