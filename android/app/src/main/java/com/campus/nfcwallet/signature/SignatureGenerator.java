package com.campus.nfcwallet.signature;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/**
 * Signature generator for API request authentication.
 * 
 * Generates SHA256 signatures for balance queries and transactions.
 * Signature format: SHA256(uid + amount + timestamp + secret_key)
 */
public class SignatureGenerator {
    
    /**
     * Generate signature for balance query.
     * 
     * Signature = SHA256(uid + timestamp + secret_key)
     * 
     * @param uid User identifier from NFC card
     * @param timestamp Unix timestamp in seconds
     * @param secretKey Shared secret key
     * @return Hexadecimal signature string
     */
    public static String generateBalanceSignature(String uid, long timestamp, String secretKey) {
        String data = uid + timestamp + secretKey;
        return sha256Hex(data);
    }
    
    /**
     * Generate signature for transaction (payment or recharge).
     * 
     * Signature = SHA256(uid + amount + timestamp + secret_key)
     * 
     * @param uid User identifier from NFC card
     * @param amount Transaction amount
     * @param timestamp Unix timestamp in seconds
     * @param secretKey Shared secret key
     * @return Hexadecimal signature string
     */
    public static String generateTransactionSignature(String uid, double amount, long timestamp, String secretKey) {
        String data = uid + amount + timestamp + secretKey;
        return sha256Hex(data);
    }
    
    /**
     * Generate signature with integer amount.
     * 
     * Signature = SHA256(uid + amount + timestamp + secret_key)
     * 
     * @param uid User identifier from NFC card
     * @param amount Transaction amount (integer)
     * @param timestamp Unix timestamp in seconds
     * @return Hexadecimal signature string
     */
    public static String generateSignature(String uid, int amount, long timestamp) {
        // Use default secret key or get from config
        String secretKey = "your_secret_key_here";
        String data = uid + amount + timestamp + secretKey;
        return sha256Hex(data);
    }
    
    /**
     * Get current Unix timestamp in seconds.
     * 
     * @return Current timestamp in seconds
     */
    public static long getCurrentTimestamp() {
        return System.currentTimeMillis() / 1000;
    }
    
    /**
     * Compute SHA256 hash and convert to hexadecimal string.
     * 
     * @param data Input data to hash
     * @return Hexadecimal hash string
     */
    private static String sha256Hex(String data) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(data.getBytes(StandardCharsets.UTF_8));
            return bytesToHex(hash);
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("SHA-256 algorithm not available", e);
        }
    }
    
    /**
     * Convert byte array to hexadecimal string.
     * 
     * @param bytes Byte array to convert
     * @return Hexadecimal string (lowercase)
     */
    private static String bytesToHex(byte[] bytes) {
        StringBuilder hexString = new StringBuilder();
        for (byte b : bytes) {
            String hex = Integer.toHexString(0xff & b);
            if (hex.length() == 1) {
                hexString.append('0');
            }
            hexString.append(hex);
        }
        return hexString.toString();
    }
}
