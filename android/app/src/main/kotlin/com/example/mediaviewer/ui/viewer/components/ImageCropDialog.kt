package com.example.mediaviewer.ui.viewer.components

import android.graphics.Bitmap
import android.widget.Toast
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Done
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.ClipOp
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.clipPath
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.example.mediaviewer.model.MediaItem
import com.example.mediaviewer.ui.theme.AccentBlue
import com.example.mediaviewer.ui.theme.ChipSelected
import com.example.mediaviewer.ui.theme.ChipUnselected
import com.example.mediaviewer.ui.theme.DarkBackground
import com.example.mediaviewer.ui.theme.DarkSurface
import com.example.mediaviewer.ui.theme.TextPrimary
import com.example.mediaviewer.ui.theme.TextSecondary
import com.example.mediaviewer.util.ImageEditor
import kotlinx.coroutines.launch

private enum class DragMode {
    NONE,
    MOVE,
    TOP_LEFT,
    TOP_RIGHT,
    BOTTOM_LEFT,
    BOTTOM_RIGHT
}

@Composable
fun ImageCropDialog(
    item: MediaItem,
    onDismiss: () -> Unit,
    onSaved: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    var originalBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var isLoading by remember { mutableStateOf(true) }
    var isSaving by remember { mutableStateOf(false) }

    // Normalized crop rect relative to image (0f..1f)
    var cropLeft by remember { mutableFloatStateOf(0.1f) }
    var cropTop by remember { mutableFloatStateOf(0.1f) }
    var cropRight by remember { mutableFloatStateOf(0.9f) }
    var cropBottom by remember { mutableFloatStateOf(0.9f) }

    var selectedRatioName by remember { mutableStateOf("Serbest") }
    var fixedAspectRatio by remember { mutableStateOf<Float?>(null) } // width / height

    LaunchedEffect(item.uriString) {
        isLoading = true
        originalBitmap = ImageEditor.loadBitmapFromUri(context, item.uri, 2560)
        isLoading = false
    }

    Dialog(
        onDismissRequest = { if (!isSaving) onDismiss() },
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Surface(
            color = DarkBackground,
            modifier = Modifier.fillMaxSize()
        ) {
            Column(modifier = Modifier.fillMaxSize()) {
                // Top Action Bar
                Surface(
                    color = DarkSurface,
                    modifier = Modifier.fillMaxWidth().statusBarsPadding()
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 12.dp, vertical = 8.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        IconButton(
                            onClick = { if (!isSaving) onDismiss() },
                            enabled = !isSaving
                        ) {
                            Icon(Icons.Default.Close, contentDescription = "Kapat", tint = Color.White)
                        }

                        Text(
                            text = "✂️ Fotoğrafı Kırp",
                            style = MaterialTheme.typography.titleMedium.copy(
                                fontWeight = FontWeight.Bold,
                                color = TextPrimary,
                                fontSize = 16.sp
                            )
                        )

                        Button(
                            onClick = {
                                val bmp = originalBitmap ?: return@Button
                                isSaving = true
                                scope.launch {
                                    val pixelX = (cropLeft * bmp.width).toInt().coerceIn(0, bmp.width - 1)
                                    val pixelY = (cropTop * bmp.height).toInt().coerceIn(0, bmp.height - 1)
                                    val pixelW = ((cropRight - cropLeft) * bmp.width).toInt().coerceIn(1, bmp.width - pixelX)
                                    val pixelH = ((cropBottom - cropTop) * bmp.height).toInt().coerceIn(1, bmp.height - pixelY)

                                    val cropped = ImageEditor.cropBitmap(bmp, pixelX, pixelY, pixelW, pixelH)
                                    val savedUri = ImageEditor.saveBitmap(context, cropped, item.name, "_crop")
                                    isSaving = false
                                    if (savedUri != null) {
                                        Toast.makeText(context, "Kırpılan fotoğraf galeriye kaydedildi!", Toast.LENGTH_SHORT).show()
                                        onSaved()
                                        onDismiss()
                                    } else {
                                        Toast.makeText(context, "Kırpılan fotoğraf kaydedilemedi!", Toast.LENGTH_SHORT).show()
                                    }
                                }
                            },
                            enabled = !isSaving && originalBitmap != null,
                            colors = ButtonDefaults.buttonColors(containerColor = AccentBlue),
                            shape = RoundedCornerShape(8.dp)
                        ) {
                            if (isSaving) {
                                CircularProgressIndicator(color = Color.White, modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(6.dp))
                            } else {
                                Icon(Icons.Default.Done, contentDescription = null, modifier = Modifier.size(18.dp))
                                Spacer(modifier = Modifier.width(6.dp))
                            }
                            Text("Kaydet")
                        }
                    }
                }

                // Interactive Crop Area
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxWidth()
                        .background(Color.Black),
                    contentAlignment = Alignment.Center
                ) {
                    if (isLoading) {
                        CircularProgressIndicator(color = AccentBlue)
                    } else if (originalBitmap != null) {
                        val bmp = originalBitmap!!

                        BoxWithConstraints(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(16.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            val containerWidth = constraints.maxWidth.toFloat()
                            val containerHeight = constraints.maxHeight.toFloat()

                            val bmpAspect = bmp.width.toFloat() / bmp.height.toFloat()
                            val containerAspect = containerWidth / containerHeight

                            val displayW: Float
                            val displayH: Float

                            if (bmpAspect > containerAspect) {
                                displayW = containerWidth
                                displayH = containerWidth / bmpAspect
                            } else {
                                displayH = containerHeight
                                displayW = containerHeight * bmpAspect
                            }

                            val offsetX = (containerWidth - displayW) / 2f
                            val offsetY = (containerHeight - displayH) / 2f

                            var activeDragMode by remember { mutableStateOf(DragMode.NONE) }

                            Box(
                                modifier = Modifier
                                    .size(width = (displayW / containerWidth * maxWidth.value).dp, height = (displayH / containerHeight * maxHeight.value).dp)
                                    .pointerInput(displayW, displayH) {
                                        detectDragGestures(
                                            onDragStart = { startPos ->
                                                val cLeft = cropLeft * displayW
                                                val cTop = cropTop * displayH
                                                val cRight = cropRight * displayW
                                                val cBottom = cropBottom * displayH

                                                val hitRadius = 48f

                                                activeDragMode = when {
                                                    // Corners
                                                    Offset(cLeft, cTop).minus(startPos).getDistance() <= hitRadius -> DragMode.TOP_LEFT
                                                    Offset(cRight, cTop).minus(startPos).getDistance() <= hitRadius -> DragMode.TOP_RIGHT
                                                    Offset(cLeft, cBottom).minus(startPos).getDistance() <= hitRadius -> DragMode.BOTTOM_LEFT
                                                    Offset(cRight, cBottom).minus(startPos).getDistance() <= hitRadius -> DragMode.BOTTOM_RIGHT
                                                    // Inside rect -> move
                                                    startPos.x in cLeft..cRight && startPos.y in cTop..cBottom -> DragMode.MOVE
                                                    else -> DragMode.NONE
                                                }
                                            },
                                            onDragEnd = {
                                                activeDragMode = DragMode.NONE
                                            },
                                            onDragCancel = {
                                                activeDragMode = DragMode.NONE
                                            },
                                            onDrag = { change, dragAmount ->
                                                change.consume()
                                                val dxNorm = dragAmount.x / displayW
                                                val dyNorm = dragAmount.y / displayH
                                                val minSizeNorm = 0.1f

                                                when (activeDragMode) {
                                                    DragMode.MOVE -> {
                                                        val w = cropRight - cropLeft
                                                        val h = cropBottom - cropTop
                                                        var newL = (cropLeft + dxNorm).coerceIn(0f, 1f - w)
                                                        var newT = (cropTop + dyNorm).coerceIn(0f, 1f - h)
                                                        cropLeft = newL
                                                        cropRight = newL + w
                                                        cropTop = newT
                                                        cropBottom = newT + h
                                                    }
                                                    DragMode.TOP_LEFT -> {
                                                        cropLeft = (cropLeft + dxNorm).coerceIn(0f, cropRight - minSizeNorm)
                                                        cropTop = (cropTop + dyNorm).coerceIn(0f, cropBottom - minSizeNorm)
                                                    }
                                                    DragMode.TOP_RIGHT -> {
                                                        cropRight = (cropRight + dxNorm).coerceIn(cropLeft + minSizeNorm, 1f)
                                                        cropTop = (cropTop + dyNorm).coerceIn(0f, cropBottom - minSizeNorm)
                                                    }
                                                    DragMode.BOTTOM_LEFT -> {
                                                        cropLeft = (cropLeft + dxNorm).coerceIn(0f, cropRight - minSizeNorm)
                                                        cropBottom = (cropBottom + dyNorm).coerceIn(cropTop + minSizeNorm, 1f)
                                                    }
                                                    DragMode.BOTTOM_RIGHT -> {
                                                        cropRight = (cropRight + dxNorm).coerceIn(cropLeft + minSizeNorm, 1f)
                                                        cropBottom = (cropBottom + dyNorm).coerceIn(cropTop + minSizeNorm, 1f)
                                                    }
                                                    DragMode.NONE -> {}
                                                }
                                            }
                                        )
                                    }
                            ) {
                                // Background Image
                                Image(
                                    bitmap = bmp.asImageBitmap(),
                                    contentDescription = "Fotoğraf",
                                    contentScale = ContentScale.FillBounds,
                                    modifier = Modifier.fillMaxSize()
                                )

                                // Darkened Overlay + White Crop Window + Grid Lines
                                Canvas(modifier = Modifier.fillMaxSize()) {
                                    val cLeft = cropLeft * size.width
                                    val cTop = cropTop * size.height
                                    val cRight = cropRight * size.width
                                    val cBottom = cropBottom * size.height
                                    val cWidth = cRight - cLeft
                                    val cHeight = cBottom - cTop

                                    val cropRect = Rect(cLeft, cTop, cRight, cBottom)

                                    // 1. Darken everything OUTSIDE crop rect
                                    val fullPath = Path().apply { addRect(Rect(0f, 0f, size.width, size.height)) }
                                    val cropPath = Path().apply { addRect(cropRect) }

                                    clipPath(cropPath, clipOp = ClipOp.Difference) {
                                        drawRect(Color.Black.copy(alpha = 0.7f))
                                    }

                                    // 2. White outer border of crop box
                                    drawRect(
                                        color = Color.White,
                                        topLeft = Offset(cLeft, cTop),
                                        size = Size(cWidth, cHeight),
                                        style = Stroke(width = 2.dp.toPx())
                                    )

                                    // 3. Rule of thirds grid lines
                                    val thirdW = cWidth / 3f
                                    val thirdH = cHeight / 3f
                                    val gridColor = Color.White.copy(alpha = 0.45f)
                                    val gridStroke = Stroke(width = 1.dp.toPx())

                                    // Vertical lines
                                    drawLine(gridColor, Offset(cLeft + thirdW, cTop), Offset(cLeft + thirdW, cBottom), strokeWidth = 1.dp.toPx())
                                    drawLine(gridColor, Offset(cLeft + 2 * thirdW, cTop), Offset(cLeft + 2 * thirdW, cBottom), strokeWidth = 1.dp.toPx())

                                    // Horizontal lines
                                    drawLine(gridColor, Offset(cLeft, cTop + thirdH), Offset(cRight, cTop + thirdH), strokeWidth = 1.dp.toPx())
                                    drawLine(gridColor, Offset(cLeft, cTop + 2 * thirdH), Offset(cRight, cTop + 2 * thirdH), strokeWidth = 1.dp.toPx())

                                    // 4. Corner Handles (L shapes)
                                    val handleLen = 20.dp.toPx()
                                    val handleThickness = 4.dp.toPx()
                                    val handleColor = AccentBlue

                                    // Top-Left
                                    drawLine(handleColor, Offset(cLeft - 2, cTop), Offset(cLeft + handleLen, cTop), strokeWidth = handleThickness)
                                    drawLine(handleColor, Offset(cLeft, cTop - 2), Offset(cLeft, cTop + handleLen), strokeWidth = handleThickness)

                                    // Top-Right
                                    drawLine(handleColor, Offset(cRight - handleLen, cTop), Offset(cRight + 2, cTop), strokeWidth = handleThickness)
                                    drawLine(handleColor, Offset(cRight, cTop - 2), Offset(cRight, cTop + handleLen), strokeWidth = handleThickness)

                                    // Bottom-Left
                                    drawLine(handleColor, Offset(cLeft - 2, cBottom), Offset(cLeft + handleLen, cBottom), strokeWidth = handleThickness)
                                    drawLine(handleColor, Offset(cLeft, cBottom - handleLen), Offset(cLeft, cBottom + 2), strokeWidth = handleThickness)

                                    // Bottom-Right
                                    drawLine(handleColor, Offset(cRight - handleLen, cBottom), Offset(cRight + 2, cBottom), strokeWidth = handleThickness)
                                    drawLine(handleColor, Offset(cRight, cBottom - handleLen), Offset(cRight, cBottom + 2), strokeWidth = handleThickness)
                                }
                            }
                        }
                    }
                }

                // Bottom Aspect Ratio Selector Bar
                Surface(
                    color = DarkSurface,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .navigationBarsPadding()
                            .padding(horizontal = 16.dp, vertical = 12.dp),
                        horizontalArrangement = Arrangement.SpaceEvenly,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        val ratios = listOf(
                            "Serbest" to null,
                            "1:1" to 1.0f,
                            "16:9" to 16f / 9f,
                            "4:3" to 4f / 3f,
                            "9:16" to 9f / 16f
                        )

                        ratios.forEach { (name, ratioVal) ->
                            val isSelected = selectedRatioName == name
                            FilterChip(
                                selected = isSelected,
                                onClick = {
                                    selectedRatioName = name
                                    fixedAspectRatio = ratioVal

                                    val bmp = originalBitmap
                                    if (ratioVal != null && bmp != null) {
                                        // Adjust current crop rect to match aspect ratio
                                        val curW = cropRight - cropLeft
                                        val curH = cropBottom - cropTop
                                        val centerNormX = (cropLeft + cropRight) / 2f
                                        val centerNormY = (cropTop + cropBottom) / 2f

                                        val targetAspectInNorm = ratioVal / (bmp.width.toFloat() / bmp.height.toFloat())

                                        var newWNorm: Float
                                        var newHNorm: Float

                                        if (curW / curH > targetAspectInNorm) {
                                            newHNorm = curH
                                            newWNorm = curH * targetAspectInNorm
                                        } else {
                                            newWNorm = curW
                                            newHNorm = curW / targetAspectInNorm
                                        }

                                        newWNorm = newWNorm.coerceIn(0.1f, 1f)
                                        newHNorm = newHNorm.coerceIn(0.1f, 1f)

                                        cropLeft = (centerNormX - newWNorm / 2f).coerceIn(0f, 1f - newWNorm)
                                        cropRight = cropLeft + newWNorm
                                        cropTop = (centerNormY - newHNorm / 2f).coerceIn(0f, 1f - newHNorm)
                                        cropBottom = cropTop + newHNorm
                                    }
                                },
                                label = {
                                    Text(
                                        text = name,
                                        style = MaterialTheme.typography.bodySmall.copy(
                                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal
                                        )
                                    )
                                },
                                colors = FilterChipDefaults.filterChipColors(
                                    selectedContainerColor = ChipSelected,
                                    selectedLabelColor = Color.White,
                                    containerColor = ChipUnselected,
                                    labelColor = TextSecondary
                                ),
                                border = null,
                                shape = RoundedCornerShape(14.dp)
                            )
                        }
                    }
                }
            }
        }
    }
}
