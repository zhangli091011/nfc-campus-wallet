package com.campus.nfcwallet.nfc;

import android.app.Activity;
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.os.Bundle;

/**
 * NFC card reader for ISO14443-compliant cards.
 * 
 * Handles NFC card detection and UID extraction.
 */
public class NFCReader {
    private NfcAdapter nfcAdapter;
    private NFCCallback callback;
    
    /**
     * Callback interface for NFC card detection.
     */
    public interface NFCCallback {
        /**
         * Called when an NFC card is detected.
         * 
         * @param uid Card UID in hexadecimal format
         */
        void onCardDetected(String uid);
        
        /**
         * Called when an error occurs.
         * 
         * @param error Error message
         */
        void onError(String error);
    }
    
    /**
     * Initialize NFC reader.
     * 
     * @param activity Activity context
     * @throws NFCNotSupportedException if device doesn't have NFC hardware
     * @throws NFCDisabledException if NFC is disabled in device settings
     */
    public NFCReader(Activity activity) throws NFCNotSupportedException, NFCDisabledException {
        nfcAdapter = NfcAdapter.getDefaultAdapter(activity);
        
        if (nfcAdapter == null) {
            throw new NFCNotSupportedException("This device does not support NFC");
        }
        
        if (!nfcAdapter.isEnabled()) {
            throw new NFCDisabledException("NFC is disabled. Please enable it in device settings");
        }
    }
    
    /**
     * Enable NFC reader mode.
     * 
     * Starts listening for NFC cards.
     * 
     * @param activity Activity context
     * @param callback Callback for card detection events
     */
    public void enableReaderMode(Activity activity, NFCCallback callback) {
        this.callback = callback;
        
        if (nfcAdapter != null) {
            Bundle options = new Bundle();
            options.putInt(NfcAdapter.EXTRA_READER_PRESENCE_CHECK_DELAY, 250);
            
            nfcAdapter.enableReaderMode(
                activity,
                new NfcAdapter.ReaderCallback() {
                    @Override
                    public void onTagDiscovered(Tag tag) {
                        handleTag(tag);
                    }
                },
                NfcAdapter.FLAG_READER_NFC_A | 
                NfcAdapter.FLAG_READER_NFC_B | 
                NfcAdapter.FLAG_READER_SKIP_NDEF_CHECK,
                options
            );
        }
    }
    
    /**
     * Disable NFC reader mode.
     * 
     * Stops listening for NFC cards.
     * 
     * @param activity Activity context
     */
    public void disableReaderMode(Activity activity) {
        if (nfcAdapter != null) {
            nfcAdapter.disableReaderMode(activity);
        }
    }
    
    /**
     * Handle detected NFC tag.
     * 
     * @param tag Detected NFC tag
     */
    private void handleTag(Tag tag) {
        if (tag == null) {
            if (callback != null) {
                callback.onError("Invalid NFC tag");
            }
            return;
        }
        
        // Check if tag is ISO14443-compliant
        String[] techList = tag.getTechList();
        boolean isISO14443 = false;
        
        for (String tech : techList) {
            if (tech.contains("NfcA") || tech.contains("NfcB") || tech.contains("IsoDep")) {
                isISO14443 = true;
                break;
            }
        }
        
        if (!isISO14443) {
            if (callback != null) {
                callback.onError("Card is not ISO14443-compliant");
            }
            return;
        }
        
        // Extract UID
        byte[] uidBytes = tag.getId();
        String uid = bytesToHex(uidBytes);
        
        if (callback != null) {
            callback.onCardDetected(uid);
        }
    }
    
    /**
     * Convert byte array to hexadecimal string.
     * 
     * @param bytes Byte array to convert
     * @return Hexadecimal string (uppercase)
     */
    public static String bytesToHex(byte[] bytes) {
        StringBuilder hexString = new StringBuilder();
        for (byte b : bytes) {
            String hex = Integer.toHexString(0xFF & b);
            if (hex.length() == 1) {
                hexString.append('0');
            }
            hexString.append(hex);
        }
        return hexString.toString().toUpperCase();
    }
    
    /**
     * Exception thrown when device doesn't support NFC.
     */
    public static class NFCNotSupportedException extends Exception {
        public NFCNotSupportedException(String message) {
            super(message);
        }
    }
    
    /**
     * Exception thrown when NFC is disabled.
     */
    public static class NFCDisabledException extends Exception {
        public NFCDisabledException(String message) {
            super(message);
        }
    }
}
