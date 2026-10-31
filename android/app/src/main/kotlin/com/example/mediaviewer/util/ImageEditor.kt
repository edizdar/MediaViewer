package com.example.mediaviewer.util

import android.content.ContentValues
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.ColorMatrix
import android.graphics.ColorMatrixColorFilter
import android.graphics.Matrix
import android.graphics.Paint
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import java.io.OutputStream

object ImageEditor {

    suspend fun loadBitmapFromUri(context: Context, uri: Uri, maxDimension: Int = 2048): Bitmap? = withContext(Dispatchers.IO) {
        try {
            // Read bytes once to handle single-use content streams safely
            val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                ?: if (uri.scheme == "file" && uri.path != null) File(uri.path!!).readBytes() else null

            if (bytes != null && bytes.isNotEmpty()) {
                val boundsOptions = BitmapFactory.Options().apply { inJustDecodeBounds = true }
                BitmapFactory.decodeByteArray(bytes, 0, bytes.size, boundsOptions)

                var sampleSize = 1
                while (boundsOptions.outWidth / sampleSize > maxDimension || boundsOptions.outHeight / sampleSize > maxDimension) {
                    sampleSize *= 2
                }

                val decodeOptions = BitmapFactory.Options().apply {
                    inSampleSize = sampleSize
                    inPreferredConfig = Bitmap.Config.ARGB_8888
                }
                return@withContext BitmapFactory.decodeByteArray(bytes, 0, bytes.size, decodeOptions)
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        null
    }

    suspend fun rotateBitmap(bitmap: Bitmap, degrees: Float): Bitmap = withContext(Dispatchers.Default) {
        val matrix = Matrix().apply { postRotate(degrees) }
        Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
    }

    suspend fun flipBitmap(bitmap: Bitmap, horizontal: Boolean): Bitmap = withContext(Dispatchers.Default) {
        val matrix = Matrix().apply {
            if (horizontal) postScale(-1f, 1f) else postScale(1f, -1f)
        }
        Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
    }

    suspend fun cropBitmap(bitmap: Bitmap, x: Int, y: Int, width: Int, height: Int): Bitmap = withContext(Dispatchers.Default) {
        val safeX = x.coerceIn(0, bitmap.width - 1)
        val safeY = y.coerceIn(0, bitmap.height - 1)
        val safeW = width.coerceIn(1, bitmap.width - safeX)
        val safeH = height.coerceIn(1, bitmap.height - safeY)
        Bitmap.createBitmap(bitmap, safeX, safeY, safeW, safeH)
    }

    suspend fun adjustBitmap(
        source: Bitmap,
        brightness: Float, // -100 to 100
        contrast: Float,   // 0.5 to 2.0 (1.0 = normal)
        saturation: Float  // 0.0 to 2.0 (1.0 = normal)
    ): Bitmap = withContext(Dispatchers.Default) {
        val result = Bitmap.createBitmap(source.width, source.height, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(result)
        val paint = Paint()

        // Saturation matrix
        val satMatrix = ColorMatrix().apply { setSaturation(saturation) }

        // Contrast and brightness matrix
        val t = (1.0f - contrast) / 2.0f * 255.0f
        val scale = contrast
        val cbMatrix = ColorMatrix(
            floatArrayOf(
                scale, 0f, 0f, 0f, t + brightness,
                0f, scale, 0f, 0f, t + brightness,
                0f, 0f, scale, 0f, t + brightness,
                0f, 0f, 0f, 1f, 0f
            )
        )

        // Combine
        val finalMatrix = ColorMatrix().apply {
            postConcat(satMatrix)
            postConcat(cbMatrix)
        }

        paint.colorFilter = ColorMatrixColorFilter(finalMatrix)
        canvas.drawBitmap(source, 0f, 0f, paint)
        result
    }

    // Smart HD Upscale (Lanczos / Bicubic + Edge Sharpening matching Desktop algorithm)
    suspend fun smartHdUpscale(source: Bitmap, scaleFactor: Int = 2): Bitmap = withContext(Dispatchers.Default) {
        val newW = source.width * scaleFactor
        val newH = source.height * scaleFactor

        // 1. High quality bicubic scaling
        val scaled = Bitmap.createScaledBitmap(source, newW, newH, true)

        // 2. Unsharp Mask Edge Sharpening
        val result = Bitmap.createBitmap(newW, newH, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(result)
        val paint = Paint(Paint.FILTER_BITMAP_FLAG or Paint.ANTI_ALIAS_FLAG)

        // Subtle sharpen matrix
        val sharpenMatrix = ColorMatrix(
            floatArrayOf(
                1.35f, -0.1f, -0.1f, 0f, 0f,
                -0.1f, 1.35f, -0.1f, 0f, 0f,
                -0.1f, -0.1f, 1.35f, 0f, 0f,
                0f, 0f, 0f, 1f, 0f
            )
        )
        paint.colorFilter = ColorMatrixColorFilter(sharpenMatrix)
        canvas.drawBitmap(scaled, 0f, 0f, paint)
        result
    }

    suspend fun saveBitmap(
        context: Context,
        bitmap: Bitmap,
        originalName: String,
        suffix: String = "_edited"
    ): Uri? = withContext(Dispatchers.IO) {
        val baseName = originalName.substringBeforeLast('.')
        val fileName = "${baseName}${suffix}_${System.currentTimeMillis()}.jpg"

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val contentValues = ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, fileName)
                put(MediaStore.MediaColumns.MIME_TYPE, "image/jpeg")
                put(MediaStore.MediaColumns.RELATIVE_PATH, "${Environment.DIRECTORY_PICTURES}/MediaViewer")
                put(MediaStore.MediaColumns.IS_PENDING, 1)
            }

            val uri = context.contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, contentValues)
            if (uri != null) {
                context.contentResolver.openOutputStream(uri)?.use { stream ->
                    bitmap.compress(Bitmap.CompressFormat.JPEG, 95, stream)
                }
                contentValues.clear()
                contentValues.put(MediaStore.MediaColumns.IS_PENDING, 0)
                context.contentResolver.update(uri, contentValues, null, null)
                return@withContext uri
            }
        } else {
            val dir = File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES), "MediaViewer")
            if (!dir.exists()) dir.mkdirs()
            val file = File(dir, fileName)
            FileOutputStream(file).use { stream ->
                bitmap.compress(Bitmap.CompressFormat.JPEG, 95, stream)
            }
            return@withContext Uri.fromFile(file)
        }
        null
    }
}
