package com.campus.nfcwallet.api;

import com.campus.nfcwallet.models.BalanceResponse;
import com.campus.nfcwallet.models.BoothInfo;
import com.campus.nfcwallet.models.BoothPaymentRequest;
import com.campus.nfcwallet.models.EventInfo;
import com.campus.nfcwallet.models.LoanIssuanceRequest;
import com.campus.nfcwallet.models.LoanIssuanceResponse;
import com.campus.nfcwallet.models.LoginRequest;
import com.campus.nfcwallet.models.LoginResponse;
import com.campus.nfcwallet.models.ParticipantInfo;
import com.campus.nfcwallet.models.PaymentRequest;
import com.campus.nfcwallet.models.Product;
import com.campus.nfcwallet.models.RechargeRequest;
import com.campus.nfcwallet.models.RefundRequest;
import com.campus.nfcwallet.models.RefundResponse;
import com.campus.nfcwallet.models.Stock;
import com.campus.nfcwallet.models.StockBuyRequest;
import com.campus.nfcwallet.models.StockBuyResponse;
import com.campus.nfcwallet.models.StockHolding;
import com.campus.nfcwallet.models.StockOrderResponse;
import com.campus.nfcwallet.models.StockPurchaseRequest;
import com.campus.nfcwallet.models.StockPurchaseResponse;
import com.campus.nfcwallet.models.Transaction;
import com.campus.nfcwallet.models.TransactionHistoryResponse;
import com.campus.nfcwallet.models.TransactionResponse;
import com.campus.nfcwallet.models.UserInfo;

import java.util.List;
import java.util.Map;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.Header;
import retrofit2.http.POST;
import retrofit2.http.Path;
import retrofit2.http.Query;

/**
 * Retrofit API service interface for NFC Campus E-Wallet backend.
 * 
 * Defines all API endpoints.
 */
public interface WalletAPIService {
    
    // ==================== Authentication ====================
    
    /**
     * User login.
     * 
     * POST /auth/login
     * 
     * @param request Login request body
     * @return Login response with JWT token
     */
    @POST("auth/login")
    Call<LoginResponse> login(@Body LoginRequest request);
    
    /**
     * Get current user info.
     * 
     * GET /auth/me
     * 
     * @param authorization Authorization header (Bearer token)
     * @return User information
     */
    @GET("auth/me")
    Call<UserInfo> getCurrentUser(@Header("Authorization") String authorization);
    
    // ==================== Events ====================
    
    /**
     * Get event details.
     * 
     * GET /events/{event_id}
     * 
     * @param eventId Event ID
     * @return Event information
     */
    @GET("events/{event_id}")
    Call<EventInfo> getEvent(@Path("event_id") int eventId);
    
    // ==================== Booths ====================
    
    /**
     * Get list of booths.
     * 
     * GET /booths?status={status}
     * 
     * @param authorization Authorization header (Bearer token)
     * @param status Filter by booth status (optional)
     * @return List of booths
     */
    @GET("booths")
    Call<List<BoothInfo>> getBooths(
        @Header("Authorization") String authorization,
        @Query("status") String status
    );
    
    /**
     * Get booth details.
     * 
     * GET /booths/{booth_id}
     * 
     * @param authorization Authorization header (Bearer token)
     * @param boothId Booth ID
     * @return Booth information
     */
    @GET("booths/{booth_id}")
    Call<BoothInfo> getBooth(
        @Header("Authorization") String authorization,
        @Path("booth_id") int boothId
    );
    
    /**
     * Process booth payment.
     * 
     * POST /booths/{booth_id}/pay
     * 
     * @param authorization Authorization header (Bearer token)
     * @param boothId Booth ID
     * @param request Payment request body
     * @return Transaction response
     */
    @POST("booths/{booth_id}/pay")
    Call<TransactionResponse> processBoothPayment(
        @Header("Authorization") String authorization,
        @Path("booth_id") int boothId,
        @Body BoothPaymentRequest request
    );
    
    // ==================== Products ====================
    
    /**
     * Get products for a booth.
     * 
     * GET /products?booth_id={booth_id}&enabled=true
     * 
     * @param authorization Authorization header (Bearer token)
     * @param boothId Booth ID
     * @param enabled Filter by enabled status
     * @return List of products
     */
    @GET("products")
    Call<List<Product>> getProducts(
        @Header("Authorization") String authorization,
        @Query("booth_id") int boothId,
        @Query("enabled") Boolean enabled
    );
    
    // ==================== Participants ====================
    
    /**
     * Get participant by card UID.
     * 
     * GET /participants/by-card/{card_uid}
     * 
     * @param cardUid Card UID
     * @return Participant information
     */
    @GET("participants/by-card/{card_uid}")
    Call<ParticipantInfo> getParticipantByCard(@Path("card_uid") String cardUid);
    
    /**
     * Create new participant.
     * 
     * POST /participants
     * 
     * @param authorization Authorization header (Bearer token)
     * @param participantData Participant data
     * @return Created participant information
     */
    @POST("participants")
    Call<ParticipantInfo> createParticipant(
        @Header("Authorization") String authorization,
        @Body Map<String, Object> participantData
    );
    
    // ==================== Legacy Endpoints ====================
    
    /**
     * Get user balance (legacy mode - deprecated).
     * 
     * GET /balance?uid={uid}&timestamp={timestamp}&signature={signature}
     * 
     * @param uid User identifier
     * @param timestamp Request timestamp
     * @param signature Request signature
     * @return Balance response
     * @deprecated Use getBalanceByEvent instead
     */
    @Deprecated
    @GET("balance")
    Call<BalanceResponse> getBalance(
        @Query("uid") String uid,
        @Query("timestamp") long timestamp,
        @Query("signature") String signature
    );
    
    /**
     * Get user balance (event mode).
     * 
     * GET /balance?event_id={event_id}&card_uid={card_uid}
     * 
     * @param eventId Event ID
     * @param cardUid Card UID
     * @return Balance response
     */
    @GET("balance")
    Call<BalanceResponse> getBalanceByEvent(
        @Query("event_id") int eventId,
        @Query("card_uid") String cardUid
    );
    
    /**
     * Process payment transaction.
     * 
     * POST /pay
     * 
     * @param request Payment request body
     * @return Transaction response
     */
    @POST("pay")
    Call<TransactionResponse> processPayment(@Body PaymentRequest request);
    
    /**
     * Process recharge transaction.
     * 
     * POST /recharge
     * 
     * @param request Recharge request body
     * @return Transaction response
     */
    @POST("recharge")
    Call<TransactionResponse> processRecharge(@Body RechargeRequest request);
    
    /**
     * Get transaction history.
     * 
     * GET /transactions?uid={uid}&start_date={start_date}&end_date={end_date}
     * 
     * @param uid User identifier
     * @param startDate Optional start date filter
     * @param endDate Optional end date filter
     * @return Transaction history response
     */
    @GET("transactions")
    Call<TransactionHistoryResponse> getTransactionHistory(
        @Query("uid") String uid,
        @Query("start_date") String startDate,
        @Query("end_date") String endDate
    );
    
    // ==================== Stock Market ====================
    
    /**
     * Get list of stocks.
     * 
     * GET /stocks?event_id={event_id}&status={status}
     * 
     * @param authorization Authorization header (Bearer token)
     * @param eventId Event ID filter
     * @param status Status filter (optional)
     * @return List of stocks
     */
    @GET("stocks")
    Call<List<Stock>> getStocks(
        @Header("Authorization") String authorization,
        @Query("event_id") Integer eventId,
        @Query("status") String status
    );
    
    /**
     * Get stock details.
     * 
     * GET /stocks/{stock_id}
     * 
     * @param authorization Authorization header (Bearer token)
     * @param stockId Stock ID
     * @return Stock information
     */
    @GET("stocks/{stock_id}")
    Call<Stock> getStock(
        @Header("Authorization") String authorization,
        @Path("stock_id") int stockId
    );
    
    /**
     * Purchase stock (NFC card).
     * 
     * POST /stocks/purchase
     * 
     * @param request Stock purchase request body
     * @return Stock purchase response
     */
    @POST("stocks/purchase")
    Call<StockPurchaseResponse> purchaseStock(@Body StockPurchaseRequest request);
    
    /**
     * Get participant stock holdings.
     * 
     * GET /stocks/holdings/{participant_id}?event_id={event_id}
     * 
     * @param authorization Authorization header (Bearer token)
     * @param participantId Participant ID
     * @param eventId Event ID filter (optional)
     * @return List of stock holdings
     */
    @GET("stocks/holdings/{participant_id}")
    Call<List<StockHolding>> getStockHoldings(
        @Header("Authorization") String authorization,
        @Path("participant_id") int participantId,
        @Query("event_id") Integer eventId
    );
    
    // ==================== Stock API (New System) ====================
    
    /**
     * Buy stock (directly from main account).
     * 
     * POST /api/stock/buy
     * 
     * @param authorization Authorization header (Bearer token)
     * @param request Stock buy request body
     * @return Stock buy response
     */
    @POST("api/stock/buy")
    Call<StockBuyResponse> buyStock(
        @Header("Authorization") String authorization,
        @Body StockBuyRequest request
    );
    
    /**
     * Sell stock (return funds to main account at current price).
     * 
     * POST /api/stock/sell
     * 
     * @param authorization Authorization header (Bearer token)
     * @param request Stock sell request body
     * @return Stock sell response
     */
    @POST("api/stock/sell")
    Call<StockSellResponse> sellStock(
        @Header("Authorization") String authorization,
        @Body StockSellRequest request
    );
    
    /**
     * Get participant stock holdings (aggregated by booth).
     * 
     * GET /api/stock/holdings?card_uid={card_uid}&event_id={event_id}
     * 
     * @param authorization Authorization header (Bearer token)
     * @param cardUid Card UID
     * @param eventId Event ID
     * @return List of stock holdings by booth
     */
    @GET("api/stock/holdings")
    Call<List<StockHoldingInfo>> getStockHoldingsByCard(
        @Header("Authorization") String authorization,
        @Query("card_uid") String cardUid,
        @Query("event_id") int eventId
    );
    
    /**
     * Get stock orders.
     * 
     * GET /api/stock/orders/{participant_id}?event_id={event_id}
     * 
     * @param authorization Authorization header (Bearer token)
     * @param participantId Participant ID
     * @param eventId Event ID filter (optional)
     * @return List of stock orders
     */
    @GET("api/stock/orders/{participant_id}")
    Call<List<StockOrderResponse>> getStockOrders(
        @Header("Authorization") String authorization,
        @Path("participant_id") int participantId,
        @Query("event_id") Integer eventId
    );
    
    // ==================== Refund ====================

    /**
     * Get booth transaction history (for refund management).
     *
     * GET /booths/{booth_id}/transactions?card_uid={card_uid}&limit={limit}
     *
     * @param authorization Authorization header (Bearer token)
     * @param boothId Booth ID
     * @param cardUid Optional card UID filter
     * @param limit Optional result limit
     * @return List of transactions
     */
    @GET("booths/{booth_id}/transactions")
    Call<List<Transaction>> getBoothTransactions(
        @Header("Authorization") String authorization,
        @Path("booth_id") int boothId,
        @Query("card_uid") String cardUid,
        @Query("limit") Integer limit
    );

    /**
     * Process refund for a booth transaction (red-letter reversal).
     *
     * POST /api/trade/refund
     *
     * Requires admin PIN authorization.
     * Creates a refund ledger entry (red-letter reversal) and deducts booth score/stock price.
     *
     * @param authorization Authorization header (Bearer token)
     * @param request Refund request body (includes booth_id)
     * @return Refund response
     */
    @POST("api/trade/refund")
    Call<RefundResponse> processRefund(
        @Header("Authorization") String authorization,
        @Body RefundRequest request
    );

    // ==================== Bank Loan (Credit Advance) ====================
    
    /**
     * Issue a bank loan (credit advance) to a participant.
     * 
     * POST /api/bank/issue_loan
     * 
     * Business rules:
     * - Fixed 5% fee deducted upfront
     * - Principal 100 -> Fee 5 -> Disbursed 95
     * 
     * @param authorization Authorization header (Bearer token)
     * @param request Loan issuance request body
     * @return Loan issuance response with breakdown
     */
    @POST("api/bank/issue_loan")
    Call<LoanIssuanceResponse> issueLoan(
        @Header("Authorization") String authorization,
        @Body LoanIssuanceRequest request
    );
}
