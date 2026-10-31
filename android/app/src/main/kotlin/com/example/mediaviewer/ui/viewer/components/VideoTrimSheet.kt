package com.example.mediaviewer.ui.viewer.components

import android.widget.Toast
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.ContentCut
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.RangeSlider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.mediaviewer.model.MediaItem
import com.example.mediaviewer.ui.theme.AccentBlue
import com.example.mediaviewer.ui.theme.DarkBorder
import com.example.mediaviewer.ui.theme.DarkSurface
import com.example.mediaviewer.ui.theme.TextMuted
import com.example.mediaviewer.ui.theme.TextPrimary
import com.example.mediaviewer.ui.theme.TextSecondary
import com.example.mediaviewer.util.VideoTrimmer
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VideoTrimSheet(
    item: MediaItem,
    totalDurationMs: Long,
    onDismiss: () -> Unit,
    onSaved: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)

    val validDuration = if (totalDurationMs > 0) totalDurationMs else (item.durationMs.takeIf { it > 0 } ?: 60000L)
    var sliderPosition by remember { mutableStateOf(0f..validDuration.toFloat()) }
    var isTrimming by remember { mutableStateOf(false) }

    val startMs = sliderPosition.start.toLong()
    val endMs = sliderPosition.endInclusive.toLong()
    val selectedDurationMs = (endMs - startMs).coerceAtLeast(0L)

    ModalBottomSheet(
        onDismissRequest = { if (!isTrimming) onDismiss() },
        sheetState = sheetState,
        containerColor = DarkSurface
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .navigationBarsPadding()
                .padding(horizontal = 20.dp, vertical = 12.dp)
        ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Default.ContentCut,
                        contentDescription = null,
                        tint = AccentBlue,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Video Kırpıcı (Trimmer)",
                        style = MaterialTheme.typography.titleMedium.copy(
                            fontWeight = FontWeight.Bold,
                            color = TextPrimary
                        )
                    )
                }

                IconButton(
                    onClick = { if (!isTrimming) onDismiss() },
                    enabled = !isTrimming
                ) {
                    Icon(Icons.Default.Close, contentDescription = "Kapat", tint = TextSecondary)
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Time preview info
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text("Başlangıç", color = TextMuted, fontSize = 12.sp)
                    Text(formatMillis(startMs), color = TextPrimary, fontWeight = FontWeight.Bold, fontSize = 15.sp)
                }

                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("Kırpılacak Süre", color = AccentBlue, fontSize = 12.sp)
                    Text(formatMillis(selectedDurationMs), color = AccentBlue, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                }

                Column(horizontalAlignment = Alignment.End) {
                    Text("Bitiş", color = TextMuted, fontSize = 12.sp)
                    Text(formatMillis(endMs), color = TextPrimary, fontWeight = FontWeight.Bold, fontSize = 15.sp)
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Range Slider
            RangeSlider(
                value = sliderPosition,
                onValueChange = { range ->
                    sliderPosition = range
                },
                valueRange = 0f..validDuration.toFloat(),
                colors = SliderDefaults.colors(
                    thumbColor = AccentBlue,
                    activeTrackColor = AccentBlue,
                    inactiveTrackColor = DarkBorder
                ),
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Action button
            Button(
                onClick = {
                    isTrimming = true
                    scope.launch {
                        val savedUri = VideoTrimmer.trimVideo(
                            context = context,
                            inputUri = item.uri,
                            startMs = startMs,
                            endMs = endMs,
                            originalName = item.name
                        )
                        isTrimming = false
                        if (savedUri != null) {
                            Toast.makeText(context, "Kırpılan video kaydedildi!", Toast.LENGTH_SHORT).show()
                            onSaved()
                            onDismiss()
                        } else {
                            Toast.makeText(context, "Video kırpılamadı!", Toast.LENGTH_SHORT).show()
                        }
                    }
                },
                enabled = !isTrimming && selectedDurationMs > 500,
                colors = ButtonDefaults.buttonColors(containerColor = AccentBlue),
                modifier = Modifier.fillMaxWidth().height(48.dp)
            ) {
                if (isTrimming) {
                    CircularProgressIndicator(color = Color.White, modifier = Modifier.size(20.dp))
                    Spacer(modifier = Modifier.width(10.dp))
                    Text("Kırpılıyor, lütfen bekleyin...")
                } else {
                    Icon(Icons.Default.ContentCut, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Videonun Bu Kısmını Kes ve Kaydet")
                }
            }

            Spacer(modifier = Modifier.height(20.dp))
        }
    }
}

private fun formatMillis(millis: Long): String {
    if (millis <= 0) return "00:00"
    val totalSeconds = millis / 1000
    val hours = totalSeconds / 3600
    val minutes = (totalSeconds % 3600) / 60
    val seconds = totalSeconds % 60
    return if (hours > 0) {
        String.format("%d:%02d:%02d", hours, minutes, seconds)
    } else {
        String.format("%02d:%02d", minutes, seconds)
    }
}
