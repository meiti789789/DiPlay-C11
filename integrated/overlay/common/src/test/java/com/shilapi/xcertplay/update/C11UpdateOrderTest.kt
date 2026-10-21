package com.shilapi.xcertplay.update

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [29])
class C11UpdateOrderTest {
    private fun release(revision: Int, complete: Boolean = true, draft: Boolean = false) = JSONObject().apply {
        put("tag_name", "c11-v0.2.21-c11.$revision")
        put("draft", draft)
        put("prerelease", true)
        put("assets", JSONArray().apply {
            put(JSONObject().put("name", "DiPlay-C11-0.2.21-c11.$revision.apk")
                .put("browser_download_url", "https://example.com/$revision.apk"))
            if (complete) put(JSONObject().put("name", "SHA256SUMS.txt")
                .put("browser_download_url", "https://example.com/$revision/SHA256SUMS.txt"))
        })
    }
    @Test fun twoDigitRevisionWinsEvenWhenListedAfterNineAndThree() {
        val json = JSONArray().put(release(9)).put(release(8)).put(release(3)).put(release(10)).put(release(2))
        val newest = UpdateCatalog.parse(json.toString())
        assertEquals("c11-v0.2.21-c11.10", newest?.tagName)
        assertEquals("https://example.com/10.apk", newest?.apkUrl)
        assertTrue(UpdateVersion.isNewer(newest!!.tagName, "0.2.21-c11.9"))
        assertFalse(UpdateVersion.isNewer("c11-v0.2.21-c11.9", "0.2.21-c11.10"))
    }
    @Test fun incompleteOrDraftReleaseDoesNotMaskTheNewestInstallableRelease() {
        val json = JSONArray().put(release(12, complete = false)).put(release(13, draft = true))
            .put(release(9)).put(release(11)).put(release(10))
        assertEquals("c11-v0.2.21-c11.11", UpdateCatalog.parse(json.toString())?.tagName)
    }
    @Test fun releasePermutationAndDigitCountDoNotChangeSelection() {
        for (revisions in listOf(listOf(99, 100, 9, 11), listOf(11, 9, 100, 99))) {
            val json = JSONArray()
            revisions.forEach { json.put(release(it)) }
            assertEquals("c11-v0.2.21-c11.100", UpdateCatalog.parse(json.toString())?.tagName)
        }
    }
}
