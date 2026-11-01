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

    /**
     * Resolves the canonical MediaStore content URI (with numeric _ID) for a given MediaItem,
     * regardless of whether it came from a direct query, SAF Document URI, file:// URI, or file path.
     */
    fun findCanonicalMediaStoreUri(context: Context, item: MediaItem): Uri? {
        val uri = item.uri

        // 1. If it's already a MediaStore URI with a valid numeric ID at the end
        if (uri.authority == MediaStore.AUTHORITY) {
            try {
                val id = ContentUris.parseId(uri)
                if (id > 0) return uri
            } catch (_: Exception) {}
        }

        // 2. If it's a MediaStore Documents URI (com.android.providers.media.documents)
        // e.g. content://com.android.providers.media.documents/document/image%3A12345
        if (DocumentsContract.isDocumentUri(context, uri) || uri.authority == "com.android.providers.media.documents") {
            try {
                val docId = DocumentsContract.getDocumentId(uri)
                val parts = docId.split(":")
                if (parts.size >= 2) {
                    val type = parts[0].lowercase()
                    val id = parts[1].toLongOrNull()
                    if (id != null && id > 0) {
                        val baseUri = when (type) {
                            "image" -> MediaStore.Images.Media.EXTERNAL_CONTENT_URI
                            "video" -> MediaStore.Video.Media.EXTERNAL_CONTENT_URI
                            "audio" -> MediaStore.Audio.Media.EXTERNAL_CONTENT_URI
                            else -> MediaStore.Files.getContentUri("external")
                        }
                        return ContentUris.withAppendedId(baseUri, id)
                    }
                }
            } catch (_: Exception) {}
        }

        // 3. If item has a valid numeric MediaStore ID (< 1 trillion to exclude System.currentTimeMillis() fallback IDs)
        if (item.id > 0 && item.id < 1_000_000_000_000L) {
            val baseUri = when (item.mediaType) {
                MediaType.IMAGE -> MediaStore.Images.Media.EXTERNAL_CONTENT_URI
                MediaType.VIDEO -> MediaStore.Video.Media.EXTERNAL_CONTENT_URI
                MediaType.AUDIO -> MediaStore.Audio.Media.EXTERNAL_CONTENT_URI
            }
            return ContentUris.withAppendedId(baseUri, item.id)
        }

        // 4. Query MediaStore by absolute file path
        val path = item.path ?: if (uri.scheme == "file") uri.path else null
        if (!path.isNullOrEmpty()) {
            try {
                val baseUri = when (item.mediaType) {
                    MediaType.IMAGE -> MediaStore.Images.Media.EXTERNAL_CONTENT_URI
                    MediaType.VIDEO -> MediaStore.Video.Media.EXTERNAL_CONTENT_URI
                    MediaType.AUDIO -> MediaStore.Audio.Media.EXTERNAL_CONTENT_URI
                }
                context.contentResolver.query(
                    baseUri,
                    arrayOf(MediaStore.MediaColumns._ID),
                    "${MediaStore.MediaColumns.DATA} = ?",
                    arrayOf(path),
                    null
                )?.use { cursor ->
                    if (cursor.moveToFirst()) {
                        val id = cursor.getLong(cursor.getColumnIndexOrThrow(MediaStore.MediaColumns._ID))
                        if (id > 0) return ContentUris.withAppendedId(baseUri, id)
                    }
                }

                // Also query generic Files table
                context.contentResolver.query(
                    MediaStore.Files.getContentUri("external"),
                    arrayOf(MediaStore.Files.FileColumns._ID),
                    "${MediaStore.Files.FileColumns.DATA} = ?",
                    arrayOf(path),
                    null
                )?.use { cursor ->
                    if (cursor.moveToFirst()) {
                        val id = cursor.getLong(cursor.getColumnIndexOrThrow(MediaStore.Files.FileColumns._ID))
                        if (id > 0) return ContentUris.withAppendedId(MediaStore.Files.getContentUri("external"), id)
                    }
                }
            } catch (_: Exception) {}
        }

        // 5. Query MediaStore by Display Name and Size
        if (item.name.isNotEmpty()) {
            try {
                val baseUri = when (item.mediaType) {
                    MediaType.IMAGE -> MediaStore.Images.Media.EXTERNAL_CONTENT_URI
                    MediaType.VIDEO -> MediaStore.Video.Media.EXTERNAL_CONTENT_URI
                    MediaType.AUDIO -> MediaStore.Audio.Media.EXTERNAL_CONTENT_URI
                }
                val selection = if (item.size > 0) {
                    "${MediaStore.MediaColumns.DISPLAY_NAME} = ? AND ${MediaStore.MediaColumns.SIZE} = ?"
                } else {
                    "${MediaStore.MediaColumns.DISPLAY_NAME} = ?"
                }
                val selectionArgs = if (item.size > 0) {
                    arrayOf(item.name, item.size.toString())
                } else {
                    arrayOf(item.name)
                }
                context.contentResolver.query(
                    baseUri,
                    arrayOf(MediaStore.MediaColumns._ID),
                    selection,
                    selectionArgs,
                    null
                )?.use { cursor ->
                    if (cursor.moveToFirst()) {
                        val id = cursor.getLong(cursor.getColumnIndexOrThrow(MediaStore.MediaColumns._ID))
                        if (id > 0) return ContentUris.withAppendedId(baseUri, id)
                    }
                }
            } catch (_: Exception) {}
        }

        return null
    }

    suspend fun deleteItem(context: Context, item: MediaItem): DeleteRequestResult = withContext(Dispatchers.IO) {
        // Step 1: Direct File deletion if URI is file:// or path exists in writable app storage
        val directPath = if (item.uri.scheme == "file") item.uri.path else item.path
        if (!directPath.isNullOrEmpty()) {
            try {
                val f = File(directPath)
                if (f.exists() && f.delete()) {
                    // File successfully deleted, clean up MediaStore index if any
                    findCanonicalMediaStoreUri(context, item)?.let { msUri ->
                        try {
                            context.contentResolver.delete(msUri, null, null)
                        } catch (_: Exception) {}
                    }
                    return@withContext DeleteRequestResult.Success
                }
            } catch (_: Exception) {}
        }

        // Step 2: Resolve canonical MediaStore content URI
        val canonicalUri = findCanonicalMediaStoreUri(context, item)
        val targetUri = canonicalUri ?: item.uri

        // Step 3: Android 11+ (API 30+) MediaStore Scoped Storage with createDeleteRequest
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R && targetUri.authority == MediaStore.AUTHORITY) {
            // Try direct delete first (succeeds without prompt if file was created by this app)
            try {
                val rows = context.contentResolver.delete(targetUri, null, null)
                if (rows > 0) return@withContext DeleteRequestResult.Success
            } catch (_: SecurityException) {
                // Expected for files owned by other apps; proceed to createDeleteRequest
            } catch (_: Exception) {}

            try {
                val pi = MediaStore.createDeleteRequest(context.contentResolver, listOf(targetUri))
                return@withContext DeleteRequestResult.NeedsUserConsent(pi.intentSender)
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }

        // Step 4: Android 10 (API 29) RecoverableSecurityException
        if (Build.VERSION.SDK_INT == Build.VERSION_CODES.Q && targetUri.authority == MediaStore.AUTHORITY) {
            try {
                val rows = context.contentResolver.delete(targetUri, null, null)
                if (rows > 0) return@withContext DeleteRequestResult.Success
            } catch (e: RecoverableSecurityException) {
                return@withContext DeleteRequestResult.NeedsUserConsent(e.userAction.actionIntent.intentSender)
            } catch (_: Exception) {}
        }

        // Step 5: Direct delete on targetUri (Android <= 28 or granted WRITE_EXTERNAL_STORAGE)
        try {
            val rows = context.contentResolver.delete(targetUri, null, null)
            if (rows > 0) return@withContext DeleteRequestResult.Success
        } catch (_: Exception) {}

        // Step 6: DocumentsContract for SAF document URIs
        if (DocumentsContract.isDocumentUri(context, item.uri)) {
            try {
                if (DocumentsContract.deleteDocument(context.contentResolver, item.uri)) {
                    return@withContext DeleteRequestResult.Success
                }
            } catch (_: Exception) {}
        }

        // Step 7: Fallback direct delete on item.uri if different from targetUri
        if (item.uri != targetUri) {
            try {
                val rows = context.contentResolver.delete(item.uri, null, null)
                if (rows > 0) return@withContext DeleteRequestResult.Success
            } catch (_: Exception) {}
        }

        // Step 8: Physical file deletion if path exists
        item.path?.let { p ->
            try {
                val f = File(p)
                if (f.exists() && f.delete()) {
                    return@withContext DeleteRequestResult.Success
                }
            } catch (_: Exception) {}
        }

        DeleteRequestResult.Failed
    }

    suspend fun directDelete(context: Context, item: MediaItem): Boolean = withContext(Dispatchers.IO) {
        val canonicalUri = findCanonicalMediaStoreUri(context, item) ?: item.uri
        try {
            val rows = context.contentResolver.delete(canonicalUri, null, null)
            if (rows > 0) return@withContext true
        } catch (e: Exception) {
            e.printStackTrace()
        }

        if (canonicalUri != item.uri) {
            try {
                val rows = context.contentResolver.delete(item.uri, null, null)
                if (rows > 0) return@withContext true
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }

        val directPath = if (item.uri.scheme == "file") item.uri.path else item.path
        if (!directPath.isNullOrEmpty()) {
            val f = File(directPath)
            if (f.exists() && f.delete()) return@withContext true
            if (!f.exists()) return@withContext true
        }

        false
    }
}
