# Design Document: Android Cashier Terminal Upgrade

## Overview

The Android Cashier Terminal Upgrade transforms the existing NFC Campus E-Wallet Android application into a full-featured point-of-sale (POS) terminal for booth cashiers. The upgraded system integrates with the backend Booth Management System to provide authentication, product management, shopping cart functionality, and multiple payment modes while preserving backward compatibility with existing NFC reading and signature verification mechanisms.

### Key Features

- **JWT-based Authentication**: Secure login for booth cashiers with role-based access control
- **Booth Context**: Display event and booth information for operational clarity
- **Product Management**: Browse and select products from the booth's inventory
- **Shopping Cart**: Build multi-item orders with quantity management
- **Dual Payment Modes**: Support both product selection and quick amount entry
- **Participant Information**: Display participant name and balance after card scan
- **Offline Caching**: Cache critical data for resilient operation
- **Backward Compatibility**: Preserve existing NFC and signature logic

### Design Principles

1. **Single-Screen Design**: All cashier operations accessible from one main screen
2. **Touch-Friendly UI**: Large buttons (minimum 48dp) for easy interaction
3. **Clear Visual Feedback**: Color-coded states (green=success, red=error, blue=info, orange=warning)
4. **Resilient Operation**: Graceful degradation with offline caching
5. **Security First**: Encrypted token storage, secure API communication
6. **Backward Compatible**: Preserve existing components without modification

---

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Android Application"
        UI[UI Layer<br/>Activities & Layouts]
        BL[Business Logic Layer<br/>Managers & Controllers]
        API[API Client Layer<br/>Retrofit Services]
        DATA[Data Layer<br/>Models & Cache]
        NFC[NFC Layer<br/>Card Reader]
        SIG[Security Layer<br/>Signature & JWT]
    end
    
    subgraph "Backend Services"
        AUTH[Authentication Service<br/>/auth/login]
        BOOTH[Booth Service<br/>/booths/*]
        PROD[Product Service<br/>/products]
        TXN[Transaction Service<br/>/pay, /recharge]
        BAL[Balance Service<br/>/balance]
    end
    
    UI --> BL
    BL --> API
    BL --> DATA
    BL --> NFC
    BL --> SIG
    API --> AUTH
    API --> BOOTH
    API --> PROD
    API --> TXN
    API --> BAL
    DATA --> CACHE[(SharedPreferences<br/>Encrypted Storage)]
