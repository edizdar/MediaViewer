package com.example.mediaviewer.data

import android.content.Context
import com.example.mediaviewer.model.MediaItem
import com.example.mediaviewer.model.MediaType
import org.json.JSONArray
import org.json.JSONObject

data class SavedStream(
    val id: String,
    val name: String,
    val url: String,
    val type: String = "AUTO", // RTSP, HLS, HTTP, IPTV
    val bufferMode: String = "BALANCED", // LOW_LATENCY, BALANCED, HIGH_BUFFER
    val dateAdded: Long = System.currentTimeMillis()
) {
    fun toMediaItem(): MediaItem {
        return MediaItem(
            id = id.hashCode().toLong(),
            uriString = url,
            name = name,
            mimeType = when {
                url.startsWith("rtsp://", ignoreCase = true) -> "video/rtsp"
                url.contains(".m3u8", ignoreCase = true) || url.contains(".m3u", ignoreCase = true) -> "application/x-mpegurl"
                else -> "video/mp4"
            },
            mediaType = MediaType.VIDEO,
            path = url
        )
    }
}

object StreamManager {
    private const val PREFS_NAME = "media_viewer_streams"
    private const val KEY_SAVED_STREAMS = "saved_network_streams"
    private const val KEY_BUFFER_MODE = "stream_buffer_mode"

    fun getBufferMode(context: Context): String {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_BUFFER_MODE, "BALANCED") ?: "BALANCED"
    }

    fun setBufferMode(context: Context, mode: String) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_BUFFER_MODE, mode).apply()
    }

    fun getSavedStreams(context: Context): List<SavedStream> {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val jsonStr = prefs.getString(KEY_SAVED_STREAMS, null)
        val list = mutableListOf<SavedStream>()

        if (!jsonStr.isNullOrEmpty()) {
            try {
                val array = JSONArray(jsonStr)
                for (i in 0 until array.length()) {
                    val obj = array.getJSONObject(i)
                    list.add(
                        SavedStream(
                            id = obj.optString("id", System.currentTimeMillis().toString()),
                            name = obj.optString("name", "Akış"),
                            url = obj.optString("url", ""),
                            type = obj.optString("type", "AUTO"),
                            bufferMode = obj.optString("bufferMode", "BALANCED"),
                            dateAdded = obj.optLong("dateAdded", System.currentTimeMillis())
                        )
                    )
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }

        // If empty, add default sample streams for immediate testing
        if (list.isEmpty()) {
            list.addAll(getSampleStreams())
            saveAllStreams(context, list)
        }

        return list
    }

    fun saveStream(context: Context, name: String, url: String, type: String = "AUTO", bufferMode: String = "BALANCED"): SavedStream {
        val current = getSavedStreams(context).toMutableList()
        val newStream = SavedStream(
            id = System.currentTimeMillis().toString(),
            name = name.ifBlank { inferStreamName(url) },
            url = url.trim(),
            type = if (type == "AUTO") inferStreamType(url) else type,
            bufferMode = bufferMode
        )
        // Avoid duplicate URLs
        current.removeAll { it.url.equals(url.trim(), ignoreCase = true) }
        current.add(0, newStream)
        saveAllStreams(context, current)
        return newStream
    }

    fun deleteStream(context: Context, id: String) {
        val current = getSavedStreams(context).toMutableList()
        current.removeAll { it.id == id }
        saveAllStreams(context, current)
    }

    private fun saveAllStreams(context: Context, list: List<SavedStream>) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val array = JSONArray()
        for (stream in list) {
            val obj = JSONObject().apply {
                put("id", stream.id)
                put("name", stream.name)
                put("url", stream.url)
                put("type", stream.type)
                put("bufferMode", stream.bufferMode)
                put("dateAdded", stream.dateAdded)
            }
            array.put(obj)
        }
        prefs.edit().putString(KEY_SAVED_STREAMS, array.toString()).apply()
    }

    fun inferStreamType(url: String): String {
        return when {
            url.startsWith("rtsp://", ignoreCase = true) -> "RTSP"
            url.contains(".m3u8", ignoreCase = true) -> "HLS (M3U8)"
            url.contains(".m3u", ignoreCase = true) -> "IPTV (M3U)"
            url.contains(".mpd", ignoreCase = true) -> "DASH"
            else -> "HTTP Canlı"
        }
    }

    fun inferStreamName(url: String): String {
        return when {
            url.startsWith("rtsp://", ignoreCase = true) -> "RTSP Kamera Yayını"
            url.contains(".m3u8", ignoreCase = true) -> "HLS Canlı Yayın"
            url.contains(".m3u", ignoreCase = true) -> "IPTV Kanal Listesi"
            else -> {
                val clean = url.substringAfterLast("/").substringBefore("?")
                if (clean.isNotBlank()) clean else "Canlı Akış"
            }
        }
    }

    fun getSampleStreams(): List<SavedStream> {
        return listOf(
            SavedStream(
                id = "sample_hls_bbb",
                name = "🎬 Test: Big Buck Bunny (Çoklu Kalite HLS)",
                url = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
                type = "HLS (M3U8)",
                bufferMode = "BALANCED"
            ),
            SavedStream(
                id = "sample_hls_sintel",
                name = "🎬 Test: Sintel Canlı HLS Yayını",
                url = "https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8",
                type = "HLS (M3U8)",
                bufferMode = "BALANCED"
            ),
            SavedStream(
                id = "sample_rtsp_wowza",
                name = "🎥 Test: Wowza RTSP Demo (Big Buck Bunny)",
                url = "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4",
                type = "RTSP",
                bufferMode = "LOW_LATENCY"
            ),
            SavedStream(
                id = "sample_rtsp_demo",
                name = "🎥 Test: RTSP Kamera Yayını (Pattern)",
                url = "rtsp://rtsp.stream/pattern",
                type = "RTSP",
                bufferMode = "LOW_LATENCY"
            )
        )
    }
}
