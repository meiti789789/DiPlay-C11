# DiPlay C11 · 2023 款零跑 C11 增程方控适配

**状态：测试阶段，尚未实车验证。** 目标是补充上一首、下一首、播放/暂停，同时保留 DiPlay 上游原版的在线升级能力。音量由原车处理。

本项目由独立的 **C11 Wheel Bridge 方控桥接应用** 和 GitHub Actions 发布流程组成。CarPlay 主程序来自上游，桥接通过 Android MediaSession 对接，不修改上游 APK，也不冒用原作者签名。

## 来源、借用与许可

- CarPlay / DiPlay 主项目：[shihabal3amri/DiPlay](https://github.com/shihabal3amri/DiPlay)，GPL-3.0。CarPlay、编解码、连接和原版在线更新归上游实现与维护。本项目未从零开发这些能力。
- 零跑方控广播名称与映射参考：[Wh1t3co1azZ/DiPlay-Leapmotor](https://github.com/Wh1t3co1azZ/DiPlay-Leapmotor)，GPL-3.0。感谢原作者的零跑适配研究。
- 本仓库提供独立桥接实现、屏幕诊断、按键去重与发布自动化，按 GPL-3.0 分发，全文见 [LICENSE](LICENSE)。原作者版权、上游附带的其它许可证与声明均应保留。
- 仓库内 Gradle Wrapper 来自 Gradle 项目，许可与声明见 [第三方声明](THIRD_PARTY_NOTICES.md)。
- 与零跑、Apple、上游作者没有官方合作或认证关系。上游实验性 CarPlay 身份说明、兼容性限制以原项目为准。本仓库不提交任何配件身份私钥或上游 Android 签名密钥。

## 支持范围

车主设备：2023 C11 增程；提供的图片显示 Android 9 / API 28，`msmnile_gvmq`、`qti`、`arm64-v8a`。图片不是系统固件版本页，不能据此推定具体固件号。APK 支持 Android 7.1+，包含已知旧款零跑广播协议，同时接受 C11 按键值的字符串和整型表示。广播实际可达性、通知权限和媒体会话行为仍需实车验证。

桥接不请求音频焦点，不写 CAN、不刷车机。没有联网权限，不读取或记录通知内容。通知使用权仅用于取得 DiPlay 媒体会话控制权限。记录保存在内存中，只有用户手动分享才会导出。

## 下载与安装

在本仓库 **Releases** 页面下载 `C11-WheelBridge-*.apk`。`Actions` 中构建的 debug APK 仅用于开发检查，正式可覆盖升级版本以 Releases 的固定签名包为准。

1. 保留工作正常的 DiPlay，通过车机正常 APK 安装方式另装桥接。
2. 手动开启桥接的“通知使用权”，返回确认监听已连接。
3. 停车并连接 CarPlay、播放音乐。先保持转发关闭，按上一首、下一首、暂停，检查屏幕记录。
4. 确认事件匹配后开启转发，验证每次只切一首、暂停与恢复正常。断开 CarPlay 后确认原车方控正常。
5. 若没有事件或没有会话，分享屏幕诊断记录。若重复切歌或误暂停，关闭桥接。撤销通知使用权即可停止监听。

早期 0.1.0 为 debug 签名；首次安装 0.1.1 release 版本前只需卸载旧桥接，不需卸载 DiPlay。

## 自动更新与上游同步

| 层级 | 行为 | 限制 |
| --- | --- | --- |
| DiPlay 主程序 | 原版保留自己的在线更新机制 | 零跑分支与上游原版签名不同，不能保证直接覆盖安装 |
| C11 桥接 | `bridge-v*` 标签自动构建、检查、使用固定私钥签名并发布 | 用户从 Releases 下载并确认安装，不静默安装 |
| 上游发布同步 | 每 6 小时检查上游（含预发布），校验 SHA256，原样同步原版 APK 与对应源码，再附加桥接包 | 同步结果标记为待实车验证；未来接口变化可能需要修改桥接 |

组合包中两个 APK 需要分别安装，不是把桥接注入 DiPlay。上游新版本不会删除桥接代码，但未来接口兼容性无法永久保证。同步脚本不会执行上游代码，不会重新签名上游 APK。缺少源码或校验值时停止发布。

## 构建与发布

JDK 17、Android SDK 35、Build Tools 34、Gradle 8.9（已提供校验固定的 Wrapper）：

```sh
python3 scripts/test_protocol.py
python3 -m unittest discover -s tests -p 'test_*.py'
./gradlew :app:lintDebug :app:assembleDebug
```

发布用 `version.json` 管理版本。仓库维护者须先设置 GitHub Actions Secrets：`C11_SIGNING_KEY_B64`、`C11_STORE_PASSWORD`；私钥别名为 `c11bridge`。推送与版本一致的 `bridge-v版本号` 标签后自动发布。签名缺失时失败，禁止回退到临时签名。私钥与密码不应写入仓库或日志。

## 设备操作约定

**所有涉及车机的 ADB 操作均须事先向车主说明具体命令和用途，并单独获得批准。** 本仓库的自动构建、上游同步与标准测试流程均不执行 ADB、不连接车机。
