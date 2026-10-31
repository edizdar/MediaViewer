package com.example.mediaviewer

import com.example.mediaviewer.model.MediaItem
import com.example.mediaviewer.model.MediaType
import junit.framework.TestCase.assertEquals
import org.junit.Test

class MediaItemTest {

    @Test
    fun testFormattedSize() {
        val itemBytes = MediaItem(1, "file://test.jpg", "test.jpg", "image/jpeg", MediaType.IMAGE, size = 500)
        assertEquals("500 B", itemBytes.formattedSize)

        val itemKb = MediaItem(2, "file://test.jpg", "test.jpg", "image/jpeg", MediaType.IMAGE, size = 2048)
        assertEquals("2.0 KB", itemKb.formattedSize)

        val itemMb = MediaItem(3, "file://test.mp4", "test.mp4", "video/mp4", MediaType.VIDEO, size = 15 * 1024 * 1024)
        assertEquals("15.0 MB", itemMb.formattedSize)
    }

    @Test
    fun testFormattedDuration() {
        val itemShort = MediaItem(1, "file://test.mp4", "test.mp4", "video/mp4", MediaType.VIDEO, durationMs = 65000)
        assertEquals("01:05", itemShort.formattedDuration)

        val itemLong = MediaItem(2, "file://test.mp4", "test.mp4", "video/mp4", MediaType.VIDEO, durationMs = 3665000)
        assertEquals("1:01:05", itemLong.formattedDuration)
    }

    @Test
    fun testResolutionText() {
        val item = MediaItem(1, "file://test.jpg", "test.jpg", "image/jpeg", MediaType.IMAGE, width = 1920, height = 1080)
        assertEquals("1920x1080", item.resolutionText)
    }
}
