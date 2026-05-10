package com.campus.nfcwallet.ui;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.campus.nfcwallet.R;
import com.campus.nfcwallet.models.Stock;

import java.util.List;

/**
 * RecyclerView adapter for stock list.
 * 
 * 股票列表适配器
 */
public class StockListAdapter extends RecyclerView.Adapter<StockListAdapter.StockViewHolder> {
    
    private List<Stock> stocks;
    private OnStockClickListener listener;
    
    public interface OnStockClickListener {
        void onStockClick(Stock stock);
    }
    
    public StockListAdapter(List<Stock> stocks, OnStockClickListener listener) {
        this.stocks = stocks;
        this.listener = listener;
    }
    
    @NonNull
    @Override
    public StockViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
            .inflate(R.layout.item_stock, parent, false);
        return new StockViewHolder(view);
    }
    
    @Override
    public void onBindViewHolder(@NonNull StockViewHolder holder, int position) {
        Stock stock = stocks.get(position);
        holder.bind(stock, listener);
    }
    
    @Override
    public int getItemCount() {
        return stocks.size();
    }
    
    static class StockViewHolder extends RecyclerView.ViewHolder {
        private TextView tvBoothName;
        private TextView tvClassName;
        private TextView tvPrice;
        private TextView tvShares;
        private TextView tvStatus;
        
        public StockViewHolder(@NonNull View itemView) {
            super(itemView);
            tvBoothName = itemView.findViewById(R.id.tv_booth_name);
            tvClassName = itemView.findViewById(R.id.tv_class_name);
            tvPrice = itemView.findViewById(R.id.tv_price);
            tvShares = itemView.findViewById(R.id.tv_shares);
            tvStatus = itemView.findViewById(R.id.tv_status);
        }
        
        public void bind(Stock stock, OnStockClickListener listener) {
            tvBoothName.setText(stock.getBoothName());
            tvClassName.setText(stock.getClassName());
            tvPrice.setText(String.format("¥%.2f/股", stock.getInitialPriceYuan()));
            tvShares.setText(String.format(
                "%d/%d股",
                stock.getAvailableShares(),
                stock.getTotalShares()
            ));
            
            if (stock.isAvailable()) {
                tvStatus.setText("可购买");
                tvStatus.setTextColor(0xFF4CAF50);  // Green
                itemView.setOnClickListener(v -> listener.onStockClick(stock));
                itemView.setEnabled(true);
                itemView.setAlpha(1.0f);
            } else {
                if (stock.getAvailableShares() == 0) {
                    tvStatus.setText("已售罄");
                } else {
                    tvStatus.setText("已暂停");
                }
                tvStatus.setTextColor(0xFF9E9E9E);  // Gray
                itemView.setOnClickListener(null);
                itemView.setEnabled(false);
                itemView.setAlpha(0.5f);
            }
        }
    }
}
