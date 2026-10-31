package com.example.mediaviewer.data

import android.app.RecoverableSecurityException
import android.content.ContentUris
import android.content.Context
import android.content.IntentSender
import android.media.MediaMetadataRetriever
import android.net.Uri
import android.os.Build
import android.provider.DocumentsContract
import android.provider.MediaStore
import android.provider.OpenableColumns
import android.webkit.MimeTypeMap
import com.example.mediaviewer.model.MediaItem
import com.example.mediaviewer.model.MediaType
import com.example.mediaviewer.model.MediaTypeFilter
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

sealed class DeleteRequestResult {
    object Success : DeleteRequestResult()
    object Failed : DeleteRequestResult()
    data class NeedsUserConsent(val intentSender: IntentSender) : DeleteRequestResult()
}

class MediaRepository {

    suspend fun queryAllMedia(context: Context, filter: MediaTypeFilter): List<MediaItem> = withContext(Dispatchers.IO) {
        val items = mutableListOf<MediaItem>()

        if (filter == MediaTypeFilter.ALL || filter == MediaTypeFilter.PHOTOS) {
            items.addAll(queryImages(context))
        }
        if (filter == MediaTypeFilter.ALL || filter == MediaTypeFilter.VIDEOS) {
            items.addAll(queryVideos(context))
        }
        if (filter == MediaTypeFilter.ALL || filter == MediaTypeFilter.AUDIO) {
            items.addAll(queryAudio(context))
        }

        // Sort descending by modified date
        items.sortByDescending { it.dateModified }
        items
    }

    private fun queryImages(context: Context): List<MediaItem> {
        val result = mutableListOf<MediaItem>()
        val projection = arrayOf(
            MediaStore.Images.Media._ID,
            MediaStore.Images.Media.DISPLAY_NAME,
            MediaStore.Images.Media.MIME_TYPE,
            MediaStore.Images.Media.SIZE,
            MediaStore.Images.Media.DATE_MODIFIED,
            MediaStore.Images.Media.WIDTH,
            MediaStore.Images.Media.HEIGHT,
            MediaStore.Images.Media.DATA
        )

        try {
            context.contentResolver.query(
                MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
                projection,
                null,
                null,
                "${MediaStore.Images.Media.DATE_MODIFIED} DESC"
            )?.use { cursor ->
                val idCol = cursor.getColumnIndexOrThrow(MediaStore.Images.Media._ID)
                val nameCol = cursor.getColumnIndexOrThrow(MediaStore.Images.Media.DISPLAY_NAME)
                val mimeCol = cursor.getColumnIndexOrThrow(MediaStore.Images.Media.MIME_TYPE)
                val sizeCol = cursor.getColumnIndexOrThrow(MediaStore.Images.Media.SIZE)
                val dateCol = cursor.getColumnIndexOrThrow(MediaStore.Images.Media.DATE_MODIFIED)
                val widthCol = cursor.getColumnIndex(MediaStore.Images.Media.WIDTH)
                val heightCol = cursor.getColumnIndex(MediaStore.Images.Media.HEIGHT)
                val dataCol = cursor.getColumnIndex(MediaStore.Images.Media.DATA)

                while (cursor.moveToNext()) {
                    val id = cursor.getLong(idCol)
                    val contentUri = ContentUris.withAppendedId(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, id)
                    val name = cursor.getString(nameCol) ?: "Fotoğraf_$id"
                    val mime = cursor.getString(mimeCol) ?: "image/jpeg"
                    val size = cursor.getLong(sizeCol)
                    val date = cursor.getLong(dateCol)
                    val width = if (widthCol != -1) cursor.getInt(widthCol) else 0
                    val height = if (heightCol != -1) cursor.getInt(heightCol) else 0
                    val path = if (dataCol != -1) cursor.getString(dataCol) else null

                    result.add(
                        MediaItem(
                            id = id,
                            uriString = contentUri.toString(),
                            name = name,
                            mimeType = mime,
                            mediaType = MediaType.IMAGE,
                            size = size,
                            dateModified = date,
                            width = width,
                            height = height,
                            path = path
                        )
                    )
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return result
    }

    private fun queryVideos(context: Context): List<MediaItem> {
        val result = mutableListOf<MediaItem>()
        val projection = arrayOf(
            MediaStore.Video.Media._ID,
            MediaStore.Video.Media.DISPLAY_NAME,
            MediaStore.Video.Media.MIME_TYPE,
            MediaStore.Video.Media.SIZE,
            MediaStore.Video.Media.DATE_MODIFIED,
            MediaStore.Video.Media.DURATION,
            MediaStore.Video.Media.WIDTH,
            MediaStore.Video.Media.HEIGHT,
            MediaStore.Video.Media.DATA
        )

        try {
            context.contentResolver.query(
                MediaStore.Video.Media.EXTERNAL_CONTENT_URI,
                projection,
                null,
                null,
                "${MediaStore.Video.Media.DATE_MODIFIED} DESC"
            )?.use { cursor ->
                val idCol = cursor.getColumnIndexOrThrow(MediaStore.Video.Media._ID)
                val nameCol = cursor.getColumnIndexOrThrow(MediaStore.Video.Media.DISPLAY_NAME)
                val mimeCol = cursor.getColumnIndexOrThrow(MediaStore.Video.Media.MIME_TYPE)
                val sizeCol = cursor.getColumnIndexOrThrow(MediaStore.Video.Media.SIZE)
                val dateCol = cursor.getColumnIndexOrThrow(MediaStore.Video.Media.DATE_MODIFIED)
                val durationCol = cursor.getColumnIndex(MediaStore.Video.Media.DURATION)
                val widthCol = cursor.getColumnIndex(MediaStore.Video.Media.WIDTH)
                val heightCol = cursor.getColumnIndex(MediaStore.Video.Media.HEIGHT)
                val dataCol = cursor.getColumnIndex(MediaStore.Video.Media.DATA)

                while (cursor.moveToNext()) {
                    val id = cursor.getLong(idCol)
                    val contentUri = ContentUris.withAppendedId(MediaStore.Video.Media.EXTERNAL_CONTENT_URI, id)
                    val name = cursor.getString(nameCol) ?: "Video_$id"
                    val mime = cursor.getString(mimeCol) ?: "video/mp4"
                    val size = cursor.getLong(sizeCol)
                    val date = cursor.getLong(dateCol)
                    val duration = if (durationCol != -1) cursor.getLong(durationCol) else 0L
                    val width = if (widthCol != -1) cursor.getInt(widthCol) else 0
                    val height = if (heightCol != -1) cursor.getInt(heightCol) else 0
                    val path = if (dataCol != -1) cursor.getString(dataCol) else null

                    result.add(
                        MediaItem(
                            id = id,
                            uriString = contentUri.toString(),
                            name = name,
                            mimeType = mime,
                            mediaType = MediaType.VIDEO,
                            size = size,
                            dateModified = date,
                            durationMs = duration,
                            width = width,
                            height = height,
                            path = path
                        )
                    )
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return result
    }

    private fun queryAudio(context: Context): List<MediaItem> {
        val result = mutableListOf<MediaItem>()
        val projection = arrayOf(
            MediaStore.Audio.Media._ID,
            MediaStore.Audio.Media.DISPLAY_NAME,
            MediaStore.Audio.Media.MIME_TYPE,
            MediaStore.Audio.Media.SIZE,
            MediaStore.Audio.Media.DATE_MODIFIED,
            MediaStore.Audio.Media.DURATION,
            MediaStore.Audio.Media.DATA
        )

        try {
            val selection = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                "${MediaStore.Audio.Media.IS_MUSIC} != 0 OR ${MediaStore.Audio.Media.DURATION} > 0"
            } else {
                null
            }

            context.contentResolver.query(
                MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,
                projection,
                selection,
                null,
                "${MediaStore.Audio.Media.DATE_MODIFIED} DESC"
            )?.use { cursor ->
                val idCol = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media._ID)
                val nameCol = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.DISPLAY_NAME)
                val mimeCol = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.MIME_TYPE)
                val sizeCol = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.SIZE)
                val dateCol = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.DATE_MODIFIED)
                val durationCol = cursor.getColumnIndex(MediaStore.Audio.Media.DURATION)
                val dataCol = cursor.getColumnIndex(MediaStore.Audio.Media.DATA)

                while (cursor.moveToNext()) {
                    val id = cursor.getLong(idCol)
                    val contentUri = ContentUris.withAppendedId(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, id)
                    val name = cursor.getString(nameCol) ?: "Ses_$id"
                    val mime = cursor.getString(mimeCol) ?: "audio/mpeg"
                    val size = cursor.getLong(sizeCol)
                    val date = cursor.getLong(dateCol)
                    val duration = if (durationCol != -1) cursor.getLong(durationCol) else 0L
                    val path = if (dataCol != -1) cursor.getString(dataCol) else null

                    result.add(
                        MediaItem(
                            id = id,
                            uriString = contentUri.toString(),
                            name = name,
                            mimeType = mime,
                            mediaType = MediaType.AUDIO,
                            size = size,
                            dateModified = date,
                            durationMs = duration,
                            path = path
                        )
                    )
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return result
    }

    suspend fun resolveUri(context: Context, uri: Uri): MediaItem = withContext(Dispatchers.IO) {
        var name = uri.lastPathSegment ?: "Bilinmeyen Dosya"
        var size = 0L
        var mimeType = context.contentResolver.getType(uri)

        // Try querying OpenableColumns for display name and size
        try {
            context.contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                val nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                val sizeIndex = cursor.getColumnIndex(OpenableColumns.SIZE)
                if (cursor.moveToFirst()) {
                    if (nameIndex != -1 && !cursor.isNull(nameIndex)) {
                        name = cursor.getString(nameIndex)
                    }
                    if (sizeIndex != -1 && !cursor.isNull(sizeIndex)) {
                        size = cursor.getLong(sizeIndex)
                    }
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }

        // Infer MIME if not found
        if (mimeType == null) {
            val extension = MimeTypeMap.getFileExtensionFromUrl(name)
            if (!extension.isNullOrEmpty()) {
                mimeType = MimeTypeMap.getSingleton().getMimeTypeFromExtension(extension.lowercase())
            }
        }
        mimeType = mimeType ?: "application/octet-stream"

        val mediaType = when {
            mimeType.startsWith("image/") -> MediaType.IMAGE
            mimeType.startsWith("video/") -> MediaType.VIDEO
            mimeType.startsWith("audio/") -> MediaType.AUDIO
            else -> {
                val ext = name.substringAfterLast('.', "").lowercase()
                when (ext) {
                    "jpg", "jpeg", "png", "webp", "gif", "bmp", "heic", "avif" -> MediaType.IMAGE
                    "mp4", "mkv", "avi", "mov", "3gp", "webm", "flv", "ts", "m4v", "wmv" -> MediaType.VIDEO
                    "mp3", "wav", "flac", "m4a", "aac", "ogg", "wma", "opus" -> MediaType.AUDIO
                    else -> MediaType.IMAGE
                }
            }
        }

        var durationMs = 0L
        var width = 0
        var height = 0

        // Attempt to extract metadata via MediaMetadataRetriever if video or audio
        if (mediaType == MediaType.VIDEO || mediaType == MediaType.AUDIO) {
            try {
                MediaMetadataRetriever().use { retriever ->
                    retriever.setDataSource(context, uri)
                    val durStr = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)
                    if (!durStr.isNullOrEmpty()) {
                        durationMs = durStr.toLongOrNull() ?: 0L
                    }
                    if (mediaType == MediaType.VIDEO) {
                        val wStr = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_WIDTH)
                        val hStr = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_HEIGHT)
                        width = wStr?.toIntOrNull() ?: 0
                        height = hStr?.toIntOrNull() ?: 0
                    }
                }
            } catch (e: Exception) {
                // Ignore if retriever fails on stream
            }
        }

        MediaItem(
            id = System.currentTimeMillis(),
            uriString = uri.toString(),
            name = name,
            mimeType = mimeType,
            mediaType = mediaType,
            size = size,
            dateModified = System.currentTimeMillis() / 1000,
            durationMs = durationMs,
            width = width,
            height = height,
            path = uri.path
        )
    }

    suspend fun getSiblings(context: Context, item: MediaItem): List<MediaItem> = withContext(Dispatchers.IO) {
        val uri = item.uri
        val scheme = uri.scheme
        if (scheme == "content") {
            try {
                // Check if this content URI belongs to MediaStore
                val host = uri.host
                if (host == "media" || uri.toString().contains("media/external")) {
                    var bucketId: String? = null
                    val projection = arrayOf(MediaStore.MediaColumns.BUCKET_ID)
                    context.contentResolver.query(uri, projection, null, null, null)?.use { cursor ->
                        if (cursor.moveToFirst()) {
                            val bucketIndex = cursor.getColumnIndex(MediaStore.MediaColumns.BUCKET_ID)
                            if (bucketIndex != -1) bucketId = cursor.getString(bucketIndex)
                        }
                    }

                    if (!bucketId.isNullOrEmpty()) {
                        val siblings = mutableListOf<MediaItem>()
                        // Query images in bucket
                        queryBucket(context, MediaStore.Images.Media.EXTERNAL_CONTENT_URI, bucketId, MediaType.IMAGE, siblings)
                        // Query videos in bucket
                        queryBucket(context, MediaStore.Video.Media.EXTERNAL_CONTENT_URI, bucketId, MediaType.VIDEO, siblings)
                        if (siblings.isNotEmpty()) {
                            siblings.sortByDescending { it.dateModified }
                            return@withContext siblings
                        }
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
        // Fallback: just return the single item
        listOf(item)
    }

    private fun queryBucket(
        context: Context,
        contentUri: Uri,
        bucketId: String,
        mediaType: MediaType,
        targetList: MutableList<MediaItem>
    ) {
        val projection = arrayOf(
            MediaStore.MediaColumns._ID,
            MediaStore.MediaColumns.DISPLAY_NAME,
            MediaStore.MediaColumns.MIME_TYPE,
            MediaStore.MediaColumns.SIZE,
            MediaStore.MediaColumns.DATE_MODIFIED,
            MediaStore.MediaColumns.WIDTH,
            MediaStore.MediaColumns.HEIGHT
        )
        val selection = "${MediaStore.MediaColumns.BUCKET_ID} = ?"
        val selectionArgs = arrayOf(bucketId)

        try {
            context.contentResolver.query(
                contentUri,
                projection,
                selection,
                selectionArgs,
                "${MediaStore.MediaColumns.DATE_MODIFIED} DESC"
            )?.use { cursor ->
                val idCol = cursor.getColumnIndexOrThrow(MediaStore.MediaColumns._ID)
                val nameCol = cursor.getColumnIndexOrThrow(MediaStore.MediaColumns.DISPLAY_NAME)
                val mimeCol = cursor.getColumnIndexOrThrow(MediaStore.MediaColumns.MIME_TYPE)
                val sizeCol = cursor.getColumnIndexOrThrow(MediaStore.MediaColumns.SIZE)
                val dateCol = cursor.getColumnIndexOrThrow(MediaStore.MediaColumns.DATE_MODIFIED)
                val widthCol = cursor.getColumnIndex(MediaStore.MediaColumns.WIDTH)
                val heightCol = cursor.getColumnIndex(MediaStore.MediaColumns.HEIGHT)

                while (cursor.moveToNext()) {
                    val id = cursor.getLong(idCol)
                    val itemUri = ContentUris.withAppendedId(contentUri, id)
                    val name = cursor.getString(nameCol) ?: "Medya_$id"
                    val mime = cursor.getString(mimeCol) ?: "application/octet-stream"
                    val size = cursor.getLong(sizeCol)
                    val date = cursor.getLong(dateCol)
                    val width = if (widthCol != -1) cursor.getInt(widthCol) else 0
                    val height = if (heightCol != -1) cursor.getInt(heightCol) else 0

                    targetList.add(
                        MediaItem(
                            id = id,
                            uriString = itemUri.toString(),
                            name = name,
                            mimeType = mime,
                            mediaType = mediaType,
                            size = size,
                            dateModified = date,
                            width = width,
                            height = height
                        )
                    )
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    suspend fun deleteItem(context: Context, item: MediaItem): DeleteRequestResult = withContext(Dispatchers.IO) {
        // 1. Direct file check
        if (item.uri.scheme == "file") {
            val path = item.path ?: item.uri.path
            if (path != null) {
                val f = File(path)
                if (f.exists() && f.delete()) {
                    return@withContext DeleteRequestResult.Success
                }
            }
            return@withContext DeleteRequestResult.Failed
        }

        // 2. Android 11+ (API 30+) MediaStore Scoped Storage
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            val isMediaStore = item.uri.authority == MediaStore.AUTHORITY || item.uriString.contains("media")
            if (isMediaStore) {
                try {
                    // Try createDeleteRequest for MediaStore items - this triggers Android's system prompt
                    val pi = MediaStore.createDeleteRequest(context.contentResolver, listOf(item.uri))
                    return@withContext DeleteRequestResult.NeedsUserConsent(pi.intentSender)
                } catch (e: Exception) {
                    e.printStackTrace()
                    // Fallback to direct delete if createDeleteRequest fails
                    try {
                        val rows = context.contentResolver.delete(item.uri, null, null)
                        if (rows > 0) return@withContext DeleteRequestResult.Success
                    } catch (ex: Exception) {
                        ex.printStackTrace()
                    }
                    return@withContext DeleteRequestResult.Failed
                }
            }
        }

        // 3. Android 10 (API 29) RecoverableSecurityException
        if (Build.VERSION.SDK_INT == Build.VERSION_CODES.Q) {
            try {
                val rows = context.contentResolver.delete(item.uri, null, null)
                if (rows > 0) return@withContext DeleteRequestResult.Success
            } catch (e: RecoverableSecurityException) {
                return@withContext DeleteRequestResult.NeedsUserConsent(e.userAction.actionIntent.intentSender)
            } catch (e: Exception) {
                e.printStackTrace()
                return@withContext DeleteRequestResult.Failed
            }
        }

        // 4. Fallback for older Android (API <= 28) or non-MediaStore URIs
        try {
            val rows = context.contentResolver.delete(item.uri, null, null)
            if (rows > 0) return@withContext DeleteRequestResult.Success
        } catch (e: Exception) {
            e.printStackTrace()
        }

        // 5. DocumentsContract if document URI
        if (DocumentsContract.isDocumentUri(context, item.uri)) {
            try {
                if (DocumentsContract.deleteDocument(context.contentResolver, item.uri)) {
                    return@withContext DeleteRequestResult.Success
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }

        // 6. Direct physical file deletion if path exists
        item.path?.let { p ->
            try {
                val f = File(p)
                if (f.exists() && f.delete()) {
                    return@withContext DeleteRequestResult.Success
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }

        DeleteRequestResult.Failed
    }

    suspend fun directDelete(context: Context, item: MediaItem): Boolean = withContext(Dispatchers.IO) {
        try {
            val rows = context.contentResolver.delete(item.uri, null, null)
            rows > 0
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }
}
