package com.example.mediaviewer.util

import android.content.ContentValues
import android.content.Context
import android.media.MediaCodec
import android.media.MediaExtractor
import android.media.MediaFormat
import android.media.MediaMuxer
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileInputStream
import java.nio.ByteBuffer

object VideoTrimmer {

    suspend fun trimVideo(
        context: Context,
        inputUri: Uri,
        startMs: Long,
        endMs: Long,
        originalName: String
    ): Uri? = withContext(Dispatchers.IO) {
        val baseName = originalName.substringBeforeLast('.')
        val outputName = "${baseName}_trim_${System.currentTimeMillis()}.mp4"

        val tempFile = File(context.cacheDir, outputName)

        val extractor = MediaExtractor()
        var muxer: MediaMuxer? = null

        try {
            extractor.setDataSource(context, inputUri, null)
            val trackCount = extractor.trackCount
            muxer = MediaMuxer(tempFile.absolutePath, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)

            val trackMap = mutableMapOf<Int, Int>()
            for (i in 0 until trackCount) {
                val format = extractor.getTrackFormat(i)
                val mime = format.getString(MediaFormat.KEY_MIME) ?: ""
                if (mime.startsWith("video/") || mime.startsWith("audio/")) {
                    extractor.selectTrack(i)
                    val muxerTrack = muxer.addTrack(format)
                    trackMap[i] = muxerTrack
                }
            }

            muxer.start()

            val startUs = startMs * 1000L
            val endUs = endMs * 1000L

            extractor.seekTo(startUs, MediaExtractor.SEEK_TO_CLOSEST_SYNC)

            val bufferSize = 2 * 1024 * 1024 // 2MB buffer
            val buffer = ByteBuffer.allocate(bufferSize)
            val bufferInfo = MediaCodec.BufferInfo()

            while (true) {
                val trackIndex = extractor.sampleTrackIndex
                if (trackIndex < 0) break

                val sampleTime = extractor.sampleTime
                if (sampleTime > endUs) break

                bufferInfo.offset = 0
                bufferInfo.size = extractor.readSampleData(buffer, 0)
                if (bufferInfo.size < 0) break

                bufferInfo.presentationTimeUs = (sampleTime - startUs).coerceAtLeast(0L)
                bufferInfo.flags = extractor.sampleFlags

                val muxerTrack = trackMap[trackIndex]
                if (muxerTrack != null && sampleTime >= startUs) {
                    muxer.writeSampleData(muxerTrack, buffer, bufferInfo)
                }

                extractor.advance()
            }

            muxer.stop()
            muxer.release()
            muxer = null
            extractor.release()

            // Save to Public Movies/MediaViewer folder
            return@withContext saveVideoToPublicStorage(context, tempFile, outputName)
        } catch (e: Exception) {
            e.printStackTrace()
            try {
                muxer?.stop()
                muxer?.release()
            } catch (_: Exception) {}
            try {
                extractor.release()
            } catch (_: Exception) {}
            if (tempFile.exists()) tempFile.delete()
            null
        }
    }

    private fun saveVideoToPublicStorage(context: Context, tempFile: File, fileName: String): Uri? {
        if (!tempFile.exists()) return null

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val contentValues = ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, fileName)
                put(MediaStore.MediaColumns.MIME_TYPE, "video/mp4")
                put(MediaStore.MediaColumns.RELATIVE_PATH, "${Environment.DIRECTORY_MOVIES}/MediaViewer")
                put(MediaStore.MediaColumns.IS_PENDING, 1)
            }

            val uri = context.contentResolver.insert(MediaStore.Video.Media.EXTERNAL_CONTENT_URI, contentValues)
            if (uri != null) {
                context.contentResolver.openOutputStream(uri)?.use { out ->
                    FileInputStream(tempFile).use { input ->
                        input.copyTo(out)
                    }
                }
                contentValues.clear()
                contentValues.put(MediaStore.MediaColumns.IS_PENDING, 0)
                context.contentResolver.update(uri, contentValues, null, null)
                tempFile.delete()
                return uri
            }
        } else {
            val dir = File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_MOVIES), "MediaViewer")
            if (!dir.exists()) dir.mkdirs()
            val dest = File(dir, fileName)
            tempFile.copyTo(dest, overwrite = true)
            tempFile.delete()
            return Uri.fromFile(dest)
        }
        return null
    }
}
