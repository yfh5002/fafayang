package com.example.jizhanggongju;

import android.Manifest;
import android.annotation.SuppressLint;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.view.View;
import android.webkit.ConsoleMessage;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.ValueCallback;
import android.webkit.CookieManager;
import android.widget.ProgressBar;
import android.widget.Toast;
import android.media.Ringtone;
import android.media.RingtoneManager;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import androidx.annotation.NonNull;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.security.MessageDigest;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private ProgressBar progressBar;
    private ActivityResultLauncher<String[]> permissionLauncher;
    private ActivityResultLauncher<Intent> manageStorageLauncher;
    private JsInterface jsInterface;
    private java.util.function.Consumer<Boolean> permissionCallback;
    private ValueCallback<Uri[]> mUploadMessage;
    private final int REQUEST_SELECT_FILE = 100;
    private Handler timeoutHandler;

    @Override
    protected void onSaveInstanceState(@NonNull Bundle outState) {
        super.onSaveInstanceState(outState);
    }

    @Override
    protected void onRestoreInstanceState(@NonNull Bundle savedInstanceState) {
        super.onRestoreInstanceState(savedInstanceState);
    }

    private boolean isSavingData = false;
    private boolean dataSaveCompleted = false;

    private static final String PREF_NAME = "jzgj_data";
    private static final int DATA_VERSION = 1;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            setContentView(R.layout.activity_main);

            webView = findViewById(R.id.webView);
            progressBar = findViewById(R.id.progressBar);

            if (webView == null || progressBar == null) {
                android.util.Log.e("JZGJ", "无法找到WebView或ProgressBar");
                Toast.makeText(this, "界面初始化失败", Toast.LENGTH_LONG).show();
                finish();
                return;
            }

            permissionLauncher = registerForActivityResult(
            new ActivityResultContracts.RequestMultiplePermissions(),
            result -> {
                boolean allGranted = true;
                for (Boolean granted : result.values()) {
                    if (!granted) {
                        allGranted = false;
                        break;
                    }
                }
                if (permissionCallback != null) {
                    permissionCallback.accept(allGranted);
                }
            }
        );

        manageStorageLauncher = registerForActivityResult(
            new ActivityResultContracts.StartActivityForResult(),
            result -> {
                boolean granted = false;
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    granted = Environment.isExternalStorageManager();
                }
                if (permissionCallback != null) {
                    permissionCallback.accept(granted);
                }
            }
        );

        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webSettings.setDomStorageEnabled(true);
        webSettings.setAllowFileAccess(true);
        webSettings.setAllowContentAccess(true);
        webSettings.setDefaultTextEncodingName("UTF-8");
        // 允许本地文件加载外部CDN资源
        webSettings.setAllowUniversalAccessFromFileURLs(true);
        webSettings.setCacheMode(WebSettings.LOAD_DEFAULT);

        webSettings.setUseWideViewPort(true);
        webSettings.setLoadWithOverviewMode(true);
        webSettings.setSupportZoom(false);
        webSettings.setBuiltInZoomControls(false);
        webSettings.setDisplayZoomControls(false);
        webSettings.setDatabaseEnabled(true);
        webSettings.setLoadsImagesAutomatically(true);
        webSettings.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);
        
        // 布局和渲染优化
        webSettings.setLayoutAlgorithm(WebSettings.LayoutAlgorithm.NORMAL);
        webSettings.setDefaultFontSize(16);
        webSettings.setDefaultFixedFontSize(13);
        webSettings.setMinimumFontSize(8);
        webSettings.setTextZoom(100);
        webSettings.setUseWideViewPort(true);
        webSettings.setLoadWithOverviewMode(true);

        // 性能优化
        webSettings.setBlockNetworkImage(false);
        webSettings.setGeolocationEnabled(false);
        webSettings.setSaveFormData(false);
        webSettings.setSavePassword(false);

        // 优化触摸响应
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            webView.setRendererPriorityPolicy(WebView.RENDERER_PRIORITY_BOUND, true);
        }
        webSettings.setJavaScriptCanOpenWindowsAutomatically(true);
        webSettings.setMediaPlaybackRequiresUserGesture(false);

        // 启用硬件加速
        webView.setLayerType(View.LAYER_TYPE_HARDWARE, null);

        // 启用WebView调试
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
            WebView.setWebContentsDebuggingEnabled(true);
        }

        jsInterface = new JsInterface(this);
        webView.addJavascriptInterface(jsInterface, "Android");

        timeoutHandler = new Handler(Looper.getMainLooper());
        final long[] pageStartTime = {0};
        final Runnable timeoutRunnable = () -> {
            if (pageStartTime[0] > 0) {
                android.util.Log.w("JZGJ", "页面加载超时，强制隐藏进度条");
                progressBar.setVisibility(View.GONE);
                pageStartTime[0] = 0;
            }
        };

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
                super.onPageStarted(view, url, favicon);
                progressBar.setVisibility(View.VISIBLE);
                pageStartTime[0] = System.currentTimeMillis();
                // 3秒超时
                timeoutHandler.postDelayed(timeoutRunnable, 3000);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                progressBar.setVisibility(View.GONE);
                pageStartTime[0] = 0;
                timeoutHandler.removeCallbacks(timeoutRunnable);
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                super.onReceivedError(view, request, error);
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                    if (request.isForMainFrame()) {
                        progressBar.setVisibility(View.GONE);
                        pageStartTime[0] = 0;
                        timeoutHandler.removeCallbacks(timeoutRunnable);
                        showLoadError("页面加载失败，请检查网络连接");
                    }
                }
            }

            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                super.onReceivedError(view, errorCode, description, failingUrl);
                progressBar.setVisibility(View.GONE);
                pageStartTime[0] = 0;
                timeoutHandler.removeCallbacks(timeoutRunnable);
                showLoadError("页面加载失败：" + description);
            }
        });

        // 添加 WebChromeClient 捕获 JavaScript 错误和进度
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onConsoleMessage(ConsoleMessage consoleMessage) {
                android.util.Log.d("JZGJ-JS", consoleMessage.message() + " -- From line " +
                    consoleMessage.lineNumber() + " of " + consoleMessage.sourceId());
                return true;
            }

            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                if (newProgress < 100) {
                    progressBar.setVisibility(View.VISIBLE);
                } else {
                    progressBar.setVisibility(View.GONE);
                }
            }

            @SuppressWarnings("unused")
            public void openFileChooser(ValueCallback<Uri> uploadMsg) {
                mUploadMessage = new ValueCallback<Uri[]>() {
                    @Override
                    public void onReceiveValue(Uri[] value) {
                        uploadMsg.onReceiveValue(value != null && value.length > 0 ? value[0] : null);
                    }
                };
                Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("*/*");
                startActivityForResult(Intent.createChooser(intent, "选择文件"), REQUEST_SELECT_FILE);
            }

            @SuppressWarnings("unused")
            public void openFileChooser(ValueCallback<Uri> uploadMsg, String acceptType) {
                mUploadMessage = new ValueCallback<Uri[]>() {
                    @Override
                    public void onReceiveValue(Uri[] value) {
                        uploadMsg.onReceiveValue(value != null && value.length > 0 ? value[0] : null);
                    }
                };
                Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType(acceptType != null && !acceptType.isEmpty() ? acceptType : "*/*");
                startActivityForResult(Intent.createChooser(intent, "选择文件"), REQUEST_SELECT_FILE);
            }

            @SuppressWarnings("unused")
            public void openFileChooser(ValueCallback<Uri> uploadMsg, String acceptType, String capture) {
                mUploadMessage = new ValueCallback<Uri[]>() {
                    @Override
                    public void onReceiveValue(Uri[] value) {
                        uploadMsg.onReceiveValue(value != null && value.length > 0 ? value[0] : null);
                    }
                };
                Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType(acceptType != null && !acceptType.isEmpty() ? acceptType : "*/*");
                startActivityForResult(Intent.createChooser(intent, "选择文件"), REQUEST_SELECT_FILE);
            }

            @SuppressWarnings("unused")
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, Object fileChooserParams) {
                mUploadMessage = filePathCallback;
                Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("*/*");
                startActivityForResult(Intent.createChooser(intent, "选择文件"), REQUEST_SELECT_FILE);
                return true;
            }
        });

        enableRemoteDebugging();

        webView.loadUrl("file:///android_asset/index.html");
        } catch (Exception e) {
            android.util.Log.e("JZGJ", "onCreate 失败: " + e.getMessage(), e);
            Toast.makeText(this, "应用启动失败: " + e.getMessage(), Toast.LENGTH_LONG).show();
            finish();
        }
    }


    private void enableRemoteDebugging() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
            WebView.setWebContentsDebuggingEnabled(true);
        }
    }

    private void showLoadError(String message) {
        runOnUiThread(() -> {
            Toast.makeText(MainActivity.this, message, Toast.LENGTH_LONG).show();
            webView.loadUrl("about:blank");
        });
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            waitForDataSaveAndExit();
        }
    }

    private void waitForDataSaveAndExit() {
        runOnUiThread(() -> {
            try {
                isSavingData = true;
                dataSaveCompleted = false;

                webView.evaluateJavascript("(function() { " +
                    "if(typeof saveDataToSQLite === 'function') { " +
                        "console.log('[Native] 开始保存数据...'); " +
                        "saveDataToSQLite(); " +
                        "return true; " +
                    "} else { " +
                        "console.warn('[Native] saveDataToSQLite 函数不存在'); " +
                        "return false; " +
                    "} " +
                    "})()", value -> {
                        dataSaveCompleted = true;
                        isSavingData = false;
                        android.util.Log.i("JZGJ", "数据保存回调：" + value);

                        new Handler(Looper.getMainLooper()).postDelayed(() -> {
                            finishAffinity();
                            android.os.Process.killProcess(android.os.Process.myPid());
                        }, 500);
                    });

                new Handler(Looper.getMainLooper()).postDelayed(() -> {
                    if (!dataSaveCompleted) {
                        android.util.Log.w("JZGJ", "数据保存超时，强制退出");
                        finishAffinity();
                        android.os.Process.killProcess(android.os.Process.myPid());
                    }
                }, 3500);
            } catch (Exception e) {
                android.util.Log.e("JZGJ", "waitForDataSaveAndExit 失败：" + e.getMessage());
                finishAffinity();
                android.os.Process.killProcess(android.os.Process.myPid());
            }
        });
    }

    @Override
    protected void onPause() {
        super.onPause();
        forceSaveData();
    }

    @Override
    protected void onResume() {
        super.onResume();
        ensureDataLoaded();
    }

    private void ensureDataLoaded() {
        runOnUiThread(() -> {
            try {
                webView.evaluateJavascript("(function() { " +
                    "if(typeof loadDataFromSQLite === 'function') { " +
                        "console.log('[Native] 检查并重新加载数据...'); " +
                        "loadDataFromSQLite(); " +
                        "if(typeof loadDataAndRefresh === 'function') { " +
                            "loadDataAndRefresh(); " +
                        "} " +
                    "} " +
                    "})()", null);
            } catch (Exception e) {
                android.util.Log.e("JZGJ", "ensureDataLoaded 失败：" + e.getMessage());
            }
        });
    }

    @Override
    protected void onStop() {
        super.onStop();
        forceSaveData();
        flushWebViewStorage();
    }

    private void flushWebViewStorage() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            CookieManager.getInstance().flush();
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent intentData) {
        if (requestCode == REQUEST_SELECT_FILE) {
            if (mUploadMessage == null) return;

            if (resultCode == RESULT_OK) {
                if (intentData != null && intentData.getData() != null) {
                    mUploadMessage.onReceiveValue(new Uri[]{intentData.getData()});
                } else if (intentData != null && intentData.getClipData() != null) {
                    int count = intentData.getClipData().getItemCount();
                    Uri[] uris = new Uri[count];
                    for (int i = 0; i < count; i++) {
                        uris[i] = intentData.getClipData().getItemAt(i).getUri();
                    }
                    mUploadMessage.onReceiveValue(uris);
                } else {
                    mUploadMessage.onReceiveValue(new Uri[]{});
                }
            } else {
                mUploadMessage.onReceiveValue(null);
            }
            mUploadMessage = null;
        }
        super.onActivityResult(requestCode, resultCode, intentData);
    }

    @Override
    protected void onDestroy() {
        if (timeoutHandler != null) {
            timeoutHandler.removeCallbacksAndMessages(null);
        }

        if (jsInterface != null) {
            jsInterface.destroyCharts();
        }

        if (webView != null) {
            webView.destroy();
            webView = null;
        }
        jsInterface = null;
        permissionCallback = null;
        mUploadMessage = null;
        super.onDestroy();
    }

    private void forceSaveData() {
        if (isSavingData) {
            android.util.Log.w("JZGJ", "正在保存数据，跳过本次请求");
            return;
        }

        runOnUiThread(() -> {
            try {
                isSavingData = true;

                webView.evaluateJavascript("(function() { " +
                    "if(typeof saveDataToSQLite === 'function') { " +
                        "console.log('[Native] 强制保存数据...'); " +
                        "saveDataToSQLite(); " +
                        "return true; " +
                    "} else { " +
                        "console.warn('[Native] saveDataToSQLite 函数不存在'); " +
                        "return false; " +
                    "} " +
                    "})()", value -> {
                        isSavingData = false;
                        android.util.Log.i("JZGJ", "forceSaveData 执行完成：" + value);
                    });

                if (timeoutHandler != null) {
                    timeoutHandler.postDelayed(() -> {
                        isSavingData = false;
                    }, 1500);
                }
            } catch (Exception e) {
                isSavingData = false;
                android.util.Log.e("JZGJ", "forceSaveData 失败：" + e.getMessage());
            }
        });
    }

    class JsInterface {
        private Context context;

        public JsInterface(Context context) {
            this.context = context;
        }

        @JavascriptInterface
        public void requestStoragePermission(String callbackName) {
            runOnUiThread(() -> {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    if (!Environment.isExternalStorageManager()) {
                        try {
                            Intent intent = new Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION);
                            intent.setData(Uri.parse("package:" + getPackageName()));
                            manageStorageLauncher.launch(intent);
                        } catch (Exception e) {
                            Intent intent = new Intent(Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION);
                            manageStorageLauncher.launch(intent);
                        }
                        return;
                    }
                } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    if (ContextCompat.checkSelfPermission(MainActivity.this, Manifest.permission.READ_MEDIA_IMAGES)
                            != PackageManager.PERMISSION_GRANTED) {
                        permissionLauncher.launch(new String[]{Manifest.permission.READ_MEDIA_IMAGES});
                        return;
                    }
                } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    webView.evaluateJavascript(callbackName + "(true)", null);
                    return;
                } else {
                    if (ContextCompat.checkSelfPermission(MainActivity.this, Manifest.permission.WRITE_EXTERNAL_STORAGE)
                            != PackageManager.PERMISSION_GRANTED) {
                        permissionLauncher.launch(new String[]{
                            Manifest.permission.READ_EXTERNAL_STORAGE,
                            Manifest.permission.WRITE_EXTERNAL_STORAGE
                        });
                        return;
                    }
                }
                webView.evaluateJavascript(callbackName + "(true)", null);
            });
        }

        @JavascriptInterface
        public boolean saveAllData(String jsonData) {
            try {
                SharedPreferences prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
                SharedPreferences.Editor editor = prefs.edit();
                editor.putString("app_data", jsonData);
                editor.putInt("data_version", DATA_VERSION);
                editor.putLong("last_save_time", System.currentTimeMillis());

                String checksum = calculateChecksum(jsonData);
                editor.putString("data_checksum", checksum);

                // 使用apply()异步保存，避免阻塞UI线程
                editor.apply();

                log("saveAllData: 已异步保存，数据版本：" + DATA_VERSION + ", 数据长度：" + jsonData.length());
                return true;
            } catch (Exception e) {
                logError("saveAllData 失败：" + e.getMessage());
                e.printStackTrace();
                return false;
            }
        }

        @JavascriptInterface
        public synchronized boolean saveAllDataSync(String jsonData) {
            // 即使是同步版本也使用apply()，返回值始终为true
            // 因为apply()是异步的，但会确保数据最终被写入
            return saveAllData(jsonData);
        }

        @JavascriptInterface
        public String loadAllData() {
            try {
                SharedPreferences prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
                String data = prefs.getString("app_data", "");
                int version = prefs.getInt("data_version", 0);
                String savedChecksum = prefs.getString("data_checksum", "");
                long saveTime = prefs.getLong("last_save_time", 0);

                if (!data.isEmpty() && !data.equals("{}")) {
                    String currentChecksum = calculateChecksum(data);
                    if (!savedChecksum.isEmpty() && !currentChecksum.equals(savedChecksum)) {
                        logError("loadAllData: 数据校验失败！保存的校验和：" + savedChecksum + ", 当前校验和：" + currentChecksum);
                        runOnUiThread(() -> {
                            Toast.makeText(context, "数据文件已损坏，将使用默认数据", Toast.LENGTH_LONG).show();
                        });
                        return "";
                    }

                    log("loadAllData: 加载数据成功，版本：" + version + ", 长度：" + data.length() + ", 保存时间：" + formatTime(saveTime));
                    return data;
                }

                log("loadAllData: 没有保存的数据");
                return "";
            } catch (Exception e) {
                logError("loadAllData 失败：" + e.getMessage());
                e.printStackTrace();
                return "";
            }
        }

        @JavascriptInterface
        public boolean hasSavedData() {
            SharedPreferences prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
            String data = prefs.getString("app_data", "");
            return !data.isEmpty() && !data.equals("{}");
        }

        @JavascriptInterface
        public boolean exportBackup(String jsonData) {
            try {
                // 检查权限
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    if (!Environment.isExternalStorageManager()) {
                        logError("exportBackup: 缺少存储权限");
                        return false;
                    }
                }

                File backupDir = getBackupDirectory();
                if (!backupDir.exists()) {
                    boolean created = backupDir.mkdirs();
                    if (!created) {
                        logError("exportBackup: 无法创建备份目录 " + backupDir.getAbsolutePath());
                        return false;
                    }
                }

                String fileName = "jzgj_backup_" + new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(new Date()) + ".json";
                File backupFile = new File(backupDir, fileName);

                FileOutputStream fos = new FileOutputStream(backupFile);
                fos.write(jsonData.getBytes("UTF-8"));
                fos.close();

                log("exportBackup: 成功导出到 " + backupFile.getAbsolutePath());
                return true;
            } catch (Exception e) {
                logError("exportBackup 失败：" + e.getMessage());
                e.printStackTrace();
                return false;
            }
        }

        @JavascriptInterface
        public String importBackup() {
            try {
                // 检查权限
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    if (!Environment.isExternalStorageManager()) {
                        logError("importBackup: 缺少存储权限");
                        return "";
                    }
                }

                File backupDir = getBackupDirectory();
                if (!backupDir.exists() || !backupDir.isDirectory()) {
                    log("importBackup: 备份目录不存在: " + backupDir.getAbsolutePath());
                    return "";
                }

                File[] files = backupDir.listFiles((d, name) -> name.startsWith("jzgj_backup_") && name.endsWith(".json"));
                if (files == null || files.length == 0) {
                    log("importBackup: 没有找到备份文件");
                    return "";
                }

                java.util.Arrays.sort(files, (f1, f2) -> Long.compare(f2.lastModified(), f1.lastModified()));

                File latestFile = files[0];
                FileInputStream fis = new FileInputStream(latestFile);
                byte[] data = new byte[(int) latestFile.length()];
                fis.read(data);
                fis.close();

                String result = new String(data, "UTF-8");
                log("importBackup: 成功导入 " + latestFile.getName() + ", 长度：" + result.length());
                return result;
            } catch (Exception e) {
                logError("importBackup 失败：" + e.getMessage());
                e.printStackTrace();
                return "";
            }
        }

        @JavascriptInterface
        public String getBackupFilePath() {
            File backupDir = getBackupDirectory();
            return backupDir.getAbsolutePath();
        }

        @JavascriptInterface
        public String[] listBackupFiles() {
            try {
                File backupDir = getBackupDirectory();
                if (!backupDir.exists() || !backupDir.isDirectory()) {
                    return new String[0];
                }

                File[] files = backupDir.listFiles((d, name) -> name.startsWith("jzgj_backup_") && name.endsWith(".json"));
                if (files == null) {
                    return new String[0];
                }

                java.util.Arrays.sort(files, (f1, f2) -> Long.compare(f2.lastModified(), f1.lastModified()));

                String[] names = new String[files.length];
                for (int i = 0; i < files.length; i++) {
                    names[i] = files[i].getName();
                }
                return names;
            } catch (Exception e) {
                logError("listBackupFiles 失败：" + e.getMessage());
                return new String[0];
            }
        }

        @JavascriptInterface
        public boolean saveSetting(String key, String value) {
            try {
                SharedPreferences prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
                SharedPreferences.Editor editor = prefs.edit();
                editor.putString("setting_" + key, value);
                // 使用apply()异步保存，避免阻塞UI
                editor.apply();
                return true;
            } catch (Exception e) {
                logError("saveSetting 失败：" + e.getMessage());
                return false;
            }
        }

        @JavascriptInterface
        public String getSetting(String key, String defaultValue) {
            try {
                SharedPreferences prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
                return prefs.getString("setting_" + key, defaultValue);
            } catch (Exception e) {
                return defaultValue;
            }
        }

        @JavascriptInterface
        public String getSetting(String key) {
            return getSetting(key, "");
        }

        @JavascriptInterface
        public void clearAllData() {
            try {
                SharedPreferences prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
                SharedPreferences.Editor editor = prefs.edit();
                editor.clear();
                // 使用apply()异步清除，避免阻塞UI
                editor.apply();
                log("clearAllData: 已异步清除所有数据");
            } catch (Exception e) {
                logError("clearAllData 失败：" + e.getMessage());
            }
        }

        @JavascriptInterface
        public void destroyCharts() {
            runOnUiThread(() -> {
                try {
                    webView.evaluateJavascript("(function() { " +
                        "try { " +
                            "if (window.chartInstances) { " +
                                "Object.keys(window.chartInstances).forEach(function(key) { " +
                                    "if (window.chartInstances[key]) { " +
                                        "window.chartInstances[key].destroy(); " +
                                        "window.chartInstances[key] = null; " +
                                    "}" +
                                "}); " +
                                "window.chartInstances = {}; " +
                            "}" +
                            "if (window.attendanceStatsChartInstance) { " +
                                "window.attendanceStatsChartInstance.destroy(); " +
                                "window.attendanceStatsChartInstance = null; " +
                            "}" +
                            "if (window.attendanceTrendChartInstance) { " +
                                "window.attendanceTrendChartInstance.destroy(); " +
                                "window.attendanceTrendChartInstance = null; " +
                            "}" +
                            "console.log('[Native] 图表已清理'); " +
                        "} catch(e) { " +
                            "console.error('[Native] 清理图表失败:', e); " +
                        "} " +
                        "})()", null);
                    log("destroyCharts: 已发送图表清理指令");
                } catch (Exception e) {
                    logError("destroyCharts 失败：" + e.getMessage());
                }
            });
        }

        @JavascriptInterface
        public void showToast(String message) {
            runOnUiThread(() -> {
                Toast.makeText(context, message, Toast.LENGTH_LONG).show();
            });
        }

        @JavascriptInterface
        public void playAlarmSound() {
            runOnUiThread(() -> {
                try {
                    Uri notification = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
                    Ringtone ringtone = RingtoneManager.getRingtone(context, notification);
                    if (ringtone != null) {
                        ringtone.play();
                        log("播放系统铃声提醒");
                    }
                } catch (Exception e) {
                    logError("播放铃声失败：" + e.getMessage());
                    Toast.makeText(context, "提醒时间到了！", Toast.LENGTH_LONG).show();
                }
            });
        }

        @JavascriptInterface
        public void playAlarmWithSound(String soundType) {
            runOnUiThread(() -> {
                try {
                    int ringtoneType;
                    switch (soundType) {
                        case "alarm":
                            ringtoneType = RingtoneManager.TYPE_ALARM;
                            break;
                        case "notification":
                        default:
                            ringtoneType = RingtoneManager.TYPE_NOTIFICATION;
                            break;
                        case "ringtone":
                            ringtoneType = RingtoneManager.TYPE_RINGTONE;
                            break;
                    }

                    Uri soundUri = RingtoneManager.getDefaultUri(ringtoneType);
                    Ringtone ringtone = RingtoneManager.getRingtone(context, soundUri);
                    if (ringtone != null) {
                        ringtone.play();
                        log("播放" + soundType + "铃声");
                    }
                } catch (Exception e) {
                    logError("播放" + soundType + "铃声失败：" + e.getMessage());
                    Toast.makeText(context, "提醒时间到了！", Toast.LENGTH_LONG).show();
                }
            });
        }

        private File getBackupDirectory() {
            // 使用短路径方便查找: /storage/emulated/0/JZGJ/
            File backupDir = new File(Environment.getExternalStorageDirectory(), "JZGJ");
            if (!backupDir.exists()) {
                backupDir.mkdirs();
            }
            return backupDir;
        }

        private void log(String message) {
            android.util.Log.i("JZGJ", message);
        }

        private void logError(String message) {
            android.util.Log.e("JZGJ", message);
        }

        private String formatTime(long timestamp) {
            if (timestamp == 0) return "未知";
            return new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(new Date(timestamp));
        }

        private String calculateChecksum(String data) {
            try {
                MessageDigest md = MessageDigest.getInstance("MD5");
                byte[] hashBytes = md.digest(data.getBytes("UTF-8"));
                StringBuilder sb = new StringBuilder();
                for (byte b : hashBytes) {
                    sb.append(String.format("%02x", b));
                }
                return sb.toString();
            } catch (Exception e) {
                return String.valueOf(data.hashCode());
            }
        }
    }
}
