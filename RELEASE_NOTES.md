2023 款零跑 C11 增程方控桥接 · 待实车验证。

独立 APK，支持参考协议的上一首、下一首、播放/暂停，兼容 Android 7.1+；车主图片显示 Android 9 / API 28 / arm64-v8a / msmnile_gvmq，但尚未完成实车按键验证。

保留现有 DiPlay，另装桥接并手动打开通知使用权。先保持转发关闭，连接 CarPlay 播放音乐，分别按三个按键查看记录；确认匹配后再开启转发。断开 CarPlay 后检查原车音乐，发生重复切歌时关闭桥接。

桥接使用自己的固定私钥签名，后续正式测试版本可同签名覆盖升级。早期 0.1.0 是 debug 签名，不能被这个 release 签名直接覆盖；只需卸载早期桥接应用再装本包，不要卸载 DiPlay。

上游 DiPlay：https://github.com/shihabal3amri/DiPlay （GPL-3.0；其它许可保留在上游源码）。
零跑广播协议参考：https://github.com/Wh1t3co1azZ/DiPlay-Leapmotor （GPL-3.0）。
本项目并非从零开发的 CarPlay，不代表上游作者、零跑或 Apple；不包含或重新发布任何作者签名私钥。

不改 DiPlay 更新源、不重签上游 APK；未来接口兼容性不能保证。仓库的上游同步发布会附带原版 APK 和对应源码，不代表实车验证完成，也不是车机静默 OTA。
