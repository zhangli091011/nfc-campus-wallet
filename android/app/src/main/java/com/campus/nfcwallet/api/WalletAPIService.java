package com.campus.nfcwallet.api;

import com.campus.nfcwallet.models.BoothTransactionsResponse;
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
import com.campus.nfcwallet.models.SetStaffNameRequest;
import com.campus.nfcwallet.models.SetStaffNameResponse;
import com.campus.nfcwallet.models.Stock;
import com.campus.nfcwallet.models.StockBuyRequest;
import com.campus.nfcwallet.models.StockBuyResponse;
import com.campus.nfcwallet.models.StockHolding;
import com.campus.nfcwallet.models.StockHoldingInfo;
import com.campus.nfcwallet.models.StockOrderResponse;
import com.campus.nfcwallet.models.StockPurchaseRequest;
import com.campus.nfcwallet.models.StockPurchaseResponse;
import com.campus.nfcwallet.models.StockSellRequest;
import com.campus.nfcwallet.models.StockSellResponse;
import com.campus.nfcwallet.models.Transaction;
import com.campus.nfcwallet.models.TransactionHistoryResponse;
import com.campus.nfcwallet.models.TransactionResponse;
import com.campus.nfcwallet.models.UserInfo;

import java.util.List;
import java.util.Map;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.DELETE;
import retrofit2.http.GET;
import retrofit2.http.Header;
import retrofit2.http.PATCH;
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
    
    /**
     * Set staff name (first login).
     * 
     * POST /auth/set-staff-name
     * 
     * @param authorization Authorization header (Bearer token)
     * @param request Staff name request body
     * @return Set staff name response
     */
    @POST("auth/set-staff-name")
    Call<SetStaffNameResponse> setStaffName(
        @Header("Authorization") String authorization,
        @Body SetStaffNameRequest request
    );
    
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

    /**
     * Update participant information (for real-name verification).
     *
     * PATCH /participants/{participant_id}
     *
     * @param authorization Authorization header (Bearer token)
     * @param participantId Participant ID
     * @param updateData Fields to update (name, class_name, student_no)
     * @return Updated participant information
     */
    @PATCH("participants/{participant_id}")
    Call<ParticipantInfo> updateParticipant(
        @Header("Authorization") String authorization,
        @Path("participant_id") int participantId,
        @Body Map<String, Object> updateData
    );

    /**
     * Delete participant (super_admin only).
     *
     * DELETE /participants/{participant_id}
     *
     * @param authorization Authorization header (Bearer token)
     * @param participantId Participant ID
     * @return Void (204 No Content on success)
     */
    @DELETE("participants/{participant_id}")
    Call<Void> deleteParticipant(
        @Header("Authorization") String authorization,
        @Path("participant_id") int participantId
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
    @POST("stock/buy")
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
    @POST("stock/sell")
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
    @GET("stock/holdings")
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
    @GET("stock/orders/{participant_id}")
    Call<List<StockOrderResponse>> getStockOrders(
        @Header("Authorization") String authorization,
        @Path("participant_id") int participantId,
        @Query("event_id") Integer eventId
    );
    
    // ==================== Refund ====================

    /**
     * Get booth transaction history (for refund management).
     *
     * GET /booths/{booth_id}/transactions?limit={limit}
     *
     * @param authorization Authorization header (Bearer token)
     * @param boothId Booth ID
     * @param limit Optional result limit
     * @return Booth transactions response with transactions list and total_count
     */
    @GET("booths/{booth_id}/transactions")
    Call<BoothTransactionsResponse> getBoothTransactions(
        @Header("Authorization") String authorization,
        @Path("booth_id") int boothId,
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
    @POST("trade/refund")
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
    @POST("bank/issue_loan")
    Call<LoanIssuanceResponse> issueLoan(
        @Header("Authorization") String authorization,
        @Body LoanIssuanceRequest request
    );

    /**
     * Repay loan (deduct from balance to clear debt).
     *
     * POST /bank/repay_loan
     *
     * @param authorization Authorization header (Bearer token)
     * @param request Repay loan request body
     * @return Repay loan response
     */
    @POST("bank/repay_loan")
    Call<Map<String, Object>> repayLoan(
        @Header("Authorization") String authorization,
        @Body Map<String, Object> request
    );

    /**
     * Return card (refund balance and unbind card).
     *
     * POST /bank/return_card
     *
     * @param authorization Authorization header (Bearer token)
     * @param request Return card request body
     * @return Return card response
     */
    @POST("bank/return_card")
    Call<Map<String, Object>> returnCard(
        @Header("Authorization") String authorization,
        @Body Map<String, Object> request
    );

    /**
     * Get participant loan summary (for card return terminal).
     *
     * GET /bank/loan_summary?event_id={event_id}&card_uid={card_uid}
     *
     * @param authorization Authorization header (Bearer token)
     * @param eventId Event ID
     * @param cardUid Card UID
     * @return Loan summary with loan_count and total_debt
     */
    @GET("bank/loan_summary")
    Call<Map<String, Object>> getParticipantLoans(
        @Header("Authorization") String authorization,
        @Query("event_id") int eventId,
        @Query("card_uid") String cardUid
    );

    // ==================== Card Detail (刷卡查看明细) ====================

    /**
     * Get comprehensive card detail (participant info + balance + loans + transactions).
     *
     * GET /card-detail/{card_uid}?event_id={event_id}&txn_limit={txn_limit}
     *
     * @param authorization Authorization header (Bearer token)
     * @param cardUid Card UID
     * @param eventId Event ID
     * @param txnLimit Transaction limit (default 50)
     * @return Full card detail map
     */
    @GET("card-detail/{card_uid}")
    Call<Map<String, Object>> getCardDetail(
        @Header("Authorization") String authorization,
        @Path("card_uid") String cardUid,
        @Query("event_id") int eventId,
        @Query("txn_limit") int txnLimit
    );

    /**
     * Record cash payment (现金收款).
     *
     * POST /booths/{booth_id}/cash-payment
     *
     * @param authorization Authorization header (Bearer token)
     * @param boothId Booth ID
     * @param request Request body containing amount and remark
     * @return Cash payment response
     */
    @POST("booths/{booth_id}/cash-payment")
    Call<Map<String, Object>> processCashPayment(
        @Header("Authorization") String authorization,
        @Path("booth_id") int boothId,
        @Body Map<String, Object> request
    );
}
