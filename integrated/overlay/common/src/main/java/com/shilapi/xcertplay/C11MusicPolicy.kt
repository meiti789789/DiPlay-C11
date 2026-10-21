package com.shilapi.xcertplay

/** Session-local bookkeeping; never changes system volumes or launches another application. */
internal class C11MusicPolicy {
    interface Player {
        val id: Any
        val packageName: String
        val state: Int
        fun pause()
        fun play()
    }
    private data class Entry(val player: Player, val restore: Boolean, var paused: Boolean = false, var lastPause: Long = -10000)
    private val entries = linkedMapOf<Any, Entry>()
    private var baseline = true
    fun inspect(players: List<Player>, now: Long, pause: Boolean = true) {
        players.filter { supported(it.packageName) }.forEach { player ->
            val entry = entries.getOrPut(player.id) { Entry(player, baseline && player.state == 3) }
            if (pause && player.state == 3 && now - entry.lastPause >= 500) {
                try { player.pause(); entry.paused = true; entry.lastPause = now }
                catch (_: RuntimeException) { /* Retry on a later state observation. */ }
            }
        }
        baseline = false
    }
    fun finish(restore: Boolean, activeIds: Set<Any>? = null) {
        if (restore) entries.values.forEach {
            try { if (it.restore && it.paused && (activeIds == null || it.player.id in activeIds) && it.player.state == 2) it.player.play() }
            catch (_: RuntimeException) { }
        }
        entries.clear(); baseline = true
    }
    fun discard() = finish(false)
    companion object {
        fun supported(name: String): Boolean = name == "com.netease.cloudmusic" || name.startsWith("com.netease.cloudmusic.") ||
            name in setOf("com.netease.cloudmusiccar", "com.netease.cloudmusic.tv", "cn.kuwo.kwmusiccar",
                "cn.kuwo.player", "com.tencent.qqmusic", "com.tencent.qqmusiccar", "com.tencent.qqmusiccarh")
    }
}
