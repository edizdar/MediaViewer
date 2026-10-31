package com.example.mediaviewer.ui.viewer.components

import android.graphics.Bitmap
import android.widget.Toast
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Done
import androidx.compose.material.icons.filled.RestartAlt
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.graphics.ColorMatrix
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.mediaviewer.model.MediaItem
import com.example.mediaviewer.ui.theme.AccentBlue
import com.example.mediaviewer.ui.theme.DarkBorder
import com.example.mediaviewer.ui.theme.DarkSurface
import com.example.mediaviewer.ui.theme.DarkSurfaceElevated
import com.example.mediaviewer.ui.theme.TextPrimary
import com.example.mediaviewer.ui.theme.TextSecondary
import com.example.mediaviewer.util.ImageEditor
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ImageAdjustmentSheet(
    item: MediaItem,
    onDismiss: () -> Unit,
    onSaved: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)

    var originalBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var isLoading by remember { mutableStateOf(true) }
    var isSaving by remember { mutableStateOf(false) }

    var brightness by remember { mutableFloatStateOf(0f) }      // -100 to 100
    var contrast by remember { mutableFloatStateOf(1.0f) }     // 0.5 to 2.0
    var saturation by remember { mutableFloatStateOf(1.0f) }   // 0.0 to 2.0

    LaunchedEffect(item.uriString) {
        isLoading = true
        originalBitmap = ImageEditor.loadBitmapFromUri(context, item.uri, 1280)
        isLoading = false
    }

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        containerColor = DarkSurface
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 12.dp)
        ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "🎨 Renk ve Işık Ayarları",
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary
                    )
                )

                Row {
                    IconButton(
                        onClick = {
                            brightness = 0f
                            contrast = 1.0f
                            saturation = 1.0f
                        }
                    ) {
                        Icon(Icons.Default.RestartAlt, contentDescription = "Sıfırla", tint = TextSecondary)
                    }
                    IconButton(onClick = onDismiss) {
                        Icon(Icons.Default.Close, contentDescription = "Kapat", tint = TextSecondary)
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Real-time Preview Box
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(200.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(DarkSurfaceElevated),
                contentAlignment = Alignment.Center
            ) {
                if (isLoading) {
                    CircularProgressIndicator(color = AccentBlue)
                } else if (originalBitmap != null) {
                    // Compose live color matrix filter
                    val t = (1.0f - contrast) / 2.0f * 255.0f
                    val matrixValues = floatArrayOf(
                        contrast, 0f, 0f, 0f, t + brightness,
                        0f, contrast, 0f, 0f, t + brightness,
                        0f, 0f, contrast, 0f, t + brightness,
                        0f, 0f, 0f, 1f, 0f
                    )
                    val composeMatrix = ColorMatrix(matrixValues).apply {
                        val satMat = ColorMatrix().apply { setToSaturation(saturation) }
                        timesAssign(satMat)
                    }

                    Image(
                        bitmap = originalBitmap!!.asImageBitmap(),
                        contentDescription = "Önizleme",
                        contentScale = ContentScale.Fit,
                        colorFilter = ColorFilter.colorMatrix(composeMatrix),
                        modifier = Modifier.fillMaxHeight()
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Brightness Slider
            AdjustmentSliderRow(
                label = "Parlaklık",
                valueText = "${brightness.toInt()}",
                value = brightness,
                valueRange = -100f..100f,
                onValueChange = { brightness = it }
            )

            // Contrast Slider
            AdjustmentSliderRow(
                label = "Kontrast",
                valueText = String.format("%.2fx", contrast),
                value = contrast,
                valueRange = 0.5f..2.0f,
                onValueChange = { contrast = it }
            )

            // Saturation Slider
            AdjustmentSliderRow(
                label = "Doygunluk",
                valueText = String.format("%.2fx", saturation),
                value = saturation,
                valueRange = 0.0f..2.0f,
                onValueChange = { saturation = it }
            )

            Spacer(modifier = Modifier.height(20.dp))

            // Action Buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End
            ) {
                Button(
                    onClick = {
                        val bmp = originalBitmap ?: return@Button
                        isSaving = true
                        scope.launch {
                            val adjusted = ImageEditor.adjustBitmap(bmp, brightness, contrast, saturation)
                            val savedUri = ImageEditor.saveBitmap(context, adjusted, item.name, "_adjusted")
                            isSaving = false
                            if (savedUri != null) {
                                Toast.makeText(context, "Resim galeriye kaydedildi!", Toast.LENGTH_SHORT).show()
                                onSaved()
                                onDismiss()
                            } else {
                                Toast.makeText(context, "Kaydedilemedi!", Toast.LENGTH_SHORT).show()
                            }
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = AccentBlue),
                    enabled = !isSaving && originalBitmap != null
                ) {
                    if (isSaving) {
                        CircularProgressIndicator(color = Color.White, modifier = Modifier.size(18.dp))
                        Spacer(modifier = Modifier.width(8.dp))
                    } else {
                        Icon(Icons.Default.Done, contentDescription = null, modifier = Modifier.size(18.dp))
                        Spacer(modifier = Modifier.width(8.dp))
                    }
                    Text("Kaydet")
                }
            }
            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}

@Composable
private fun AdjustmentSliderRow(
    label: String,
    valueText: String,
    value: Float,
    valueRange: ClosedFloatingPointRange<Float>,
    onValueChange: (Float) -> Unit
) {
    Column(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(label, color = TextSecondary, fontSize = 13.sp)
            Text(valueText, color = AccentBlue, fontWeight = FontWeight.Bold, fontSize = 13.sp)
        }
        Slider(
            value = value,
            onValueChange = onValueChange,
            valueRange = valueRange,
            colors = SliderDefaults.colors(
                thumbColor = AccentBlue,
                activeTrackColor = AccentBlue,
                inactiveTrackColor = DarkBorder
            )
        )
    }
}
