"""Keep the C11 instrument transparent until a decoded texture frame arrives."""
def apply(target, replace):
    path = target/'common/src/main/java/com/shilapi/xcertplay/ClusterMapPresentation.kt'
    replace(path, '    private var streamActive = false', '''    private var streamActive = false
    private val c11FrameGate = C11ClusterFrameGate()
    private fun c11Output() = C11ClusterRoute.plan(sizeOf(display).x, sizeOf(display).y) != null
    private fun applyC11Visibility() {
        if (!c11Output()) return
        window?.let { w ->
            val next = if (c11FrameGate.visible) 1f else 0f
            if (w.attributes.alpha != next) w.attributes = w.attributes.apply { alpha = next }
        }
    }
    internal fun onC11FrameUpdated() {
        c11FrameGate.frameReceived()
        applyC11Visibility()
    }''')
    replace(path, '        if (plan != null) {\n            val textureView = TextureView(context)', '''        if (c11 != null) {
            val textureView = TextureView(context)
            textureView.surfaceTextureListener = object : TextureView.SurfaceTextureListener {
                override fun onSurfaceTextureAvailable(texture: SurfaceTexture, width: Int, height: Int) {
                    outputSurface = Surface(texture).also(onSurface)
                }
                override fun onSurfaceTextureSizeChanged(texture: SurfaceTexture, width: Int, height: Int) = Unit
                override fun onSurfaceTextureUpdated(texture: SurfaceTexture) = onC11FrameUpdated()
                override fun onSurfaceTextureDestroyed(texture: SurfaceTexture): Boolean {
                    c11FrameGate.resetFrames(); applyC11Visibility()
                    onSurface(null)
                    outputSurface?.release(); outputSurface = null
                    return true
                }
            }
            root.addView(textureView, videoParams)
            videoView = textureView
        } else if (plan != null) {
            val textureView = TextureView(context)''')
    replace(path, '        C11ClusterRoute.configureWindow(window, display)\n    }\n\n    override fun onStart()', '''        C11ClusterRoute.configureWindow(window, display)
        if (c11 != null) {
            videoView?.alpha = 1f
            waitingLabel?.visibility = View.GONE
            applyC11Visibility()
        }
    }

    override fun onStart()''')
    replace(path, '    fun setStreamActive(active: Boolean) {\n        if (streamActive == active) return', '''    fun setStreamActive(active: Boolean) {
        if (c11Output()) {
            streamActive = active
            c11FrameGate.setActive(active)
            videoView?.alpha = 1f
            waitingLabel?.visibility = View.GONE
            applyC11Visibility()
            return
        }
        if (streamActive == active) return''')
    replace(path, '    fun setMapVisible(visible: Boolean) {\n        mapVisible = visible', '''    fun setMapVisible(visible: Boolean) {
        mapVisible = visible
        if (c11Output()) {
            c11FrameGate.shown = visible
            applyC11Visibility()
            return
        }''')

    host = target/'common/src/main/java/com/shilapi/xcertplay/CarPlayHostActivity.kt'
    text = host.read_text()
    anchor = 'activeScreenStreamTypes.clear()'
    if text.count(anchor) != 3:
        raise RuntimeError('C11 visibility: expected exactly three stream reset paths')
    text = text.replace(anchor, anchor + '\n                    if (C11ClusterRoute.platformSupported()) clusterPresentation?.setStreamActive(false)')
    host.write_text(text)
    replace(host, '                    C11MusicGuard.stop(session)',
        '                    C11MusicGuard.stop(session)\n                    if (C11ClusterRoute.platformSupported()) clusterPresentation?.setStreamActive(false)')
    replace(host, '                    startupRetryBudget.disconnected()\n                    if (menuOpen) {',
        '                    startupRetryBudget.disconnected()\n                    if (C11ClusterRoute.platformSupported()) clusterPresentation?.setStreamActive(false)\n                    if (menuOpen) {')
