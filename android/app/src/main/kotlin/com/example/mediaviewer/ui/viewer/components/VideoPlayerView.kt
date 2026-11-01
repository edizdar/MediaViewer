package com.example.mediaviewer.ui.viewer.components

import android.app.Activity
import android.content.ContentValues
import android.content.Context
import android.graphics.Bitmap
import android.media.AudioManager
import android.os.Build
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.provider.MediaStore
import android.view.PixelCopy
import android.view.SurfaceView
import android.view.TextureView
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.Toast
import androidx.annotation.OptIn
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BrightnessHigh
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.ContentCut
import androidx.compose.material.icons.filled.FastForward
import androidx.compose.material.icons.filled.FastRewind
import androidx.compose.material.icons.filled.FitScreen
import androidx.compose.material.icons.filled.HighQuality
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Replay
import androidx.compose.material.icons.filled.Speed
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.MediaItem as ExoMediaItem
import androidx.media3.common.PlaybackParameters
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.DefaultLoadControl
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.rtsp.RtspMediaSource
import androidx.media3.ui.AspectRatioFrameLayout
import androidx.media3.ui.PlayerView
import com.example.mediaviewer.data.StreamManager
import com.example.mediaviewer.model.MediaItem
import com.example.mediaviewer.ui.theme.AccentBlue
import com.example.mediaviewer.ui.theme.AccentCyan
import com.example.mediaviewer.ui.theme.AccentGreen
import com.example.mediaviewer.ui.theme.AccentRed
import com.example.mediaviewer.ui.theme.DarkSurface
import com.example.mediaviewer.ui.theme.OverlayDark
import com.example.mediaviewer.ui.theme.TextPrimary
import com.example.mediaviewer.ui.theme.TextSecondary
import kotlinx.coroutines.delay

@OptIn(UnstableApi::class)
@Composable
fun VideoPlayerView(
    item: MediaItem,
    isCurrentPage: Boolean,
    controlsVisible: Boolean,
    onToggleControls: () -> Unit,
    onTrimClicked: ((Long) -> Unit)? = null,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val audioManager = remember { context.getSystemService(Context.AUDIO_SERVICE) as AudioManager }
    val activity = context as? Activity

    val isRtsp = item.uriString.startsWith("rtsp://", ignoreCase = true)
    val isNetworkStream = item.uriString.startsWith("http://", ignoreCase = true) ||
            item.uriString.startsWith("https://", ignoreCase = true) ||
            isRtsp

    val bufferMode = remember { StreamManager.getBufferMode(context) }

    // ExoPlayer instance configured with network latency tuning and load control
    val exoPlayer = remember {
        val loadControl = DefaultLoadControl.Builder()
            .setBufferDurationsMs(
                /* minBufferMs = */ if (bufferMode == "LOW_LATENCY") 3_000 else 15_000,
                /* maxBufferMs = */ if (bufferMode == "LOW_LATENCY") 10_000 else 50_000,
                /* bufferForPlaybackMs = */ if (bufferMode == "LOW_LATENCY") 500 else 1_500,
                /* bufferForPlaybackAfterRebufferMs = */ if (bufferMode == "LOW_LATENCY") 1_000 else 3_000
            )
            .build()

        ExoPlayer.Builder(context)
            .setLoadControl(loadControl)
            .build().apply {
                repeatMode = Player.REPEAT_MODE_OFF
            }
    }

    var isPlaying by remember { mutableStateOf(false) }
    var currentPosition by remember { mutableLongStateOf(0L) }
    var duration by remember { mutableLongStateOf(0L) }
    var isBuffering by remember { mutableStateOf(true) }
    var isLiveStream by remember { mutableStateOf(isRtsp || item.uriString.contains(".m3u8", ignoreCase = true)) }
    var playbackSpeed by remember { mutableFloatStateOf(1.0f) }
    var resizeMode by remember { mutableIntStateOf(AspectRatioFrameLayout.RESIZE_MODE_FIT) }

    // Quality selection states
    var showQualityMenu by remember { mutableStateOf(false) }
    var selectedQualityLabel by remember { mutableStateOf("Otomatik") }

    // PlayerView reference for snapshot capture
    var playerViewRef by remember { mutableStateOf<PlayerView?>(null) }

    // Gesture HUD states
    var showBrightnessHud by remember { mutableStateOf(false) }
    var brightnessPercent by remember { mutableIntStateOf(50) }
    var showVolumeHud by remember { mutableStateOf(false) }
    var volumePercent by remember { mutableIntStateOf(50) }
    var seekNoticeText by remember { mutableStateOf<String?>(null) }
    var showSpeedMenu by remember { mutableStateOf(false) }

    // Load media item into player
    LaunchedEffect(item.uriString) {
        val uri = item.uri
        if (isRtsp) {
            // Force TCP transport for RTSP to prevent packet loss over lossy Wi-Fi/mobile networks
            val rtspSource = RtspMediaSource.Factory()
                .setForceUseRtpTcp(true)
                .createMediaSource(ExoMediaItem.fromUri(uri))
            exoPlayer.setMediaSource(rtspSource)
        } else {
            val mediaItem = ExoMediaItem.fromUri(uri)
            exoPlayer.setMediaItem(mediaItem)
        }
        exoPlayer.prepare()
        if (isCurrentPage) {
            exoPlayer.playWhenReady = true
        }
    }

    // Play/Pause depending on whether this page is current
    LaunchedEffect(isCurrentPage) {
        if (!isCurrentPage) {
            exoPlayer.pause()
        } else {
            exoPlayer.play()
        }
    }

    // Listen to player state
    DisposableEffect(exoPlayer) {
        val listener = object : Player.Listener {
            override fun onIsPlayingChanged(playing: Boolean) {
                isPlaying = playing
            }

            override fun onPlaybackStateChanged(state: Int) {
                isBuffering = state == Player.STATE_BUFFERING
                if (state == Player.STATE_READY) {
                    val d = exoPlayer.duration
                    duration = d.coerceAtLeast(0L)
                    isLiveStream = exoPlayer.isCurrentMediaItemLive || isRtsp || d <= 0L
                }
            }
        }
        exoPlayer.addListener(listener)
        onDispose {
            exoPlayer.removeListener(listener)
            exoPlayer.release()
        }
    }

    // Position update loop
    LaunchedEffect(isPlaying) {
        while (isPlaying) {
            currentPosition = exoPlayer.currentPosition.coerceAtLeast(0L)
            val d = exoPlayer.duration
            if (d > 0) duration = d
            delay(500)
        }
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Color.Black)
            // Gesture handling: Tap, Double tap, Vertical drags
            .pointerInput(Unit) {
                detectTapGestures(
                    onTap = { onToggleControls() },
                    onDoubleTap = { offset ->
                        if (!isLiveStream) {
                            val isLeft = offset.x < size.width / 2
                            if (isLeft) {
                                val newPos = (exoPlayer.currentPosition - 10000).coerceAtLeast(0L)
                                exoPlayer.seekTo(newPos)
                                currentPosition = newPos
                                seekNoticeText = "⏪ -10s"
                            } else {
                                val newPos = (exoPlayer.currentPosition + 10000).coerceAtMost(duration)
                                exoPlayer.seekTo(newPos)
                                currentPosition = newPos
                                seekNoticeText = "⏩ +10s"
                            }
                        }
                    }
                )
            }
            .pointerInput(Unit) {
                detectVerticalDragGestures(
                    onDragStart = { offset ->
                        val isLeft = offset.x < size.width / 2
                        if (isLeft) {
                            showBrightnessHud = true
                            activity?.let { act ->
                                val curBright = act.window.attributes.screenBrightness
                                val initial = if (curBright < 0) 0.5f else curBright
                                brightnessPercent = (initial * 100).toInt()
                            }
                        } else {
                            showVolumeHud = true
                            val max = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC)
                            val cur = audioManager.getStreamVolume(AudioManager.STREAM_MUSIC)
                            volumePercent = ((cur.toFloat() / max) * 100).toInt()
                        }
                    },
                    onDragEnd = {
                        showBrightnessHud = false
                        showVolumeHud = false
                    },
                    onDragCancel = {
                        showBrightnessHud = false
                        showVolumeHud = false
                    },
                    onVerticalDrag = { change, dragAmount ->
                        change.consume()
                        val isLeft = change.position.x < size.width / 2
                        val delta = -dragAmount / size.height

                        if (isLeft) {
                            activity?.let { act ->
                                val params = act.window.attributes
                                val cur = if (params.screenBrightness < 0) 0.5f else params.screenBrightness
                                val next = (cur + delta).coerceIn(0.01f, 1.0f)
                                params.screenBrightness = next
                                act.window.attributes = params
                                brightnessPercent = (next * 100).toInt()
                                showBrightnessHud = true
                            }
                        } else {
                            val max = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC)
                            val cur = audioManager.getStreamVolume(AudioManager.STREAM_MUSIC)
                            val step = (delta * max).toInt()
                            val next = (cur + step).coerceIn(0, max)
                            audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, next, 0)
                            volumePercent = ((next.toFloat() / max) * 100).toInt()
                            showVolumeHud = true
                        }
                    }
                )
            }
    ) {
        // AndroidView holding PlayerView
        AndroidView(
            factory = { ctx ->
                PlayerView(ctx).apply {
                    player = exoPlayer
                    useController = false
                    this.resizeMode = resizeMode
                    layoutParams = FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                    )
                    playerViewRef = this
                }
            },
            update = { playerView ->
                playerView.resizeMode = resizeMode
                playerViewRef = playerView
            },
            modifier = Modifier.fillMaxSize()
        )

        // Buffering indicator
        if (isBuffering) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator(
                    color = AccentBlue,
                    modifier = Modifier.size(48.dp)
                )
            }
        }

        // Live Stream Badge (CANLI)
        if (isLiveStream) {
            Surface(
                shape = RoundedCornerShape(8.dp),
                color = OverlayDark,
                modifier = Modifier
                    .align(Alignment.TopStart)
                    .padding(start = 16.dp, top = 60.dp)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(10.dp)
                            .background(AccentRed, CircleShape)
                    )
                    Text(
                        text = "CANLI YAYIN",
                        color = Color.White,
                        fontWeight = FontWeight.Bold,
                        fontSize = 11.sp
                    )
                    Text(
                        text = "• ${StreamManager.inferStreamType(item.uriString)}",
                        color = AccentCyan,
                        fontSize = 11.sp
                    )
                }
            }
        }

        // Gesture HUD - Brightness
        if (showBrightnessHud) {
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = OverlayDark,
                modifier = Modifier
                    .align(Alignment.CenterStart)
                    .padding(start = 32.dp)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Default.BrightnessHigh,
                        contentDescription = null,
                        tint = Color.White,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "$brightnessPercent%",
                        color = Color.White,
                        fontWeight = FontWeight.Bold,
                        fontSize = 16.sp
                    )
                }
            }
        }

        // Gesture HUD - Volume
        if (showVolumeHud) {
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = OverlayDark,
                modifier = Modifier
                    .align(Alignment.CenterEnd)
                    .padding(end = 32.dp)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Default.VolumeUp,
                        contentDescription = null,
                        tint = Color.White,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "$volumePercent%",
                        color = Color.White,
                        fontWeight = FontWeight.Bold,
                        fontSize = 16.sp
                    )
                }
            }
        }

        // Double Tap Seek Notice
        seekNoticeText?.let { text ->
            LaunchedEffect(text) {
                delay(700)
                seekNoticeText = null
            }
            Surface(
                shape = RoundedCornerShape(16.dp),
                color = OverlayDark,
                modifier = Modifier.align(Alignment.Center)
            ) {
                Text(
                    text = text,
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    fontSize = 20.sp,
                    modifier = Modifier.padding(horizontal = 20.dp, vertical = 12.dp)
                )
            }
        }

        // Bottom Controls Overlay
        AnimatedVisibility(
            visible = controlsVisible,
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
                        .padding(horizontal = 16.dp, vertical = 10.dp)
                ) {
                    // Seekbar & Time Row (if not a pure live stream without duration)
                    if (!isLiveStream || duration > 0) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = formatMillis(currentPosition),
                                style = MaterialTheme.typography.bodySmall.copy(
                                    color = TextPrimary,
                                    fontWeight = FontWeight.SemiBold
                                )
                            )

                            Slider(
                                value = if (duration > 0) currentPosition.toFloat() / duration else 0f,
                                onValueChange = { fraction ->
                                    currentPosition = (fraction * duration).toLong()
                                },
                                onValueChangeFinished = {
                                    exoPlayer.seekTo(currentPosition)
                                },
                                colors = SliderDefaults.colors(
                                    thumbColor = AccentBlue,
                                    activeTrackColor = AccentBlue,
                                    inactiveTrackColor = Color.White.copy(alpha = 0.25f)
                                ),
                                modifier = Modifier
                                    .weight(1f)
                                    .padding(horizontal = 8.dp)
                            )

                            Text(
                                text = formatMillis(duration),
                                style = MaterialTheme.typography.bodySmall.copy(
                                    color = TextSecondary,
                                    fontWeight = FontWeight.Normal
                                )
                            )
                        }
                    } else {
                        // Live Stream Indicator Bar
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                text = "🔴 Canlı Yayın Akışı (${StreamManager.inferStreamType(item.uriString)})",
                                color = AccentRed,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                text = if (bufferMode == "LOW_LATENCY") "⚡ Düşük Gecikme" else "🛡️ Kararlı Tampon",
                                color = AccentCyan,
                                fontSize = 11.sp
                            )
                        }
                    }

                    // Action Buttons Row
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            // Aspect ratio mode toggle
                            IconButton(
                                onClick = {
                                    resizeMode = if (resizeMode == AspectRatioFrameLayout.RESIZE_MODE_FIT) {
                                        AspectRatioFrameLayout.RESIZE_MODE_ZOOM
                                    } else {
                                        AspectRatioFrameLayout.RESIZE_MODE_FIT
                                    }
                                }
                            ) {
                                Icon(
                                    imageVector = Icons.Default.FitScreen,
                                    contentDescription = "Görünüm Modu",
                                    tint = if (resizeMode == AspectRatioFrameLayout.RESIZE_MODE_ZOOM) AccentCyan else Color.White
                                )
                            }

                            // Snapshot / Anlık Görüntü Yakala
                            IconButton(
                                onClick = {
                                    playerViewRef?.let { pv ->
                                        captureVideoFrame(context, pv) { bmp ->
                                            if (bmp != null) {
                                                saveBitmapToGallery(context, bmp)
                                            } else {
                                                Toast.makeText(context, "Kare yakalanamadı", Toast.LENGTH_SHORT).show()
                                            }
                                        }
                                    }
                                }
                            ) {
                                Icon(
                                    imageVector = Icons.Default.CameraAlt,
                                    contentDescription = "Anlık Kareyi Kaydet",
                                    tint = Color.White
                                )
                            }

                            // Quality Selector Button
                            Box {
                                Surface(
                                    shape = RoundedCornerShape(8.dp),
                                    color = if (selectedQualityLabel != "Otomatik") AccentBlue else DarkSurface,
                                    modifier = Modifier.padding(horizontal = 4.dp)
                                ) {
                                    Row(
                                        verticalAlignment = Alignment.CenterVertically,
                                        modifier = Modifier
                                            .clickable { showQualityMenu = true }
                                            .padding(horizontal = 8.dp, vertical = 6.dp)
                                    ) {
                                        Icon(
                                            imageVector = Icons.Default.HighQuality,
                                            contentDescription = "Kalite",
                                            tint = Color.White,
                                            modifier = Modifier.size(16.dp)
                                        )
                                        Spacer(modifier = Modifier.width(4.dp))
                                        Text(
                                            text = selectedQualityLabel,
                                            color = Color.White,
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.Bold
                                        )
                                    }
                                }

                                DropdownMenu(
                                    expanded = showQualityMenu,
                                    onDismissRequest = { showQualityMenu = false }
                                ) {
                                    val qualities = listOf(
                                        "Otomatik" to (0 to 0),
                                        "1080p (Full HD)" to (1920 to 1080),
                                        "720p (HD)" to (1280 to 720),
                                        "480p (SD)" to (854 to 480),
                                        "360p (Düşük)" to (640 to 360)
                                    )
                                    qualities.forEach { (label, dim) ->
                                        DropdownMenuItem(
                                            text = {
                                                Text(
                                                    text = label,
                                                    fontWeight = if (selectedQualityLabel == label) FontWeight.Bold else FontWeight.Normal,
                                                    color = if (selectedQualityLabel == label) AccentBlue else Color.White
                                                )
                                            },
                                            onClick = {
                                                selectedQualityLabel = label
                                                val (w, h) = dim
                                                val params = if (w == 0 && h == 0) {
                                                    exoPlayer.trackSelectionParameters.buildUpon()
                                                        .clearVideoSizeConstraints()
                                                        .build()
                                                } else {
                                                    exoPlayer.trackSelectionParameters.buildUpon()
                                                        .setMaxVideoSize(w, h)
                                                        .build()
                                                }
                                                exoPlayer.trackSelectionParameters = params
                                                showQualityMenu = false
                                                Toast.makeText(context, "Kalite: $label", Toast.LENGTH_SHORT).show()
                                            }
                                        )
                                    }
                                }
                            }

                            // Video Trim button (only if not live)
                            if (!isLiveStream && onTrimClicked != null) {
                                IconButton(onClick = { onTrimClicked.invoke(duration) }) {
                                    Icon(
                                        imageVector = Icons.Default.ContentCut,
                                        contentDescription = "Videoyu Kırp",
                                        tint = Color.White
                                    )
                                }
                            }
                        }

                        // Playback center controls
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(16.dp)
                        ) {
                            if (!isLiveStream) {
                                IconButton(
                                    onClick = {
                                        val target = (exoPlayer.currentPosition - 10000).coerceAtLeast(0L)
                                        exoPlayer.seekTo(target)
                                        currentPosition = target
                                    }
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.FastRewind,
                                        contentDescription = "-10 sn",
                                        tint = Color.White,
                                        modifier = Modifier.size(28.dp)
                                    )
                                }
                            }

                            Surface(
                                shape = CircleShape,
                                color = AccentBlue,
                                modifier = Modifier.size(48.dp)
                            ) {
                                IconButton(
                                    onClick = {
                                        if (isPlaying) {
                                            exoPlayer.pause()
                                        } else {
                                            if (exoPlayer.playbackState == Player.STATE_ENDED) {
                                                exoPlayer.seekTo(0)
                                            }
                                            exoPlayer.play()
                                        }
                                    }
                                ) {
                                    Icon(
                                        imageVector = if (isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow,
                                        contentDescription = if (isPlaying) "Duraklat" else "Oynat",
                                        tint = Color.White,
                                        modifier = Modifier.size(28.dp)
                                    )
                                }
                            }

                            if (!isLiveStream) {
                                IconButton(
                                    onClick = {
                                        val target = (exoPlayer.currentPosition + 10000).coerceAtMost(duration)
                                        exoPlayer.seekTo(target)
                                        currentPosition = target
                                    }
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.FastForward,
                                        contentDescription = "+10 sn",
                                        tint = Color.White,
                                        modifier = Modifier.size(28.dp)
                                    )
                                }
                            } else {
                                // Reconnect button for live stream
                                IconButton(
                                    onClick = {
                                        exoPlayer.seekToDefaultPosition()
                                        exoPlayer.prepare()
                                        exoPlayer.play()
                                        Toast.makeText(context, "Canlı akış yenilendi", Toast.LENGTH_SHORT).show()
                                    }
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.Refresh,
                                        contentDescription = "Yenile",
                                        tint = Color.White,
                                        modifier = Modifier.size(28.dp)
                                    )
                                }
                            }
                        }

                        // Speed selector (only for regular video files)
                        if (!isLiveStream) {
                            Box {
                                Surface(
                                    shape = RoundedCornerShape(8.dp),
                                    color = DarkSurface,
                                    modifier = Modifier.padding(4.dp)
                                ) {
                                    IconButton(onClick = { showSpeedMenu = true }) {
                                        Text(
                                            text = "${playbackSpeed}x",
                                            color = AccentBlue,
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 13.sp
                                        )
                                    }
                                }

                                DropdownMenu(
                                    expanded = showSpeedMenu,
                                    onDismissRequest = { showSpeedMenu = false }
                                ) {
                                    listOf(0.5f, 0.75f, 1.0f, 1.25f, 1.5f, 2.0f).forEach { speed ->
                                        DropdownMenuItem(
                                            text = { Text("${speed}x") },
                                            onClick = {
                                                playbackSpeed = speed
                                                exoPlayer.playbackParameters = PlaybackParameters(speed)
                                                showSpeedMenu = false
                                            }
                                        )
                                    }
                                }
                            }
                        } else {
                            Spacer(modifier = Modifier.size(40.dp))
                        }
                    }
                }
            }
        }
    }
}

private fun captureVideoFrame(context: Context, playerView: PlayerView, onCaptured: (Bitmap?) -> Unit) {
    val surfaceView = playerView.videoSurfaceView as? SurfaceView
    if (surfaceView != null && surfaceView.holder.surface.isValid) {
        val width = surfaceView.width
        val height = surfaceView.height
        if (width > 0 && height > 0) {
            val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
            val handler = Handler(Looper.getMainLooper())
            try {
                PixelCopy.request(surfaceView, bitmap, { copyResult ->
                    if (copyResult == PixelCopy.SUCCESS) {
                        onCaptured(bitmap)
                    } else {
                        onCaptured(null)
                    }
                }, handler)
                return
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    val textureView = playerView.videoSurfaceView as? TextureView
    onCaptured(textureView?.bitmap)
}

private fun saveBitmapToGallery(context: Context, bitmap: Bitmap) {
    try {
        val filename = "Canli_Kare_${System.currentTimeMillis()}.jpg"
        val values = ContentValues().apply {
            put(MediaStore.Images.Media.DISPLAY_NAME, filename)
            put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg")
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/MediaViewer")
                put(MediaStore.Images.Media.IS_PENDING, 1)
            }
        }
        val uri = context.contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
        if (uri != null) {
            context.contentResolver.openOutputStream(uri)?.use { stream ->
                bitmap.compress(Bitmap.CompressFormat.JPEG, 95, stream)
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                values.clear()
                values.put(MediaStore.Images.Media.IS_PENDING, 0)
                context.contentResolver.update(uri, values, null, null)
            }
            Toast.makeText(context, "📸 Canlı yayın karesi kaydedildi!", Toast.LENGTH_SHORT).show()
        }
    } catch (e: Exception) {
        e.printStackTrace()
        Toast.makeText(context, "Kare kaydedilemedi: ${e.message}", Toast.LENGTH_SHORT).show()
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
