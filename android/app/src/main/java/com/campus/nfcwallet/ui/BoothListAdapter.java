package com.campus.nfcwallet.ui;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.campus.nfcwallet.R;
import com.campus.nfcwallet.models.BoothInfo;

import java.util.List;

/**
 * Adapter for booth selection list.
 */
public class BoothListAdapter extends RecyclerView.Adapter<BoothListAdapter.BoothViewHolder> {
    
    private List<BoothInfo> booths;
    private OnBoothSelectedListener listener;
    
    public interface OnBoothSelectedListener {
        void onBoothSelected(BoothInfo booth);
    }
    
    public BoothListAdapter(List<BoothInfo> booths, OnBoothSelectedListener listener) {
        this.booths = booths;
        this.listener = listener;
    }
    
    @NonNull
    @Override
    public BoothViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
            .inflate(android.R.layout.simple_list_item_2, parent, false);
        return new BoothViewHolder(view);
    }
    
    @Override
    public void onBindViewHolder(@NonNull BoothViewHolder holder, int position) {
        BoothInfo booth = booths.get(position);
        holder.bind(booth, listener);
    }
    
    @Override
    public int getItemCount() {
        return booths.size();
    }
    
    static class BoothViewHolder extends RecyclerView.ViewHolder {
        private TextView text1;
        private TextView text2;
        
        public BoothViewHolder(@NonNull View itemView) {
            super(itemView);
            text1 = itemView.findViewById(android.R.id.text1);
            text2 = itemView.findViewById(android.R.id.text2);
        }
        
        public void bind(BoothInfo booth, OnBoothSelectedListener listener) {
            text1.setText(booth.getName());
            text2.setText("ID: " + booth.getId());
            
            itemView.setOnClickListener(v -> {
                if (listener != null) {
                    listener.onBoothSelected(booth);
                }
            });
        }
    }
}
