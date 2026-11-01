package com.example.mediaviewer.ui.dialogs

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Bookmark
import androidx.compose.material.icons.filled.BookmarkBorder
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.LiveTv
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Sensors
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CheckboxDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.RadioButton
import androidx.compose.material3.RadioButtonDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.TabRowDefaults
import androidx.compose.material3.TabRowDefaults.tabIndicatorOffset
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.mediaviewer.data.SavedStream
import com.example.mediaviewer.data.StreamManager
import com.example.mediaviewer.model.MediaItem
import com.example.mediaviewer.ui.theme.AccentBlue
import com.example.mediaviewer.ui.theme.AccentCyan
import com.example.mediaviewer.ui.theme.AccentRed
import com.example.mediaviewer.ui.theme.DarkSurface
import com.example.mediaviewer.ui.theme.TextMuted
import com.example.mediaviewer.ui.theme.TextPrimary
import com.example.mediaviewer.ui.theme.TextSecondary

@Composable
fun NetworkStreamDialog(
    onDismiss: () -> Unit,
    onPlayStream: (MediaItem) -> Unit,
    onPlayPlaylist: (List<MediaItem>) -> Unit = {}
) {
    val context = LocalContext.current
    var selectedTabIndex by remember { mutableIntStateOf(0) } // 0: Yeni Akış Aç, 1: Kayıtlı Akışlar

    var urlText by remember { mutableStateOf("") }
    var nameText by remember { mutableStateOf("") }
    var saveStreamChecked by remember { mutableStateOf(true) }
    var bufferMode by remember { mutableStateOf(StreamManager.getBufferMode(context)) }

    var savedStreams by remember { mutableStateOf(StreamManager.getSavedStreams(context)) }

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = DarkSurface,
        shape = RoundedCornerShape(20.dp),
        title = {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.LiveTv,
                    contentDescription = null,
                    tint = AccentCyan,
                    modifier = Modifier.size(26.dp)
                )
                Text(
                    text = "Ağ Akışı / Canlı Yayın Aç",
                    style = MaterialTheme.typography.titleLarge.copy(
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary
                    )
                )
            }
        },
        text = {
            Column(modifier = Modifier.fillMaxWidth()) {
                TabRow(
                    selectedTabIndex = selectedTabIndex,
                    containerColor = Color.Transparent,
                    contentColor = AccentBlue,
                    indicator = { tabPositions ->
                        TabRowDefaults.SecondaryIndicator(
                            Modifier.tabIndicatorOffset(tabPositions[selectedTabIndex]),
                            color = AccentBlue
                        )
                    }
                ) {
                    Tab(
                        selected = selectedTabIndex == 0,
                        onClick = { selectedTabIndex = 0 },
                        text = {
                            Text(
                                "Adres Gir (URL)",
                                fontSize = 13.sp,
                                fontWeight = if (selectedTabIndex == 0) FontWeight.Bold else FontWeight.Normal,
                                color = if (selectedTabIndex == 0) AccentBlue else TextSecondary
                            )
                        }
                    )
                    Tab(
                        selected = selectedTabIndex == 1,
                        onClick = { selectedTabIndex = 1 },
                        text = {
                            Text(
                                "Kayıtlılar (${savedStreams.size})",
                                fontSize = 13.sp,
                                fontWeight = if (selectedTabIndex == 1) FontWeight.Bold else FontWeight.Normal,
                                color = if (selectedTabIndex == 1) AccentBlue else TextSecondary
                            )
                        }
                    )
                }

                Spacer(modifier = Modifier.height(14.dp))

                if (selectedTabIndex == 0) {
                    // TAB 0: YENİ ADRES GİR
                    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        Text(
                            text = "RTSP, HLS (.m3u8), IPTV (.m3u) veya HTTP video adresi yapıştırın:",
                            fontSize = 12.sp,
                            color = TextSecondary
                        )

                        OutlinedTextField(
                            value = urlText,
                            onValueChange = { urlText = it },
                            placeholder = { Text("rtsp://... veya https://.../stream.m3u8", fontSize = 12.sp, color = TextMuted) },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true,
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = AccentBlue,
                                unfocusedBorderColor = Color(0xFF2E3846),
                                focusedTextColor = TextPrimary,
                                unfocusedTextColor = TextPrimary
                            ),
                            shape = RoundedCornerShape(10.dp)
                        )

                        OutlinedTextField(
                            value = nameText,
                            onValueChange = { nameText = it },
                            label = { Text("Akış Adı (İsteğe bağlı)", fontSize = 12.sp) },
                            placeholder = { Text("Örn: Bahçe Kamerası, Canlı Haber", fontSize = 12.sp, color = TextMuted) },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true,
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = AccentBlue,
                                unfocusedBorderColor = Color(0xFF2E3846),
                                focusedTextColor = TextPrimary,
                                unfocusedTextColor = TextPrimary
                            ),
                            shape = RoundedCornerShape(10.dp)
                        )

                        // Tampon / Gecikme Modu
                        Text(
                            text = "Ağ Gecikmesi & Tampon Modu:",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = AccentCyan
                        )

                        Card(
                            colors = CardDefaults.cardColors(containerColor = Color(0xFF1E2230)),
                            shape = RoundedCornerShape(10.dp),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Column(modifier = Modifier.padding(6.dp)) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clickable { bufferMode = "LOW_LATENCY" }
                                ) {
                                    RadioButton(
                                        selected = bufferMode == "LOW_LATENCY",
                                        onClick = { bufferMode = "LOW_LATENCY" },
                                        colors = RadioButtonDefaults.colors(selectedColor = AccentBlue)
                                    )
                                    Column {
                                        Text("⚡ Düşük Gecikme (IP Kamera / Canlı CCTV)", fontSize = 12.sp, color = TextPrimary)
                                        Text("Gecikmeyi minimumda tutar (0.5s tampon)", fontSize = 10.sp, color = TextSecondary)
                                    }
                                }

                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clickable { bufferMode = "BALANCED" }
                                ) {
                                    RadioButton(
                                        selected = bufferMode == "BALANCED",
                                        onClick = { bufferMode = "BALANCED" },
                                        colors = RadioButtonDefaults.colors(selectedColor = AccentBlue)
                                    )
                                    Column {
                                        Text("🛡️ Dengeli & Kararlı (IPTV / HLS)", fontSize = 12.sp, color = TextPrimary)
                                        Text("Ağ dalgalanmalarına karşı 15s önbellek", fontSize = 10.sp, color = TextSecondary)
                                    }
                                }
                            }
                        }

                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.clickable { saveStreamChecked = !saveStreamChecked }
                        ) {
                            Checkbox(
                                checked = saveStreamChecked,
                                onCheckedChange = { saveStreamChecked = it },
                                colors = CheckboxDefaults.colors(checkedColor = AccentBlue)
                            )
                            Text(
                                text = "⭐ Bu akışı kayıtlılara ekle",
                                fontSize = 12.sp,
                                color = TextPrimary
                            )
                        }
                    }
                } else {
                    // TAB 1: KAYITLI VE ÖRNEK AKIŞLAR
                    LazyColumn(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(260.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        items(savedStreams, key = { it.id }) { stream ->
                            Card(
                                colors = CardDefaults.cardColors(containerColor = Color(0xFF1E2230)),
                                shape = RoundedCornerShape(10.dp),
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clickable {
                                        StreamManager.setBufferMode(context, stream.bufferMode)
                                        onDismiss()
                                        onPlayStream(stream.toMediaItem())
                                    }
                            ) {
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(10.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Column(modifier = Modifier.weight(1f)) {
                                        Text(
                                            text = stream.name,
                                            fontSize = 13.sp,
                                            fontWeight = FontWeight.SemiBold,
                                            color = TextPrimary,
                                            maxLines = 1
                                        )
                                        Text(
                                            text = "${stream.type} • ${if (stream.bufferMode == "LOW_LATENCY") "Düşük Gecikme" else "Kararlı Tampon"}",
                                            fontSize = 11.sp,
                                            color = AccentCyan
                                        )
                                        Text(
                                            text = stream.url,
                                            fontSize = 10.sp,
                                            color = TextMuted,
                                            maxLines = 1
                                        )
                                    }

                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        IconButton(
                                            onClick = {
                                                StreamManager.setBufferMode(context, stream.bufferMode)
                                                onDismiss()
                                                onPlayStream(stream.toMediaItem())
                                            }
                                        ) {
                                            Icon(
                                                imageVector = Icons.Default.PlayArrow,
                                                contentDescription = "Oynat",
                                                tint = AccentBlue
                                            )
                                        }

                                        if (!stream.id.startsWith("sample_")) {
                                            IconButton(
                                                onClick = {
                                                    StreamManager.deleteStream(context, stream.id)
                                                    savedStreams = StreamManager.getSavedStreams(context)
                                                }
                                            ) {
                                                Icon(
                                                    imageVector = Icons.Default.Delete,
                                                    contentDescription = "Sil",
                                                    tint = AccentRed.copy(alpha = 0.7f),
                                                    modifier = Modifier.size(18.dp)
                                                )
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        confirmButton = {
            if (selectedTabIndex == 0) {
                Button(
                    onClick = {
                        val cleanUrl = urlText.trim()
                        if (cleanUrl.isNotBlank()) {
                            StreamManager.setBufferMode(context, bufferMode)
                            if (saveStreamChecked) {
                                StreamManager.saveStream(context, nameText, cleanUrl, bufferMode = bufferMode)
                            }
                            val streamItem = SavedStream(
                                id = System.currentTimeMillis().toString(),
                                name = nameText.ifBlank { StreamManager.inferStreamName(cleanUrl) },
                                url = cleanUrl,
                                bufferMode = bufferMode
                            ).toMediaItem()
                            onDismiss()
                            onPlayStream(streamItem)
                        }
                    },
                    enabled = urlText.isNotBlank(),
                    colors = ButtonDefaults.buttonColors(containerColor = AccentBlue),
                    shape = RoundedCornerShape(10.dp)
                ) {
                    Text("▶️ Akışı Oynat", fontWeight = FontWeight.Bold)
                }
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Kapat", color = TextSecondary)
            }
        }
    )
}
