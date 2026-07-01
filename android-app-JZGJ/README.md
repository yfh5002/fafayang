# 记账工具 - Android App

这是一个基于WebView的Android应用项目，使用Android Studio构建。

## 项目结构

```
android-app/
├── app/
│   ├── src/main/
│   │   ├── assets/
│   │   │   └── index.html          # 网页资源文件
│   │   ├── java/com/example/jizhanggongju/
│   │   │   └── MainActivity.java   # 主Activity
│   │   ├── res/                    # 资源文件
│   │   └── AndroidManifest.xml     # 应用配置
│   ├── build.gradle                # App模块构建配置
│   └── proguard-rules.pro          # ProGuard规则
├── build.gradle                    # 项目级构建配置
├── settings.gradle                 # 项目设置
├── gradle.properties               # Gradle属性
└── gradle/wrapper/                 # Gradle Wrapper

```

## 如何打开项目

1. 打开 Android Studio
2. 选择 "Open an existing Android Studio project"
3. 选择 `d:\XM\JIZHANGGONGJU\android-app` 文件夹
4. 等待Gradle同步完成

## 如何构建APK

### 方法一：通过Android Studio
1. 点击菜单栏 `Build` → `Build Bundle(s) / APK(s)` → `Build APK(s)`
2. 构建完成后，APK文件位于：`app/build/outputs/apk/debug/app-debug.apk`

### 方法二：通过命令行
```bash
# 进入项目目录
cd d:\XM\JIZHANGGONGJU\android-app

# 使用Gradle构建
.\gradlew assembleDebug

# APK文件将生成在 app/build/outputs/apk/debug/app-debug.apk
```

## 应用特性

- 使用 WebView 加载本地HTML页面
- 支持JavaScript
- 支持本地存储
- 竖屏显示
- 自定义数字键盘
- 图表统计功能

## 技术栈

- Android SDK 34
- Gradle 8.2
- WebView
- Tailwind CSS (网页端)
- Chart.js (图表)

## 注意事项

1. 首次打开项目时，Android Studio会自动下载所需的Gradle和依赖库
2. 确保已安装Android SDK和Android Studio
3. 应用需要网络权限来加载CDN资源（Tailwind CSS, Chart.js, Font Awesome）

## 自定义图标

项目使用了默认的Android图标。如需自定义应用图标：
1. 在 `app/src/main/res/mipmap-xxxhdpi/` 等目录替换 `ic_launcher.png` 和 `ic_launcher_round.png`
2. 或使用 Android Studio 的 Image Asset Studio 工具生成图标

## 版本信息

- 版本号: 1.0.0
- 版本代码: 1
- 最低SDK: 24 (Android 7.0)
- 目标SDK: 34 (Android 14)
