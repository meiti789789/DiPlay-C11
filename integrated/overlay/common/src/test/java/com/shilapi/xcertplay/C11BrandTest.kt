package com.shilapi.xcertplay
import android.graphics.BitmapFactory
import com.shilapi.xcertplay.host.R
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class) @Config(sdk=[28])
class C11BrandTest {
    @Test fun carPlayReturnNameUsesLeapmotorAndBothProtocolIconsAreRealPngs() {
        val context=RuntimeEnvironment.getApplication()
        assertEquals("零跑",AirPlayPersistence.loadOemLabel(context))
        AirPlayPersistence.saveOemLabel(context,"BYD")
        assertEquals("零跑",AirPlayPersistence.loadOemLabel(context))
        AirPlayPersistence.saveOemLabel(context,"My C11")
        assertEquals("My C11",AirPlayPersistence.loadOemLabel(context))
        for (id in listOf(R.raw.ic_car_home,R.raw.placeholder_icon)) {
            val bitmap=BitmapFactory.decodeResource(context.resources,id)
            assertNotNull(bitmap)
            assertEquals(256,bitmap.width);assertEquals(256,bitmap.height)
            bitmap.recycle()
        }
        assertNotNull(context.getDrawable(R.drawable.ic_carplay))
    }
}
