package com.campus.nfcwallet.ui;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.campus.nfcwallet.R;
import com.campus.nfcwallet.models.Product;

import java.util.List;

/**
 * Adapter for product grid.
 */
public class ProductAdapter extends RecyclerView.Adapter<ProductAdapter.ProductViewHolder> {
    
    private List<Product> products;
    private OnProductClickListener listener;
    
    public interface OnProductClickListener {
        void onProductClick(Product product);
    }
    
    public ProductAdapter(List<Product> products, OnProductClickListener listener) {
        this.products = products;
        this.listener = listener;
    }
    
    @NonNull
    @Override
    public ProductViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
            .inflate(R.layout.item_product, parent, false);
        return new ProductViewHolder(view);
    }
    
    @Override
    public void onBindViewHolder(@NonNull ProductViewHolder holder, int position) {
        Product product = products.get(position);
        holder.bind(product, listener);
    }
    
    @Override
    public int getItemCount() {
        return products.size();
    }
    
    static class ProductViewHolder extends RecyclerView.ViewHolder {
        private TextView nameText;
        private TextView priceText;
        private View container;
        
        public ProductViewHolder(@NonNull View itemView) {
            super(itemView);
            container = itemView;
            nameText = itemView.findViewById(R.id.productNameText);
            priceText = itemView.findViewById(R.id.productPriceText);
        }
        
        public void bind(Product product, OnProductClickListener listener) {
            nameText.setText(product.getName());
            priceText.setText(String.format("¥%.2f", product.getPriceInYuan()));
            
            // Disable if not available
            container.setEnabled(product.isAvailable());
            container.setAlpha(product.isAvailable() ? 1.0f : 0.5f);
            
            container.setOnClickListener(v -> {
                if (listener != null && product.isAvailable()) {
                    listener.onProductClick(product);
                }
            });
        }
    }
}
