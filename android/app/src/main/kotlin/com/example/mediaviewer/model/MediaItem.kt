package com.example.mediaviewer.model

import android.net.Uri
import kotlinx.serialization.Serializable
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Serializable
enum class MediaType {
    IMAGE,
    VIDEO,
    AUDIO
}

@Serializable
data class MediaItem(
    val id: Long,
    val uriString: String,
    val name: String,
    val mimeType: String,
    val mediaType: MediaType,
    val size: Long = 0L,
    val dateModified: Long = 0L,
    val durationMs: Long = 0L,
    val width: Int = 0,
    val height: Int = 0,
    val path: String? = null
) {
    val uri: Uri
        get() = Uri.parse(uriString)

    val formattedSize: String
        get() {
            if (size <= 0) return "Bilinmiyor"
            val kb = size / 1024.0
            val mb = kb / 1024.0
            val gb = mb / 1024.0
            return when {
                gb >= 1.0 -> String.format(Locale.US, "%.2f GB", gb)
                mb >= 1.0 -> String.format(Locale.US, "%.1f MB", mb)
                kb >= 1.0 -> String.format(Locale.US, "%.1f KB", kb)
                else -> "$size B"
            }
        }

    val formattedDuration: String
        get() {
            if (durationMs <= 0) return ""
            val totalSeconds = durationMs / 1000
            val hours = totalSeconds / 3600
            val minutes = (totalSeconds % 3600) / 60
            val seconds = totalSeconds % 60
            return if (hours > 0) {
                String.format(Locale.US, "%d:%02d:%02d", hours, minutes, seconds)
            } else {
                String.format(Locale.US, "%02d:%02d", minutes, seconds)
            }
        }

    val formattedDate: String
        get() {
            if (dateModified <= 0) return "Bilinmiyor"
            // dateModified from MediaStore can be in seconds or milliseconds
            val millis = if (dateModified < 10000000000L) dateModified * 1000 else dateModified
            val sdf = SimpleDateFormat("dd MMM yyyy, HH:mm", Locale("tr", "TR"))
            return sdf.format(Date(millis))
        }

    val resolutionText: String
        get() = if (width > 0 && height > 0) "${width}x${height}" else ""
}

enum class MediaTypeFilter {
    ALL,
    PHOTOS,
    VIDEOS,
    AUDIO
}
