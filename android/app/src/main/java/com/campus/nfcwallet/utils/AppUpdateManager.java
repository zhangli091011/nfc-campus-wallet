package com.campus.nfcwallet.utils;

import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.util.Log;

import androidx.core.content.FileProvider;

import com.campus.nfcwallet.api.APIClient;

import org.json.JSONObject;

import java.io.File;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

/**
 * App OTA Update Manager.
 * 
 * Checks for updates on app launch and handles APK download + install.
 */
public class AppUpdateManager {
    private static final String TAG = "AppUpdateManager";
    
    private final Context context;
    private long downloadId = -1;
    
    public AppUpdateManager(Context context) {
        this.context = context;
    }
    
    /**
     * Check for updates in background.
     * Shows dialog if update available.
     */
    public void checkForUpdate() {
        new Thread(() -> {
            try {
                int currentVersionCode = getCurrentVersionCode();
                String currentVersionName = getCurrentVersionName();
                
                String baseUrl = APIClient.getBaseUrl();
                String url = baseUrl + "app-update/check?version_code=" + currentVersionCode
                        + "&current_version=" + currentVersionName;
                
                OkHttpClient client = new OkHttpClient();
                Request request = new Request.Builder().url(url).build();
                Response response = client.newCall(request).execute();
                
                if (response.isSuccessful() && response.body() != null) {
                    String body = response.body().string();
                    JSONObject json = new JSONObject(body);
                    
                    boolean hasUpdate = json.optBoolean("has_update", false);
                    if (hasUpdate) {
                        String versionName = json.optString("version_name", "");
                        String releaseNotes = json.optString("release_notes", "");
                        long fileSize = json.optLong("file_size", 0);
                        boolean forceUpdate = json.optBoolean("force_update", false);
                        String downloadUrl = baseUrl + "app-update/download";
                        
                        showUpdateDialog(versionName, releaseNotes, fileSize, downloadUrl, forceUpdate);
                    }
                }
            } catch (Exception e) {
                Log.e(TAG, "Check update failed", e);
            }
        }).start();
    }
    
    private void showUpdateDialog(String versionName, String releaseNotes, 
                                   long fileSize, String downloadUrl, boolean forceUpdate) {
        if (context instanceof android.app.Activity) {
            ((android.app.Activity) context).runOnUiThread(() -> {
                String sizeStr = fileSize > 0 ? String.format(" (%.1f MB)", fileSize / 1024.0 / 1024.0) : "";
                String message = "发现新版本 v" + versionName + sizeStr + "\n\n";
                if (!releaseNotes.isEmpty()) {
                    message += "更新内容：\n" + releaseNotes;
                }
                
                AlertDialog.Builder builder = new AlertDialog.Builder(context)
                    .setTitle("版本更新")
                    .setMessage(message)
                    .setPositiveButton("立即更新", (dialog, which) -> {
                        startDownload(downloadUrl, versionName);
                    });
                
                if (!forceUpdate) {
                    builder.setNegativeButton("稍后再说", null);
                }
                builder.setCancelable(!forceUpdate);
                builder.show();
            });
        }
    }
    
    private void startDownload(String url, String versionName) {
        try {
            DownloadManager downloadManager = (DownloadManager) context.getSystemService(Context.DOWNLOAD_SERVICE);
            
            DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url));
            request.setTitle("NFC Campus Wallet v" + versionName);
            request.setDescription("正在下载更新...");
            request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            
            String fileName = "nfc-wallet-v" + versionName + ".apk";
            request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, fileName);
            
            downloadId = downloadManager.enqueue(request);
            
            // Register receiver to install after download
            context.registerReceiver(new BroadcastReceiver() {
                @Override
                public void onReceive(Context ctx, Intent intent) {
                    long id = intent.getLongExtra(DownloadManager.EXTRA_DOWNLOAD_ID, -1);
                    if (id == downloadId) {
                        ctx.unregisterReceiver(this);
                        installApk(fileName);
                    }
                }
            }, new IntentFilter(DownloadManager.ACTION_DOWNLOAD_COMPLETE),
               Context.RECEIVER_NOT_EXPORTED);
            
            Log.i(TAG, "Download started: " + url);
        } catch (Exception e) {
            Log.e(TAG, "Download failed", e);
        }
    }
    
    private void installApk(String fileName) {
        try {
            File file = new File(Environment.getExternalStoragePublicDirectory(
                    Environment.DIRECTORY_DOWNLOADS), fileName);
            
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                Uri uri = FileProvider.getUriForFile(context,
                        context.getPackageName() + ".fileprovider", file);
                intent.setDataAndType(uri, "application/vnd.android.package-archive");
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            } else {
                intent.setDataAndType(Uri.fromFile(file), "application/vnd.android.package-archive");
            }
            
            context.startActivity(intent);
        } catch (Exception e) {
            Log.e(TAG, "Install APK failed", e);
        }
    }
    
    private int getCurrentVersionCode() {
        try {
            PackageInfo pInfo = context.getPackageManager().getPackageInfo(context.getPackageName(), 0);
            return pInfo.versionCode;
        } catch (PackageManager.NameNotFoundException e) {
            return 0;
        }
    }
    
    private String getCurrentVersionName() {
        try {
            PackageInfo pInfo = context.getPackageManager().getPackageInfo(context.getPackageName(), 0);
            return pInfo.versionName;
        } catch (PackageManager.NameNotFoundException e) {
            return "0";
        }
    }
}
