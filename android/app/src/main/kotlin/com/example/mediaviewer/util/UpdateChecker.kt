package com.example.mediaviewer.util

import android.content.Context
import android.content.Intent
import android.net.Uri
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

data class AppUpdateInfo(
    val tagName: String,
    val releaseName: String,
    val changelog: String,
    val downloadUrl: String,
    val isNewer: Boolean,
    val currentVersion: String
)

object UpdateChecker {
    private const val REPO_API = "https://api.github.com/repos/edizdar/MediaViewer/releases/latest"
    private const val FALLBACK_RELEASE_PAGE = "https://github.com/edizdar/MediaViewer/releases"

    suspend fun checkForUpdates(currentVersion: String): AppUpdateInfo? = withContext(Dispatchers.IO) {
        try {
            val url = URL(REPO_API)
            val conn = (url.openConnection() as HttpURLConnection).apply {
                connectTimeout = 5000
                readTimeout = 5000
                setRequestProperty("User-Agent", "MediaViewer-Android-App")
                setRequestProperty("Accept", "application/vnd.github.v3+json")
            }

            if (conn.responseCode != 200) {
                return@withContext null
            }

            val jsonStr = conn.inputStream.bufferedReader().use { it.readText() }
            val json = JSONObject(jsonStr)

            val tagName = json.optString("tag_name", "")
            val name = json.optString("name", tagName)
            val body = json.optString("body", "")
            val htmlUrl = json.optString("html_url", FALLBACK_RELEASE_PAGE)

            var downloadUrl = htmlUrl
            val assets = json.optJSONArray("assets")
            if (assets != null) {
                for (i in 0 until assets.length()) {
                    val asset = assets.getJSONObject(i)
                    val assetName = asset.optString("name", "")
                    if (assetName.endsWith(".apk", ignoreCase = true)) {
                        downloadUrl = asset.optString("browser_download_url", htmlUrl)
                        break
                    }
                }
            }

            val isNewer = compareVersions(tagName, currentVersion) > 0

            AppUpdateInfo(
                tagName = tagName,
                releaseName = name,
                changelog = body,
                downloadUrl = downloadUrl,
                isNewer = isNewer,
                currentVersion = currentVersion
            )
        } catch (_: Exception) {
            null
        }
    }

    fun openDownloadUrl(context: Context, url: String) {
        try {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url)).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(intent)
        } catch (_: Exception) {}
    }

    fun compareVersions(v1: String, v2: String): Int {
        val parts1 = v1.removePrefix("v").removePrefix("V").split(".").mapNotNull { it.filter { c -> c.isDigit() }.toIntOrNull() }
        val parts2 = v2.removePrefix("v").removePrefix("V").split(".").mapNotNull { it.filter { c -> c.isDigit() }.toIntOrNull() }
        val maxLen = maxOf(parts1.size, parts2.size)
        for (i in 0 until maxLen) {
            val p1 = parts1.getOrElse(i) { 0 }
            val p2 = parts2.getOrElse(i) { 0 }
            if (p1 != p2) return p1.compareTo(p2)
        }
        return 0
    }
}
