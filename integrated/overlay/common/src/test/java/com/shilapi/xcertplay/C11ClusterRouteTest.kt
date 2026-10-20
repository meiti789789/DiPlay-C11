package com.shilapi.xcertplay

import android.hardware.display.DisplayManager
import android.view.Display
import android.view.Gravity
import android.view.WindowManager
import org.junit.After
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import org.robolectric.shadows.ShadowBuild
import org.robolectric.shadows.ShadowDisplayManager

@RunWith(RobolectricTestRunner::class) @Config(sdk = [28, 33], qualifiers="mdpi")
class C11ClusterRouteTest {
    private val context get() = RuntimeEnvironment.getApplication()
    private val added = mutableListOf<Int>()
    private fun display(name: String, geometry: String="w1920dp-h720dp-mdpi", flags: Int=Display.FLAG_PRESENTATION): Display {
        val id=ShadowDisplayManager.addDisplay(geometry,5);added += id
        return context.getSystemService(DisplayManager::class.java).getDisplay(id).also {
            shadowOf(it).setName(name);shadowOf(it).setFlags(flags)
        }
    }
    private fun c11() { ShadowBuild.setModel("msmnile_gvmq for arm64") }
    @After fun cleanup() { C11ClusterRoute.select(context,null);added.forEach { ShadowDisplayManager.removeDisplay(it) } }
    @Test fun knownPlatformAndGeometryOnly() {
        assertTrue(C11ClusterRoute.platformSupported("qti/msmnile_gvmq/board:9", "unknown"))
        assertTrue(C11ClusterRoute.platformSupported("unknown", "msmnile_gvmq for arm64"))
        assertFalse(C11ClusterRoute.platformSupported("byd/dilink", "other"))
        assertEquals(C11ClusterRoute.Viewport(),C11ClusterRoute.plan(1920,720,true))
        assertNull(C11ClusterRoute.plan(1920,1080,true));assertNull(C11ClusterRoute.plan(1920,720,false))
    }
    @Test fun neverAutomaticallyChoosesAnInstrumentOrPassengerPanel() {
        c11();display("C11 instrument");display("passenger")
        AirPlayPersistence.saveLegacyClusterEnabled(context,true)
        AirPlayPersistence.saveAdbClusterEnabled(context,true)
        assertFalse(AdbClusterRouter.enabled(context))
        assertNull(C11ClusterRoute.findDisplay(context))
    }
    @Test fun explicitChoiceUsesPublicExactGeometryAndNeverDefaultDisplay() {
        c11();val panel=display("chosen instrument")
        display("wrong geometry","w1280dp-h720dp-mdpi")
        display("private",flags=Display.FLAG_PRIVATE or Display.FLAG_PRESENTATION)
        assertEquals(listOf(panel.displayId),C11ClusterRoute.candidates(context).map { it.displayId })
        C11ClusterRoute.select(context,panel.name)
        assertEquals(panel.displayId,ClusterMapPresentation.findDisplay(context)?.displayId)
    }
    @Test fun duplicateOrDisappearingNamesDisableRouting() {
        c11();val first=display("same");val second=display("same")
        C11ClusterRoute.select(context,"same",first.displayId);assertNull(C11ClusterRoute.findDisplay(context))
        ShadowDisplayManager.removeDisplay(first.displayId);added.remove(first.displayId)
        assertNull(C11ClusterRoute.findDisplay(context))
        C11ClusterRoute.select(context,second.name,second.displayId)
        assertEquals(second.displayId,C11ClusterRoute.findDisplay(context)?.displayId)
        C11ClusterRoute.select(context,"removed");assertNull(C11ClusterRoute.findDisplay(context))
    }
    @Test fun squareStreamAndWindowDoNotFillTheInstrumentPanel() {
        c11();val panel=display("instrument");C11ClusterRoute.select(context,panel.name)
        val config=C11ClusterRoute.streamConfig(com.shilapi.xcertplay.airplay.CarPlayClusterDisplay.Content.MAP)
        assertEquals(720,config.widthPixels);assertEquals(720,config.heightPixels)
        val presentation=ClusterMapPresentation(context,panel) {}
        try {
            presentation.show()
            val attrs=presentation.window!!.attributes
            assertEquals(720,attrs.width);assertEquals(720,attrs.height)
            assertEquals(Gravity.TOP or Gravity.RIGHT,attrs.gravity)
            assertTrue(attrs.flags and WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE != 0)
            assertTrue(attrs.flags and WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE != 0)
        } finally { presentation.dismiss() }
    }
}
