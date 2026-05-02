package com.campus.nfcwallet.ui;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageButton;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.campus.nfcwallet.R;
import com.campus.nfcwallet.models.CartItem;

import java.util.List;

/**
 * Adapter for shopping cart.
 */
public class CartAdapter extends RecyclerView.Adapter<CartAdapter.CartViewHolder> {
    
    private List<CartItem> cartItems;
    private OnCartItemChangeListener changeListener;
    private OnCartItemRemoveListener removeListener;
    
    public interface OnCartItemChangeListener {
        void onQuantityChange(CartItem item, int newQuantity);
    }
    
    public interface OnCartItemRemoveListener {
        void onRemove(CartItem item);
    }
    
    public CartAdapter(List<CartItem> cartItems, 
                      OnCartItemChangeListener changeListener,
                      OnCartItemRemoveListener removeListener) {
        this.cartItems = cartItems;
        this.changeListener = changeListener;
        this.removeListener = removeListener;
    }
    
    @NonNull
    @Override
    public CartViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
            .inflate(R.layout.item_cart, parent, false);
        return new CartViewHolder(view);
    }
    
    @Override
    public void onBindViewHolder(@NonNull CartViewHolder holder, int position) {
        CartItem item = cartItems.get(position);
        holder.bind(item, changeListener, removeListener);
    }
    
    @Override
    public int getItemCount() {
        return cartItems.size();
    }
    
    static class CartViewHolder extends RecyclerView.ViewHolder {
        private TextView nameText;
        private TextView priceText;
        private TextView quantityText;
        private TextView totalText;
        private ImageButton decreaseButton;
        private ImageButton increaseButton;
        private ImageButton removeButton;
        
        public CartViewHolder(@NonNull View itemView) {
            super(itemView);
            nameText = itemView.findViewById(R.id.cartItemNameText);
            priceText = itemView.findViewById(R.id.cartItemPriceText);
            quantityText = itemView.findViewById(R.id.cartItemQuantityText);
            totalText = itemView.findViewById(R.id.cartItemTotalText);
            decreaseButton = itemView.findViewById(R.id.decreaseButton);
            increaseButton = itemView.findViewById(R.id.increaseButton);
            removeButton = itemView.findViewById(R.id.removeButton);
        }
        
        public void bind(CartItem item, 
                        OnCartItemChangeListener changeListener,
                        OnCartItemRemoveListener removeListener) {
            nameText.setText(item.getProduct().getName());
            priceText.setText(String.format("¥%.2f", item.getProduct().getPriceInYuan()));
            quantityText.setText(String.valueOf(item.getQuantity()));
            totalText.setText(String.format("¥%.2f", item.getTotalPrice()));
            
            decreaseButton.setOnClickListener(v -> {
                if (changeListener != null) {
                    changeListener.onQuantityChange(item, item.getQuantity() - 1);
                }
            });
            
            increaseButton.setOnClickListener(v -> {
                if (changeListener != null) {
                    changeListener.onQuantityChange(item, item.getQuantity() + 1);
                }
            });
            
            removeButton.setOnClickListener(v -> {
                if (removeListener != null) {
                    removeListener.onRemove(item);
                }
            });
        }
    }
}
