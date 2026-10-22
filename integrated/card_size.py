"""Extend C11 custom-card maximum without changing existing sizes or marker settings."""
def apply(target, replace):
    java = target/'common/src/main/java/com/shilapi/xcertplay'
    overlay = target/'shared/src/main/java/com/shilapi/xcertplay/airplay/ClusterTurnCardOverlay.kt'
    replace(overlay, '    /** Small-window card placement',
        '    /** C11 extension: 190% doubles the legacy 95% maximum in both dimensions. */\n    val extendedSizePercents = (30..190 step 5).toList()\n\n    /** Small-window card placement')
    replace(overlay, '''        val size = snap(sizePercent, sizePercents)
        // The card keeps its ~2.6:1 banner aspect at any size.
        val width = (window.width * size / 100).coerceAtLeast(150).coerceAtMost(panelWidth)
        val height = (width / 2.64f).toInt().coerceAtLeast(58).coerceAtMost((window.height * 0.55f).toInt())''', '''        val size = snap(sizePercent, extendedSizePercents)
        // Preserve every legacy size pixel-for-pixel, including its minimum/cap rounding.
        val legacySize = size.coerceAtMost(sizePercents.last())
        val legacyWidth = (window.width * legacySize / 100).coerceAtLeast(150).coerceAtMost(panelWidth)
        val legacyHeight = (legacyWidth / 2.64f).toInt().coerceAtLeast(58).coerceAtMost((window.height * 0.55f).toInt())
        val requestedScale = if (size > sizePercents.last()) size.toDouble() / sizePercents.last() else 1.0
        val scale = minOf(requestedScale, panelWidth.toDouble() / legacyWidth, panelHeight.toDouble() / legacyHeight)
        val width = kotlin.math.round(legacyWidth * scale).toInt().coerceIn(1, panelWidth)
        val height = kotlin.math.round(legacyHeight * scale).toInt().coerceIn(1, panelHeight)''')
    persistence = java/'AirPlayPersistence.kt'
    text = persistence.read_text()
    assert text.count('ClusterTurnCardOverlay.sizePercents') == 4
    text = text.replace('ClusterTurnCardOverlay.sizePercents', 'clusterTurnCardSizePercents()')
    anchor = '    fun loadClusterTurnCardOverlaySizePercent(context: Context): Int {'
    text = text.replace(anchor, '''    fun clusterTurnCardSizePercents(): List<Int> = if (C11ClusterRoute.platformSupported())
        ClusterTurnCardOverlay.extendedSizePercents else ClusterTurnCardOverlay.sizePercents

'''+anchor)
    persistence.write_text(text)
    ui = java/'DiPlayActivity.kt'
    replace(ui, 'ClusterTurnCardOverlay.sizePercents,', 'AirPlayPersistence.clusterTurnCardSizePercents(),', 2)
    view = java/'ClusterTurnCardView.kt'
    replace(view, '        val h = (cardHeight * 0.40f).coerceAtLeast(34f)', '''        val extensionScale = if (sizePercent > 95) sizePercent.coerceAtMost(190) / 95f else 1f
        val h = (cardHeight / extensionScale * 0.40f).coerceAtLeast(34f) * extensionScale''')
    replace(view, '        val radius = h * 0.30f', '''        strokePaint.strokeWidth = 2f * if (sizePercent > 95) sizePercent.coerceAtMost(190) / 95f else 1f
        val radius = h * 0.30f''')
