package com.shilapi.xcertplay
import com.shilapi.xcertplay.update.UpdateVersion
import com.shilapi.xcertplay.update.UpdateCatalog
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
@RunWith(RobolectricTestRunner::class) @Config(sdk=[28])
class C11UpdatesTest {
    @Test fun revisionOrderingAndUpstreamOrdering() {
        assertTrue(UpdateVersion.isNewer("c11-v0.2.21-c11.2", "0.2.21-c11.1"))
        assertFalse(UpdateVersion.isNewer("c11-v0.2.21-c11.1", "0.2.21-c11.1"))
        assertTrue(UpdateVersion.isNewer("c11-v0.2.22-c11.1", "0.2.21-c11.99"))
        assertFalse(UpdateVersion.isNewer("c11-v0.2.20-c11.99", "0.2.21-c11.1"))
    }
    @Test fun companionAndOriginalComboAreNeverOfferedAsIntegratedUpdates() {
        val json = """[
        {"tag_name":"bridge-v0.1.2","assets":[{"name":"bridge.apk","browser_download_url":"wrong"},{"name":"SHA256SUMS.txt","browser_download_url":"wrong"}]},
        {"tag_name":"c11-upstream-v0.2.21-bridge-0.1.2","assets":[{"name":"original.apk","browser_download_url":"wrong"}]},
        {"tag_name":"c11-v0.2.21-c11.1","assets":[{"name":"DiPlay-C11-0.2.21-c11.1.apk","browser_download_url":"right"},{"name":"SHA256SUMS.txt","browser_download_url":"sum"}]}
        ]"""
        assertEquals("right", UpdateCatalog.parse(json)?.apkUrl)
    }
}
