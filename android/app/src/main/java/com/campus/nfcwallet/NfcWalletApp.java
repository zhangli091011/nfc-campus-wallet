package com.campus.nfcwallet;

import android.app.Activity;
import android.app.Application;
import android.os.Bundle;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import com.campus.nfcwallet.utils.AppUpdateManager;

/**
 * Application class for NFC Campus Wallet.
 *
 * Registers lifecycle callbacks to trigger OTA update check
 * whenever any activity is resumed (with cooldown to avoid spam).
 */
public class NfcWalletApp extends Application {
    private static final String TAG = "NfcWalletApp";

    // Cooldown: only check once every 60 seconds
    private static final long UPDATE_CHECK_COOLDOWN_MS = 60_000;
    private long lastUpdateCheckTime = 0;

    @Override
    public void onCreate() {
        super.onCreate();

        registerActivityLifecycleCallbacks(new ActivityLifecycleCallbacks() {
            @Override
            public void onActivityResumed(@NonNull Activity activity) {
                long now = System.currentTimeMillis();
                if (now - lastUpdateCheckTime > UPDATE_CHECK_COOLDOWN_MS) {
                    lastUpdateCheckTime = now;
                    Log.d(TAG, "Checking for OTA update from: " + activity.getClass().getSimpleName());
                    new AppUpdateManager(activity).checkForUpdate();
                }
            }

            @Override
            public void onActivityCreated(@NonNull Activity activity, @Nullable Bundle savedInstanceState) {}
            @Override
            public void onActivityStarted(@NonNull Activity activity) {}
            @Override
            public void onActivityPaused(@NonNull Activity activity) {}
            @Override
            public void onActivityStopped(@NonNull Activity activity) {}
            @Override
            public void onActivitySaveInstanceState(@NonNull Activity activity, @NonNull Bundle outState) {}
            @Override
            public void onActivityDestroyed(@NonNull Activity activity) {}
        });
    }
}
