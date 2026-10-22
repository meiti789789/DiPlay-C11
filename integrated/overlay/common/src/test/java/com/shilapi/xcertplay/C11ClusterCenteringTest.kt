package com.shilapi.xcertplay

import android.content.Context
import com.shilapi.xcertplay.airplay.AirPlayConfig
import com.shilapi.xcertplay.airplay.AirPlayDisplayConfig
import com.shilapi.xcertplay.airplay.AirPlayInfoPlist
import com.shilapi.xcertplay.airplay.AirPlayInsets
import com.shilapi.xcertplay.airplay.CarPlayClusterDisplay
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.robolectric.shadows.ShadowBuild

/** Verifies the transmitted geometry and preference migration, not iPhone-rendered marker pixels. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28, 33])
class C11ClusterCenteringTest {
    private val context get() = RuntimeEnvironment.getApplication()
    private val migration get() = context.getSharedPreferences("c11-cluster", Context.MODE_PRIVATE)

    @Test fun advertisedAltScreenIsCentredForEveryContentAndScaleAndMainScreenIsIdentical() {
        val main = AirPlayDisplayConfig(widthPixels = 1920, heightPixels = 1080,
            safeArea = AirPlayInsets(top = 24, bottom = 16, left = 48, right = 32))
        val original = AirPlayConfig(deviceName = "C11", deviceId = "02:00:00:00:00:02",
            btMac = "02:00:00:00:00:02", sourceVersion = "366.0", main = main)
        val mainEntry = (AirPlayInfoPlist.build(original)["displays"] as List<*>).single()
        for (content in CarPlayClusterDisplay.Content.entries) {
            for (scale in CarPlayClusterDisplay.scalePresets) {
                val cluster = C11ClusterRoute.streamConfig(content, scale)
                val entries = AirPlayInfoPlist.build(original.copy(cluster = cluster))["displays"] as List<*>
                assertEquals("main stream 110 must not change", mainEntry, entries[0])
                val alt = entries[1] as Map<*, *>
                assertEquals(111, alt["type"])
                assertEquals(content.url, alt["initialURL"])
                val view = (alt["viewAreas"] as List<*>).single() as Map<*, *>
                val safe = view["safeArea"] as Map<*, *>
                val left = (safe["originXPixels"] as Number).toInt()
                val top = (safe["originYPixels"] as Number).toInt()
                val width = (safe["widthPixels"] as Number).toInt()
                val height = (safe["heightPixels"] as Number).toInt()
                assertEquals(cluster.widthPixels, 2 * left + width)
                assertEquals(cluster.heightPixels, 2 * top + height)
                assertEquals(cluster.widthPixels, view["widthPixels"])
                assertEquals(cluster.heightPixels, view["heightPixels"])
                assertEquals(true, safe["drawUIOutsideSafeArea"])
            }
        }
    }

    @Test fun savedLegacyDefaultsAreCorrectedOnceAndOriginalCoordinatesAreRetained() {
        ShadowBuild.setModel("msmnile_gvmq for arm64")
        for ((x, y) in listOf(56 to 50, 50 to 45)) {
            migration.edit().clear().commit()
            AirPlayPersistence.saveClusterMarkerXPercent(context, x)
            AirPlayPersistence.saveClusterMarkerYPercent(context, y)
            C11ClusterRoute.normalizeLegacyCenter(context)
            assertEquals(50, AirPlayPersistence.loadClusterMarkerXPercent(context))
            assertEquals(50, AirPlayPersistence.loadClusterMarkerYPercent(context))
            assertEquals(x, migration.getInt("centering_original_x", -1))
            assertEquals(y, migration.getInt("centering_original_y", -1))
            assertTrue(migration.getBoolean("centering_default_repaired", false))
            // A later intentional change is never overwritten on another connection.
            AirPlayPersistence.saveClusterMarkerXPercent(context, 65)
            C11ClusterRoute.normalizeLegacyCenter(context)
            assertEquals(65, AirPlayPersistence.loadClusterMarkerXPercent(context))
        }
    }

    @Test fun customOffsetsArePreservedAndNonC11PreferencesAreNeverMigrated() {
        ShadowBuild.setModel("msmnile_gvmq for arm64")
        AirPlayPersistence.saveClusterMarkerXPercent(context, 65)
        AirPlayPersistence.saveClusterMarkerYPercent(context, 60)
        C11ClusterRoute.normalizeLegacyCenter(context)
        assertEquals(65, AirPlayPersistence.loadClusterMarkerXPercent(context))
        assertEquals(60, AirPlayPersistence.loadClusterMarkerYPercent(context))
        assertFalse(migration.getBoolean("centering_default_repaired", true))
        migration.edit().clear().commit()
        ShadowBuild.setModel("other-car")
        AirPlayPersistence.saveClusterMarkerXPercent(context, 56)
        AirPlayPersistence.saveClusterMarkerYPercent(context, 50)
        C11ClusterRoute.normalizeLegacyCenter(context)
        assertEquals(56, AirPlayPersistence.loadClusterMarkerXPercent(context))
        assertFalse(migration.contains("centering_revision"))
    }
}
