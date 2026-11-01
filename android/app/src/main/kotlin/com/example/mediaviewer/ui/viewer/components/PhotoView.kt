package com.example.mediaviewer.ui.viewer.components

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.gestures.rememberTransformableState
import androidx.compose.foundation.gestures.transformable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.IntSize
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.example.mediaviewer.model.MediaItem

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun PhotoView(
    item: MediaItem,
    rotation: Float = 0f,
    isFlipped: Boolean = false,
    onToggleControls: () -> Unit,
    onZoomChanged: (isZoomed: Boolean) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    var scale by remember { mutableFloatStateOf(1f) }
    var offset by remember { mutableStateOf(Offset.Zero) }
    var containerSize by remember { mutableStateOf(IntSize.Zero) }

    val transformableState = rememberTransformableState { zoomChange, panChange, _ ->
        val newScale = (scale * zoomChange).coerceIn(1f, 5f)
        scale = newScale
        val isZoomed = newScale > 1.05f
        onZoomChanged(isZoomed)

        if (isZoomed && containerSize.width > 0 && containerSize.height > 0) {
            val maxOffsetX = (containerSize.width * (scale - 1)) / 2f
            val maxOffsetY = (containerSize.height * (scale - 1)) / 2f
            offset = Offset(
                x = (offset.x + panChange.x * scale).coerceIn(-maxOffsetX, maxOffsetX),
                y = (offset.y + panChange.y * scale).coerceIn(-maxOffsetY, maxOffsetY)
            )
        } else {
            offset = Offset.Zero
        }
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .onSizeChanged { containerSize = it }
            .combinedClickable(
                interactionSource = remember { MutableInteractionSource() },
                indication = null,
                onClick = { onToggleControls() },
                onDoubleClick = {
                    if (scale > 1.05f) {
                        scale = 1f
                        offset = Offset.Zero
                        onZoomChanged(false)
                    } else {
                        scale = 2.5f
                        onZoomChanged(true)
                    }
                }
            )
            .transformable(
                state = transformableState,
                canPan = { scale > 1.05f }
            ),
        contentAlignment = Alignment.Center
    ) {
        AsyncImage(
            model = ImageRequest.Builder(context)
                .data(item.uri)
                .crossfade(true)
                .build(),
            contentDescription = item.name,
            contentScale = ContentScale.Fit,
            modifier = Modifier
                .fillMaxSize()
                .graphicsLayer {
                    scaleX = scale * (if (isFlipped) -1f else 1f)
                    scaleY = scale
                    rotationZ = rotation
                    translationX = offset.x
                    translationY = offset.y
                }
        )
    }
}
