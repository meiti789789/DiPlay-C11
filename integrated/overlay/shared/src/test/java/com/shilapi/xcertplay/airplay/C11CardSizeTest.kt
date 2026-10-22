package com.shilapi.xcertplay.airplay

import org.junit.Assert.*
import org.junit.Test

class C11CardSizeTest {
    @Test fun maximumDoublesBothActualDimensionsWithoutChangingLegacySizes() {
        for ((w, h) in listOf(720 to 720, 600 to 600, 896 to 896, 1920 to 720)) {
            for (size in ClusterTurnCardOverlay.sizePercents) {
                val oldWidth = (w * 29 / 100 * size / 100).coerceAtLeast(150).coerceAtMost(w)
                val oldHeight = (oldWidth / 2.64f).toInt().coerceAtLeast(58).coerceAtMost((h * 59 / 100 * 0.55f).toInt())
                val actual = ClusterTurnCardOverlay.card(w, h, 64, 30, size)
                assertEquals(oldWidth, actual.width)
                assertEquals(oldHeight, actual.height)
            }
            val old = ClusterTurnCardOverlay.card(w, h, 64, 30, 95)
            val enlarged = ClusterTurnCardOverlay.card(w, h, 64, 30, 190)
            assertEquals(old.width * 2, enlarged.width)
            assertEquals(old.height * 2, enlarged.height)
        }
    }
    @Test fun enlargedCardsStayInsideTheInstrumentPaneAtAllPositions() {
        for (size in listOf(100, 145, 190)) for (x in ClusterTurnCardOverlay.xPercents) for (y in ClusterTurnCardOverlay.yPercents) {
            val card = ClusterTurnCardOverlay.card(720, 720, x, y, size)
            assertTrue(card.left >= 0 && card.top >= 0)
            assertTrue(card.left + card.width <= 720 && card.top + card.height <= 720)
        }
    }
}
