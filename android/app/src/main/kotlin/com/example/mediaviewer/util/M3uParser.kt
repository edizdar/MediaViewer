package com.example.mediaviewer.util

import android.content.Context
import android.net.Uri
import com.example.mediaviewer.model.MediaItem
import com.example.mediaviewer.model.MediaType
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.HttpURLConnection
import java.net.URL

object M3uParser {

    data class M3uEntry(
        val title: String,
        val url: String,
        val group: String? = null,
        val logo: String? = null
    ) {
        fun toMediaItem(index: Int): MediaItem {
            val isAudio = url.contains(".mp3", ignoreCase = true) || url.contains(".aac", ignoreCase = true)
            return MediaItem(
                id = (url.hashCode() + index).toLong(),
                uriString = url,
                name = title.ifBlank { "Kanal ${index + 1}" },
                mimeType = when {
                    url.startsWith("rtsp://", ignoreCase = true) -> "video/rtsp"
                    url.contains(".m3u8", ignoreCase = true) -> "application/x-mpegurl"
                    isAudio -> "audio/mpeg"
                    else -> "video/mp4"
                },
                mediaType = if (isAudio) MediaType.AUDIO else MediaType.VIDEO,
                path = url
            )
        }
    }

    /**
     * Determines whether the given text or file is an IPTV multi-channel playlist
     * or a direct HLS segment playlist.
     */
    fun isChannelPlaylist(content: String): Boolean {
        // If it contains multiple EXTINF tags or external URLs, it's a channel list
        val extInfCount = content.lines().count { it.startsWith("#EXTINF", ignoreCase = true) }
        return extInfCount > 1 || (extInfCount == 1 && !content.contains("#EXT-X-TARGETDURATION"))
    }

    suspend fun parseFromUri(context: Context, uri: Uri): List<MediaItem> = withContext(Dispatchers.IO) {
        val lines = mutableListOf<String>()
        try {
            if (uri.scheme == "http" || uri.scheme == "https") {
                val conn = URL(uri.toString()).openConnection() as HttpURLConnection
                conn.connectTimeout = 8000
                conn.readTimeout = 8000
                BufferedReader(InputStreamReader(conn.inputStream)).use { reader ->
                    reader.lineSequence().forEach { lines.add(it) }
                }
            } else {
                context.contentResolver.openInputStream(uri)?.use { stream ->
                    BufferedReader(InputStreamReader(stream)).use { reader ->
                        reader.lineSequence().forEach { lines.add(it) }
                    }
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }

        parseLines(lines)
    }

    fun parseLines(lines: List<String>): List<MediaItem> {
        val entries = mutableListOf<M3uEntry>()
        var pendingTitle: String? = null
        var pendingGroup: String? = null
        var pendingLogo: String? = null

        for (rawLine in lines) {
            val line = rawLine.trim()
            if (line.isEmpty()) continue

            if (line.startsWith("#EXTINF:", ignoreCase = true)) {
                // Parse #EXTINF:-1 tvg-logo="url" group-title="Group",Channel Name
                val commaIndex = line.lastIndexOf(',')
                val title = if (commaIndex != -1 && commaIndex < line.length - 1) {
                    line.substring(commaIndex + 1).trim()
                } else {
                    "Kanal ${entries.size + 1}"
                }
                pendingTitle = title

                // Extract group-title if present
                val groupRegex = "group-title=\"([^\"]+)\"".toRegex(RegexOption.IGNORE_CASE)
                pendingGroup = groupRegex.find(line)?.groupValues?.get(1)

                // Extract tvg-logo if present
                val logoRegex = "tvg-logo=\"([^\"]+)\"".toRegex(RegexOption.IGNORE_CASE)
                pendingLogo = logoRegex.find(line)?.groupValues?.get(1)
            } else if (!line.startsWith("#")) {
                // Stream URL line
                if (line.startsWith("http://", ignoreCase = true) ||
                    line.startsWith("https://", ignoreCase = true) ||
                    line.startsWith("rtsp://", ignoreCase = true) ||
                    line.startsWith("rtmp://", ignoreCase = true)
                ) {
                    val title = pendingTitle ?: "Kanal ${entries.size + 1}"
                    entries.add(
                        M3uEntry(
                            title = title,
                            url = line,
                            group = pendingGroup,
                            logo = pendingLogo
                        )
                    )
                }
                pendingTitle = null
                pendingGroup = null
                pendingLogo = null
            }
        }

        return entries.mapIndexed { idx, entry -> entry.toMediaItem(idx) }
    }
}
