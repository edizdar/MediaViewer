package com.example.mediaviewer.ui.gallery

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Audiotrack
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.FolderOpen
import androidx.compose.material.icons.filled.Image
import androidx.compose.material.icons.filled.Language
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Security
import androidx.compose.material.icons.filled.Videocam
import com.example.mediaviewer.ui.dialogs.LanguageSelectionDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.ScrollableTabRow
import androidx.compose.material3.Surface
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.core.content.ContextCompat
import android.widget.Toast
import com.example.mediaviewer.BuildConfig
import com.example.mediaviewer.util.AppUpdateInfo
import com.example.mediaviewer.util.UpdateChecker
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import android.graphics.Bitmap
import androidx.compose.foundation.Image
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.res.painterResource
import coil.request.videoFrameMillis
import com.example.mediaviewer.util.ThumbnailLoader
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.example.mediaviewer.R
import com.example.mediaviewer.model.MediaItem
import com.example.mediaviewer.model.MediaType
import com.example.mediaviewer.model.MediaTypeFilter
import com.example.mediaviewer.ui.theme.AccentAmber
import com.example.mediaviewer.ui.theme.AccentBlue
import com.example.mediaviewer.ui.theme.AccentBlueLight
import com.example.mediaviewer.ui.theme.AccentCyan
import com.example.mediaviewer.ui.theme.ChipSelected
import com.example.mediaviewer.ui.theme.ChipUnselected
import com.example.mediaviewer.ui.theme.DarkBackground
import com.example.mediaviewer.ui.theme.DarkSurface
import com.example.mediaviewer.ui.theme.DarkSurfaceElevated
import com.example.mediaviewer.ui.theme.TextMuted
import com.example.mediaviewer.ui.theme.TextPrimary
import com.example.mediaviewer.ui.theme.TextSecondary
import com.example.mediaviewer.ui.viewmodel.MediaViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GalleryScreen(
    viewModel: MediaViewModel,
    onItemClick: (items: List<MediaItem>, index: Int) -> Unit
) {
    val context = LocalContext.current
    val state by viewModel.galleryState.collectAsState()

    // Permission launcher
    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) { results ->
        val allGranted = results.values.all { it }
        viewModel.updatePermissionStatus(allGranted, context)
    }

    // SAF Document Picker launcher ("Dosya Aç")
    val filePickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) {
            viewModel.openExternalUri(context, uri)
        }
    }

    // Check permissions on start
    LaunchedEffect(Unit) {
        val hasPerms = checkMediaPermissions(context)
        viewModel.updatePermissionStatus(hasPerms, context)
    }

    var showLanguageDialog by remember { mutableStateOf(false) }
    var updateInfo by remember { mutableStateOf<AppUpdateInfo?>(null) }
    var showUpdateBanner by remember { mutableStateOf(false) }
    val coroutineScope = rememberCoroutineScope()

    // Automatic silent background update check (2.5s after launch)
    LaunchedEffect(Unit) {
        delay(2500)
        try {
            val info = UpdateChecker.checkForUpdates(BuildConfig.VERSION_NAME)
            if (info != null && info.isNewer) {
                updateInfo = info
                showUpdateBanner = true
            }
        } catch (_: Exception) {}
    }

    Scaffold(
        containerColor = DarkBackground,
        topBar = {
            TopAppBar(
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = DarkSurface,
                    titleContentColor = TextPrimary
                ),
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Image(
                            painter = painterResource(R.drawable.app_logo),
                            contentDescription = "Media Viewer Logo",
                            modifier = Modifier
                                .size(36.dp)
                                .clip(RoundedCornerShape(8.dp))
                        )
                        Spacer(modifier = Modifier.width(10.dp))
                        Column {
                            Text(
                                text = stringResource(R.string.app_name),
                                style = MaterialTheme.typography.titleMedium.copy(
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 18.sp
                                )
                            )
                            if (state.mediaList.isNotEmpty()) {
                                Text(
                                    text = stringResource(R.string.media_count_format, state.mediaList.size),
                                    style = MaterialTheme.typography.bodySmall.copy(
                                        color = TextSecondary,
                                        fontSize = 11.sp
                                    )
                                )
                            }
                        }
                    }
                },
                actions = {
                    IconButton(onClick = { showLanguageDialog = true }) {
                        Icon(
                            imageVector = Icons.Default.Language,
                            contentDescription = stringResource(R.string.language),
                            tint = TextSecondary
                        )
                    }
                    IconButton(
                        onClick = {
                            filePickerLauncher.launch(
                                arrayOf("image/*", "video/*", "audio/*", "*/*")
                            )
                        }
                    ) {
                        Icon(
                            imageVector = Icons.Default.FolderOpen,
                            contentDescription = stringResource(R.string.open_file),
                            tint = AccentBlue
                        )
                    }
                    IconButton(onClick = { viewModel.loadMedia(context) }) {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = stringResource(R.string.refresh),
                            tint = TextSecondary
                        )
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // Update notification banner (when new version published on GitHub)
            if (showUpdateBanner && updateInfo != null) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 12.dp, vertical = 6.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF1E3A8A)),
                    shape = RoundedCornerShape(10.dp)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 12.dp, vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = stringResource(R.string.update_available_banner, updateInfo!!.tagName),
                            color = Color.White,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.weight(1f)
                        )
                        TextButton(
                            onClick = {
                                UpdateChecker.openDownloadUrl(context, updateInfo!!.downloadUrl)
                            }
                        ) {
                            Text(
                                text = stringResource(R.string.update_download),
                                color = AccentCyan,
                                fontWeight = FontWeight.Bold
                            )
                        }
                        IconButton(
                            onClick = { showUpdateBanner = false },
                            modifier = Modifier.size(28.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Close,
                                contentDescription = stringResource(R.string.close),
                                tint = Color.White.copy(alpha = 0.7f),
                                modifier = Modifier.size(16.dp)
                            )
                        }
                    }
                }
            }

            // Filter Tabs
            FilterTabBar(
                currentFilter = state.currentFilter,
                onFilterSelected = { filter ->
                    viewModel.setFilter(filter, context)
                }
            )

            // Content
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 4.dp)
            ) {
                when {
                    !state.hasPermission -> {
                        PermissionRequiredContent(
                            onRequestPermission = {
                                requestRequiredPermissions(permissionLauncher)
                            },
                            onOpenFile = {
                                filePickerLauncher.launch(arrayOf("*/*"))
                            }
                        )
                    }
                    state.isLoading -> {
                        Box(
                            modifier = Modifier.fillMaxSize(),
                            contentAlignment = Alignment.Center
                        ) {
                            CircularProgressIndicator(color = AccentBlue)
                        }
                    }
                    state.mediaList.isEmpty() -> {
                        EmptyGalleryContent(
                            onOpenFile = {
                                filePickerLauncher.launch(arrayOf("*/*"))
                            }
                        )
                    }
                    else -> {
                        LazyVerticalGrid(
                            columns = GridCells.Adaptive(minSize = 110.dp),
                            contentPadding = PaddingValues(4.dp),
                            horizontalArrangement = Arrangement.spacedBy(4.dp),
                            verticalArrangement = Arrangement.spacedBy(4.dp),
                            modifier = Modifier.fillMaxSize()
                        ) {
                            itemsIndexed(
                                items = state.mediaList,
                                key = { _, item -> item.id }
                            ) { index, item ->
                                MediaThumbnailItem(
                                    item = item,
                                    onClick = { onItemClick(state.mediaList, index) }
                                )
                            }
                        }
                    }
                }
            }
        }

        if (showLanguageDialog) {
            LanguageSelectionDialog(
                onDismiss = { showLanguageDialog = false },
                onLanguageSelected = {
                    showLanguageDialog = false
                    viewModel.loadMedia(context)
                },
                onCheckUpdates = {
                    coroutineScope.launch {
                        Toast.makeText(context, context.getString(R.string.checking_updates), Toast.LENGTH_SHORT).show()
                        val info = UpdateChecker.checkForUpdates(BuildConfig.VERSION_NAME)
                        if (info != null && info.isNewer) {
                            updateInfo = info
                            showUpdateBanner = true
                        } else if (info != null) {
                            Toast.makeText(context, context.getString(R.string.already_latest_version), Toast.LENGTH_LONG).show()
                        } else {
                            Toast.makeText(context, context.getString(R.string.update_check_failed), Toast.LENGTH_LONG).show()
                        }
                    }
                }
            )
        }
    }
}

@Composable
private fun FilterTabBar(
    currentFilter: MediaTypeFilter,
    onFilterSelected: (MediaTypeFilter) -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(DarkSurface)
            .padding(horizontal = 12.dp, vertical = 6.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        val filters = listOf(
            MediaTypeFilter.ALL to stringResource(R.string.tab_all),
            MediaTypeFilter.PHOTOS to stringResource(R.string.tab_photos),
            MediaTypeFilter.VIDEOS to stringResource(R.string.tab_videos),
            MediaTypeFilter.AUDIO to stringResource(R.string.tab_audio)
        )

        filters.forEach { (filter, label) ->
            val isSelected = currentFilter == filter
            FilterChip(
                selected = isSelected,
                onClick = { onFilterSelected(filter) },
                label = {
                    Text(
                        text = label,
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
                shape = RoundedCornerShape(16.dp)
            )
        }
    }
}

@Composable
private fun MediaThumbnailItem(
    item: MediaItem,
    onClick: () -> Unit
) {
    val context = LocalContext.current
    Box(
        modifier = Modifier
            .aspectRatio(1f)
            .clip(RoundedCornerShape(8.dp))
            .background(DarkSurfaceElevated)
            .clickable(onClick = onClick)
    ) {
        when (item.mediaType) {
            MediaType.IMAGE -> {
                AsyncImage(
                    model = ImageRequest.Builder(context)
                        .data(item.uri)
                        .crossfade(true)
                        .build(),
                    contentDescription = item.name,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize()
                )
            }
            MediaType.VIDEO -> {
                VideoThumbnailView(item = item)

                // Video duration & play icon badge
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(
                            Brush.verticalGradient(
                                colors = listOf(
                                    Color.Black.copy(alpha = 0.35f),
                                    Color.Transparent,
                                    Color.Black.copy(alpha = 0.75f)
                                )
                            )
                        )
                )

                // Small Play icon at top-left
                Surface(
                    shape = CircleShape,
                    color = Color.Black.copy(alpha = 0.6f),
                    modifier = Modifier
                        .padding(6.dp)
                        .size(24.dp)
                        .align(Alignment.TopStart)
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            imageVector = Icons.Default.PlayArrow,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                }

                // Duration at bottom-right
                if (item.formattedDuration.isNotEmpty()) {
                    Surface(
                        shape = RoundedCornerShape(4.dp),
                        color = Color.Black.copy(alpha = 0.75f),
                        modifier = Modifier
                            .padding(6.dp)
                            .align(Alignment.BottomEnd)
                    ) {
                        Text(
                            text = item.formattedDuration,
                            color = Color.White,
                            style = MaterialTheme.typography.bodySmall.copy(
                                fontSize = 10.sp,
                                fontWeight = FontWeight.SemiBold
                            ),
                            modifier = Modifier.padding(horizontal = 5.dp, vertical = 2.dp)
                        )
                    }
                }
            }
            MediaType.AUDIO -> {
                // Audio tile
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(
                            Brush.linearGradient(
                                colors = listOf(DarkSurfaceElevated, AccentCyan.copy(alpha = 0.25f))
                            )
                        )
                        .padding(8.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Surface(
                            shape = CircleShape,
                            color = AccentCyan.copy(alpha = 0.2f),
                            modifier = Modifier.size(40.dp)
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(
                                    imageVector = Icons.Default.Audiotrack,
                                    contentDescription = null,
                                    tint = AccentCyan,
                                    modifier = Modifier.size(24.dp)
                                )
                            }
                        }
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = item.name,
                            style = MaterialTheme.typography.bodySmall.copy(
                                fontSize = 11.sp,
                                color = TextPrimary
                            ),
                            maxLines = 2,
                            overflow = TextOverflow.Ellipsis,
                            textAlign = TextAlign.Center
                        )
                        if (item.formattedDuration.isNotEmpty()) {
                            Spacer(modifier = Modifier.height(2.dp))
                            Text(
                                text = item.formattedDuration,
                                style = MaterialTheme.typography.bodySmall.copy(
                                    fontSize = 10.sp,
                                    color = TextSecondary
                                )
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun VideoThumbnailView(item: MediaItem) {
    val context = LocalContext.current
    var bitmap by remember(item.uriString) { mutableStateOf<Bitmap?>(null) }

    LaunchedEffect(item.uriString) {
        bitmap = ThumbnailLoader.loadVideoThumbnail(context, item.uri)
    }

    val currentBmp = bitmap
    if (currentBmp != null) {
        Image(
            bitmap = currentBmp.asImageBitmap(),
            contentDescription = item.name,
            contentScale = ContentScale.Crop,
            modifier = Modifier.fillMaxSize()
        )
    } else {
        AsyncImage(
            model = ImageRequest.Builder(context)
                .data(item.uri)
                .videoFrameMillis(1000)
                .crossfade(true)
                .build(),
            contentDescription = item.name,
            contentScale = ContentScale.Crop,
            modifier = Modifier.fillMaxSize()
        )
    }
}

@Composable
private fun PermissionRequiredContent(
    onRequestPermission: () -> Unit,
    onOpenFile: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Surface(
            shape = CircleShape,
            color = AccentAmber.copy(alpha = 0.15f),
            modifier = Modifier.size(72.dp)
        ) {
            Box(contentAlignment = Alignment.Center) {
                Icon(
                    imageVector = Icons.Default.Security,
                    contentDescription = null,
                    tint = AccentAmber,
                    modifier = Modifier.size(36.dp)
                )
            }
        }
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = stringResource(R.string.permission_required_title),
            style = MaterialTheme.typography.titleMedium.copy(
                fontWeight = FontWeight.Bold,
                color = TextPrimary
            )
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = stringResource(R.string.permission_required_desc),
            style = MaterialTheme.typography.bodyMedium.copy(color = TextSecondary),
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(20.dp))
        Button(
            onClick = onRequestPermission,
            colors = ButtonDefaults.buttonColors(containerColor = AccentBlue)
        ) {
            Text(stringResource(R.string.grant_permission))
        }
        Spacer(modifier = Modifier.height(12.dp))
        Button(
            onClick = onOpenFile,
            colors = ButtonDefaults.buttonColors(containerColor = ChipUnselected)
        ) {
            Icon(Icons.Default.FolderOpen, contentDescription = null, tint = AccentBlueLight)
            Spacer(modifier = Modifier.width(8.dp))
            Text(stringResource(R.string.open_file), color = TextPrimary)
        }
    }
}

@Composable
private fun EmptyGalleryContent(
    onOpenFile: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Surface(
            shape = CircleShape,
            color = DarkSurfaceElevated,
            modifier = Modifier.size(64.dp)
        ) {
            Box(contentAlignment = Alignment.Center) {
                Icon(
                    imageVector = Icons.Default.Image,
                    contentDescription = null,
                    tint = TextMuted,
                    modifier = Modifier.size(32.dp)
                )
            }
        }
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = stringResource(R.string.no_media_found),
            style = MaterialTheme.typography.titleMedium.copy(
                fontWeight = FontWeight.Bold,
                color = TextPrimary
            )
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = stringResource(R.string.no_media_found_desc),
            style = MaterialTheme.typography.bodyMedium.copy(color = TextSecondary),
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(20.dp))
        Button(
            onClick = onOpenFile,
            colors = ButtonDefaults.buttonColors(containerColor = AccentBlue)
        ) {
            Icon(Icons.Default.FolderOpen, contentDescription = null)
            Spacer(modifier = Modifier.width(8.dp))
            Text(stringResource(R.string.open_file))
        }
    }
}

private fun checkMediaPermissions(context: Context): Boolean {
    return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        val img = ContextCompat.checkSelfPermission(context, Manifest.permission.READ_MEDIA_IMAGES)
        val vid = ContextCompat.checkSelfPermission(context, Manifest.permission.READ_MEDIA_VIDEO)
        val aud = ContextCompat.checkSelfPermission(context, Manifest.permission.READ_MEDIA_AUDIO)
        img == PackageManager.PERMISSION_GRANTED || vid == PackageManager.PERMISSION_GRANTED
    } else {
        val ext = ContextCompat.checkSelfPermission(context, Manifest.permission.READ_EXTERNAL_STORAGE)
        ext == PackageManager.PERMISSION_GRANTED
    }
}

private fun requestRequiredPermissions(
    launcher: androidx.activity.result.ActivityResultLauncher<Array<String>>
) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        launcher.launch(
            arrayOf(
                Manifest.permission.READ_MEDIA_IMAGES,
                Manifest.permission.READ_MEDIA_VIDEO,
                Manifest.permission.READ_MEDIA_AUDIO
            )
        )
    } else {
        launcher.launch(arrayOf(Manifest.permission.READ_EXTERNAL_STORAGE))
    }
}
