package com.campus.nfcwallet.ui;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.campus.nfcwallet.R;
import com.campus.nfcwallet.models.Transaction;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/**
 * RecyclerView adapter for displaying transaction history.
 */
public class TransactionAdapter extends RecyclerView.Adapter<TransactionAdapter.TransactionViewHolder> {
    
    private List<Transaction> transactions;
    
    public TransactionAdapter(List<Transaction> transactions) {
        this.transactions = transactions;
    }
    
    @NonNull
    @Override
    public TransactionViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
            .inflate(R.layout.item_transaction, parent, false);
        return new TransactionViewHolder(view);
    }
    
    @Override
    public void onBindViewHolder(@NonNull TransactionViewHolder holder, int position) {
        Transaction transaction = transactions.get(position);
        holder.bind(transaction);
    }
    
    @Override
    public int getItemCount() {
        return transactions.size();
    }
    
    /**
     * Update transaction list and refresh display.
     */
    public void updateTransactions(List<Transaction> newTransactions) {
        this.transactions = newTransactions;
        notifyDataSetChanged();
    }
    
    /**
     * ViewHolder for transaction items.
     */
    static class TransactionViewHolder extends RecyclerView.ViewHolder {
        private TextView typeText;
        private TextView dateText;
        private TextView amountText;
        private TextView balanceAfterText;
        private TextView merchantText;
        
        public TransactionViewHolder(@NonNull View itemView) {
            super(itemView);
            typeText = itemView.findViewById(R.id.transactionType);
            dateText = itemView.findViewById(R.id.transactionDate);
            amountText = itemView.findViewById(R.id.transactionAmount);
            balanceAfterText = itemView.findViewById(R.id.transactionBalanceAfter);
            merchantText = itemView.findViewById(R.id.transactionMerchant);
        }
        
        public void bind(Transaction transaction) {
            // Set transaction type
            String type = transaction.getType();
            if ("payment".equals(type)) {
                typeText.setText(R.string.transaction_type_payment);
                typeText.setTextColor(itemView.getContext().getColor(R.color.error_red));
                amountText.setText(String.format("-¥%.2f", transaction.getAmount()));
                amountText.setTextColor(itemView.getContext().getColor(R.color.error_red));
            } else if ("recharge".equals(type)) {
                typeText.setText(R.string.transaction_type_recharge);
                typeText.setTextColor(itemView.getContext().getColor(R.color.success_green));
                amountText.setText(String.format("+¥%.2f", transaction.getAmount()));
                amountText.setTextColor(itemView.getContext().getColor(R.color.success_green));
            }
            
            // Set date
            String formattedDate = formatDate(transaction.getCreatedAt());
            dateText.setText(formattedDate);
            
            // Set balance after
            balanceAfterText.setText(String.format(
                itemView.getContext().getString(R.string.transaction_balance_after),
                transaction.getBalanceAfter()
            ));
            
            // Set merchant ID if available
            if (transaction.getMerchantId() != null && !transaction.getMerchantId().isEmpty()) {
                merchantText.setText("Merchant: " + transaction.getMerchantId());
                merchantText.setVisibility(View.VISIBLE);
            } else {
                merchantText.setVisibility(View.GONE);
            }
        }
        
        /**
         * Format ISO 8601 date string to readable format.
         */
        private String formatDate(String isoDate) {
            try {
                SimpleDateFormat inputFormat = new SimpleDateFormat(
                    "yyyy-MM-dd'T'HH:mm:ss",
                    Locale.getDefault()
                );
                SimpleDateFormat outputFormat = new SimpleDateFormat(
                    "yyyy-MM-dd HH:mm",
                    Locale.getDefault()
                );
                
                Date date = inputFormat.parse(isoDate);
                if (date != null) {
                    return outputFormat.format(date);
                }
            } catch (ParseException e) {
                // If parsing fails, return original string
            }
            
            return isoDate;
        }
    }
}
