package com.example.mediaviewer.ui.viewer.components

import android.widget.Toast
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.RadioButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
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
import com.example.mediaviewer.ui.theme.DarkSurface
import com.example.mediaviewer.ui.theme.TextMuted
import com.example.mediaviewer.ui.theme.TextPrimary
import com.example.mediaviewer.ui.theme.TextSecondary
import com.example.mediaviewer.util.ImageEditor
import kotlinx.coroutines.launch

@Composable
fun SmartUpscaleDialog(
    item: MediaItem,
    onDismiss: () -> Unit,
    onSaved: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    var scaleFactor by remember { mutableIntStateOf(2) }
    var isProcessing by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = { if (!isProcessing) onDismiss() },
        containerColor = DarkSurface,
        shape = RoundedCornerShape(16.dp),
        title = {
            Text(
                text = "🖼️ Akıllı HD Büyütme",
                style = MaterialTheme.typography.titleMedium.copy(
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary
                )
            )
        },
        text = {
            Column(modifier = Modifier.fillMaxWidth()) {
                Text(
                    text = "Fotoğrafı yapay zeka destekli kenar keskinleştirme ve yüksek çözünürlüklü piksel Enterpolasyonu ile netleştirir.",
                    style = MaterialTheme.typography.bodyMedium.copy(color = TextSecondary, fontSize = 13.sp)
                )

                Spacer(modifier = Modifier.height(16.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    RadioButton(
                        selected = scaleFactor == 2,
                        onClick = { scaleFactor = 2 },
                        colors = RadioButtonDefaults.colors(selectedColor = AccentBlue)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Column {
                        Text("2x HD Büyütme", color = TextPrimary, fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                        Text("Hızlı ve dengeli netleştirme", color = TextMuted, fontSize = 11.sp)
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    RadioButton(
                        selected = scaleFactor == 4,
                        onClick = { scaleFactor = 4 },
                        colors = RadioButtonDefaults.colors(selectedColor = AccentBlue)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Column {
                        Text("4x Ultra HD Büyütme", color = TextPrimary, fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                        Text("Maksimum çözünürlük ve detay", color = TextMuted, fontSize = 11.sp)
                    }
                }

                if (isProcessing) {
                    Spacer(modifier = Modifier.height(16.dp))
                    LinearProgressIndicator(
                        modifier = Modifier.fillMaxWidth(),
                        color = AccentBlue
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "HD işleniyor, lütfen bekleyin...",
                        color = AccentBlue,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    isProcessing = true
                    scope.launch {
                        val original = ImageEditor.loadBitmapFromUri(context, item.uri, 3000)
                        if (original != null) {
                            val upscaled = ImageEditor.smartHdUpscale(original, scaleFactor)
                            val savedUri = ImageEditor.saveBitmap(context, upscaled, item.name, "_${scaleFactor}x_HD")
                            isProcessing = false
                            if (savedUri != null) {
                                Toast.makeText(context, "${scaleFactor}x HD fotoğraf galeriye kaydedildi!", Toast.LENGTH_SHORT).show()
                                onSaved()
                                onDismiss()
                            } else {
                                Toast.makeText(context, "HD resim kaydedilemedi!", Toast.LENGTH_SHORT).show()
                            }
                        } else {
                            isProcessing = false
                            Toast.makeText(context, "Resim yüklenemedi!", Toast.LENGTH_SHORT).show()
                        }
                    }
                },
                enabled = !isProcessing,
                colors = ButtonDefaults.buttonColors(containerColor = AccentBlue)
            ) {
                if (isProcessing) {
                    CircularProgressIndicator(color = Color.White, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                }
                Text("Büyüt ve Kaydet")
            }
        },
        dismissButton = {
            if (!isProcessing) {
                TextButton(onClick = onDismiss) {
                    Text("İptal", color = TextSecondary)
                }
            }
        }
    )
}
