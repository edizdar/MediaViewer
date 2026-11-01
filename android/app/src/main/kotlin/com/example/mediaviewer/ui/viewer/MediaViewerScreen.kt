package com.example.mediaviewer.ui.viewer

import android.content.Intent
import android.os.Build
import android.provider.MediaStore
import android.widget.Toast
import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
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
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.automirrored.filled.RotateLeft
import androidx.compose.material.icons.automirrored.filled.RotateRight
import androidx.compose.material.icons.filled.Crop
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Flip
import androidx.compose.material.icons.filled.HighQuality
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Palette
import androidx.compose.material.icons.filled.QueueMusic
import androidx.compose.material.icons.filled.Save
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.mediaviewer.R
import com.example.mediaviewer.model.MediaItem
import com.example.mediaviewer.model.MediaType
import com.example.mediaviewer.ui.theme.AccentBlue
import com.example.mediaviewer.ui.theme.AccentCyan
import com.example.mediaviewer.ui.theme.AccentRed
import com.example.mediaviewer.ui.theme.DarkSurface
import com.example.mediaviewer.ui.theme.OverlayDark
import com.example.mediaviewer.ui.theme.TextPrimary
import com.example.mediaviewer.ui.theme.TextSecondary
import com.example.mediaviewer.ui.viewer.components.AudioPlayerView
import com.example.mediaviewer.ui.viewer.components.ImageAdjustmentSheet
import com.example.mediaviewer.ui.viewer.components.ImageCropDialog
import com.example.mediaviewer.ui.viewer.components.MediaInfoDialog
import com.example.mediaviewer.ui.viewer.components.PhotoView
import com.example.mediaviewer.ui.viewer.components.PlaylistFilmstrip
import com.example.mediaviewer.ui.viewer.components.SmartUpscaleDialog
import com.example.mediaviewer.ui.viewer.components.VideoPlayerView
import com.example.mediaviewer.ui.viewer.components.VideoTrimSheet
import com.example.mediaviewer.util.AppMode
import com.example.mediaviewer.util.ImageEditor
import com.example.mediaviewer.util.SettingsManager
import kotlinx.coroutines.launch

@Composable
fun MediaViewerScreen(
    items: List<MediaItem>,
    initialIndex: Int,
    onBack: () -> Unit,
    onDelete: (MediaItem) -> Unit = {},
    onModified: () -> Unit = {}
) {
    if (items.isEmpty()) {
        onBack()
        return
    }

    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val pagerState = rememberPagerState(
        initialPage = initialIndex.coerceIn(0, items.size - 1),
        pageCount = { items.size }
    )

    val isAdvancedMode = SettingsManager.appModeState.value == AppMode.ADVANCED

    var controlsVisible by remember { mutableStateOf(true) }
    var isCurrentZoomed by remember { mutableStateOf(false) }

    // Dialog & Sheet States
    var showInfoDialog by remember { mutableStateOf(false) }
    var showDeleteDialog by remember { mutableStateOf(false) }
    var showAdjustmentSheet by remember { mutableStateOf(false) }
    var showUpscaleDialog by remember { mutableStateOf(false) }
    var showCropDialog by remember { mutableStateOf(false) }
    var showPlaylistFilmstrip by remember { mutableStateOf(false) }
    var showTrimSheet by remember { mutableStateOf(false) }
    var trimTotalDurationMs by remember { mutableLongStateOf(0L) }

    // Image live transform states
    var imageRotation by remember { mutableFloatStateOf(0f) }
    var isImageFlipped by remember { mutableStateOf(false) }

    val currentItem = items.getOrNull(pagerState.currentPage) ?: items.first()

    // Reset rotation, flip and zoom when user swipes to a different photo
    LaunchedEffect(pagerState.currentPage) {
        imageRotation = 0f
        isImageFlipped = false
        isCurrentZoomed = false
    }

    BackHandler {
        onBack()
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
    ) {
        // Horizontal Pager for swiping across items
        HorizontalPager(
            state = pagerState,
            userScrollEnabled = !isCurrentZoomed,
            beyondViewportPageCount = 1,
            key = { page -> if (page in items.indices) items[page].uriString else page },
            modifier = Modifier.fillMaxSize()
        ) { page ->
            val item = items[page]
            val isCurrent = page == pagerState.currentPage

            when (item.mediaType) {
                MediaType.IMAGE -> {
                    PhotoView(
                        item = item,
                        rotation = if (isCurrent) imageRotation else 0f,
                        isFlipped = if (isCurrent) isImageFlipped else false,
                        onToggleControls = { controlsVisible = !controlsVisible },
                        onZoomChanged = { zoomed ->
                            if (isCurrent) isCurrentZoomed = zoomed
                        }
                    )
                }
                MediaType.VIDEO -> {
                    VideoPlayerView(
                        item = item,
                        isCurrentPage = isCurrent,
                        controlsVisible = controlsVisible,
                        onToggleControls = { controlsVisible = !controlsVisible },
                        onTrimClicked = if (isAdvancedMode) { dur ->
                            trimTotalDurationMs = dur
                            showTrimSheet = true
                        } else null
                    )
                }
                MediaType.AUDIO -> {
                    AudioPlayerView(
                        item = item,
                        isCurrentPage = isCurrent
                    )
                }
            }
        }

        // Left Navigation Arrow Button (Previous)
        AnimatedVisibility(
            visible = controlsVisible && pagerState.currentPage > 0,
            enter = fadeIn(),
            exit = fadeOut(),
            modifier = Modifier.align(Alignment.CenterStart)
        ) {
            Surface(
                shape = CircleShape,
                color = Color.Black.copy(alpha = 0.55f),
                modifier = Modifier
                    .padding(start = 12.dp)
                    .size(44.dp)
            ) {
                IconButton(
                    onClick = {
                        scope.launch {
                            pagerState.animateScrollToPage(pagerState.currentPage - 1)
                        }
                    }
                ) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                        contentDescription = "Önceki",
                        tint = Color.White
                    )
                }
            }
        }

        // Right Navigation Arrow Button (Next)
        AnimatedVisibility(
            visible = controlsVisible && pagerState.currentPage < items.size - 1,
            enter = fadeIn(),
            exit = fadeOut(),
            modifier = Modifier.align(Alignment.CenterEnd)
        ) {
            Surface(
                shape = CircleShape,
                color = Color.Black.copy(alpha = 0.55f),
                modifier = Modifier
                    .padding(end = 12.dp)
                    .size(44.dp)
            ) {
                IconButton(
                    onClick = {
                        scope.launch {
                            pagerState.animateScrollToPage(pagerState.currentPage + 1)
                        }
                    }
                ) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                        contentDescription = "Sonraki",
                        tint = Color.White
                    )
                }
            }
        }

        // Top Overlay Bar
        AnimatedVisibility(
            visible = controlsVisible,
            enter = fadeIn(),
            exit = fadeOut(),
            modifier = Modifier.align(Alignment.TopCenter)
        ) {
            Surface(
                color = OverlayDark,
                modifier = Modifier
                    .fillMaxWidth()
                    .statusBarsPadding()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 6.dp, vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Geri",
                            tint = Color.White
                        )
                    }

                    Image(
                        painter = painterResource(R.drawable.app_logo),
                        contentDescription = "Media Viewer Logo",
                        modifier = Modifier
                            .size(28.dp)
                            .clip(RoundedCornerShape(6.dp))
                    )

                    Spacer(modifier = Modifier.width(8.dp))

                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = currentItem.name,
                            style = MaterialTheme.typography.titleMedium.copy(
                                color = TextPrimary,
                                fontWeight = FontWeight.SemiBold,
                                fontSize = 14.sp
                            ),
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                        Text(
                            text = "${pagerState.currentPage + 1} / ${items.size}",
                            style = MaterialTheme.typography.bodySmall.copy(
                                color = TextSecondary,
                                fontSize = 11.sp
                            )
                        )
                    }

                    // Playlist Filmstrip toggle
                    IconButton(onClick = { showPlaylistFilmstrip = !showPlaylistFilmstrip }) {
                        Icon(
                            imageVector = Icons.Default.QueueMusic,
                            contentDescription = "Oynatma Listesi / Şerit",
                            tint = if (showPlaylistFilmstrip) AccentCyan else Color.White
                        )
                    }

                    // Share button
                    IconButton(
                        onClick = {
                            val shareIntent = Intent(Intent.ACTION_SEND).apply {
                                type = currentItem.mimeType
                                putExtra(Intent.EXTRA_STREAM, currentItem.uri)
                                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                            }
                            context.startActivity(Intent.createChooser(shareIntent, "Paylaş"))
                        }
                    ) {
                        Icon(
                            imageVector = Icons.Default.Share,
                            contentDescription = "Paylaş",
                            tint = Color.White
                        )
                    }

                    // Delete button
                    IconButton(
                        onClick = {
                            if (SettingsManager.confirmDeleteState.value) {
                                showDeleteDialog = true
                            } else {
                                onDelete(currentItem)
                            }
                        }
                    ) {
                        Icon(
                            imageVector = Icons.Default.Delete,
                            contentDescription = stringResource(R.string.delete),
                            tint = AccentRed
                        )
                    }

                    // Info button
                    IconButton(onClick = { showInfoDialog = true }) {
                        Icon(
                            imageVector = Icons.Default.Info,
                            contentDescription = "Bilgi",
                            tint = Color.White
                        )
                    }
                }
            }
        }

        val showBottomContainer = showPlaylistFilmstrip || (currentItem.mediaType == MediaType.IMAGE && isAdvancedMode)

        // Bottom Controls Container (Playlist Filmstrip & Image Tools Toolbar)
        AnimatedVisibility(
            visible = controlsVisible && showBottomContainer,
            enter = fadeIn(),
            exit = fadeOut(),
            modifier = Modifier.align(Alignment.BottomCenter)
        ) {
            Surface(
                color = OverlayDark,
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .navigationBarsPadding()
                        .padding(bottom = 8.dp)
                ) {
                    // Playlist Filmstrip
                    if (showPlaylistFilmstrip) {
                        PlaylistFilmstrip(
                            items = items,
                            currentIndex = pagerState.currentPage,
                            onSelectIndex = { targetIdx ->
                                scope.launch {
                                    pagerState.animateScrollToPage(targetIdx)
                                }
                            }
                        )
                    }

                    // Desktop-matching Image Toolbar (Rotate, Crop, Color Adjust, Upscale) - only in Advanced Mode
                    if (currentItem.mediaType == MediaType.IMAGE && isAdvancedMode) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(horizontal = 8.dp, vertical = 6.dp),
                            horizontalArrangement = Arrangement.SpaceEvenly,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            // Rotate CCW (Sola 90°)
                            IconButton(onClick = { imageRotation = (imageRotation - 90f) % 360f }) {
                                Icon(Icons.AutoMirrored.Filled.RotateLeft, contentDescription = "Sola Döndür", tint = Color.White)
                            }

                            // Rotate CW (Sağa 90°)
                            IconButton(onClick = { imageRotation = (imageRotation + 90f) % 360f }) {
                                Icon(Icons.AutoMirrored.Filled.RotateRight, contentDescription = "Sağa Döndür", tint = Color.White)
                            }

                            // Flip (Aynala)
                            IconButton(onClick = { isImageFlipped = !isImageFlipped }) {
                                Icon(Icons.Default.Flip, contentDescription = "Aynala", tint = Color.White)
                            }

                            // Crop (Kırp)
                            IconButton(onClick = { showCropDialog = true }) {
                                Icon(Icons.Default.Crop, contentDescription = "Kırp", tint = Color.White)
                            }

                            // Adjustments (Renk / Işık Ayarları)
                            IconButton(onClick = { showAdjustmentSheet = true }) {
                                Icon(Icons.Default.Palette, contentDescription = "Renk Ayarları", tint = AccentCyan)
                            }

                            // HD Upscale (HD Yap)
                            IconButton(onClick = { showUpscaleDialog = true }) {
                                Icon(Icons.Default.HighQuality, contentDescription = "HD Büyüt", tint = AccentBlue)
                            }

                            // If rotated or flipped, show quick Save button
                            if (imageRotation != 0f || isImageFlipped) {
                                IconButton(
                                    onClick = {
                                        scope.launch {
                                            val bmp = ImageEditor.loadBitmapFromUri(context, currentItem.uri, 3000)
                                            if (bmp != null) {
                                                var transformed = bmp
                                                if (imageRotation != 0f) {
                                                    transformed = ImageEditor.rotateBitmap(transformed, imageRotation)
                                                }
                                                if (isImageFlipped) {
                                                    transformed = ImageEditor.flipBitmap(transformed, true)
                                                }
                                                val savedUri = ImageEditor.saveBitmap(context, transformed, currentItem.name, "_rotated")
                                                if (savedUri != null) {
                                                    Toast.makeText(context, "Döndürülmüş fotoğraf kaydedildi!", Toast.LENGTH_SHORT).show()
                                                    imageRotation = 0f
                                                    isImageFlipped = false
                                                    onModified()
                                                }
                                            }
                                        }
                                    }
                                ) {
                                    Icon(Icons.Default.Save, contentDescription = "Kaydet", tint = AccentBlue)
                                }
                            }
                        }
                    }
                }
            }
        }

        // Info Dialog
        if (showInfoDialog) {
            MediaInfoDialog(
                item = currentItem,
                onDismiss = { showInfoDialog = false }
            )
        }

        // Delete Confirmation Dialog
        if (showDeleteDialog) {
            AlertDialog(
                onDismissRequest = { showDeleteDialog = false },
                containerColor = DarkSurface,
                shape = RoundedCornerShape(16.dp),
                title = { Text(stringResource(R.string.delete_dialog_title), color = TextPrimary, fontWeight = FontWeight.Bold) },
                text = {
                    Text(
                        text = stringResource(R.string.delete_dialog_msg, currentItem.name),
                        color = TextSecondary
                    )
                },
                confirmButton = {
                    Button(
                        onClick = {
                            showDeleteDialog = false
                            onDelete(currentItem)
                        },
                        colors = androidx.compose.material3.ButtonDefaults.buttonColors(containerColor = AccentRed)
                    ) {
                        Text(stringResource(R.string.delete))
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showDeleteDialog = false }) {
                        Text(stringResource(R.string.cancel), color = TextSecondary)
                    }
                }
            )
        }

        // Image Adjustments Sheet
        if (showAdjustmentSheet) {
            ImageAdjustmentSheet(
                item = currentItem,
                onDismiss = { showAdjustmentSheet = false },
                onSaved = { onModified() }
            )
        }

        // Smart HD Upscale Dialog
        if (showUpscaleDialog) {
            SmartUpscaleDialog(
                item = currentItem,
                onDismiss = { showUpscaleDialog = false },
                onSaved = { onModified() }
            )
        }

        // Crop Dialog
        if (showCropDialog) {
            ImageCropDialog(
                item = currentItem,
                onDismiss = { showCropDialog = false },
                onSaved = { onModified() }
            )
        }

        // Video Trim Sheet
        if (showTrimSheet) {
            VideoTrimSheet(
                item = currentItem,
                totalDurationMs = trimTotalDurationMs,
                onDismiss = { showTrimSheet = false },
                onSaved = { onModified() }
            )
        }
    }
}
