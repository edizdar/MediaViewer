package com.example.mediaviewer.ui.viewmodel

import android.content.Context
import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.mediaviewer.data.DeleteRequestResult
import com.example.mediaviewer.data.MediaRepository
import com.example.mediaviewer.model.MediaItem
import com.example.mediaviewer.model.MediaTypeFilter
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class GalleryUiState(
    val mediaList: List<MediaItem> = emptyList(),
    val currentFilter: MediaTypeFilter = MediaTypeFilter.ALL,
    val isLoading: Boolean = false,
    val hasPermission: Boolean = false
)

data class ViewerUiState(
    val items: List<MediaItem> = emptyList(),
    val initialIndex: Int = 0,
    val isExternal: Boolean = false
)

class MediaViewModel(
    private val repository: MediaRepository = MediaRepository()
) : ViewModel() {

    private val _galleryState = MutableStateFlow(GalleryUiState())
    val galleryState: StateFlow<GalleryUiState> = _galleryState.asStateFlow()

    private val _viewerState = MutableStateFlow<ViewerUiState?>(null)
    val viewerState: StateFlow<ViewerUiState?> = _viewerState.asStateFlow()

    fun updatePermissionStatus(granted: Boolean, context: Context) {
        _galleryState.update { it.copy(hasPermission = granted) }
        if (granted) {
            loadMedia(context)
        }
    }

    fun setFilter(filter: MediaTypeFilter, context: Context) {
        _galleryState.update { it.copy(currentFilter = filter) }
        loadMedia(context)
    }

    fun loadMedia(context: Context) {
        viewModelScope.launch {
            _galleryState.update { it.copy(isLoading = true) }
            val currentFilter = _galleryState.value.currentFilter
            val items = repository.queryAllMedia(context, currentFilter)
            _galleryState.update { it.copy(mediaList = items, isLoading = false) }
        }
    }

    fun openMediaItem(items: List<MediaItem>, index: Int) {
        _viewerState.value = ViewerUiState(
            items = items,
            initialIndex = index.coerceIn(0, (items.size - 1).coerceAtLeast(0)),
            isExternal = false
        )
    }

    fun openExternalUri(context: Context, uri: Uri, onLoaded: () -> Unit = {}) {
        viewModelScope.launch {
            val item = repository.resolveUri(context, uri)
            val siblings = repository.getSiblings(context, item)
            val initialIndex = siblings.indexOfFirst { it.uriString == item.uriString }.let {
                if (it != -1) it else 0
            }
            _viewerState.value = ViewerUiState(
                items = siblings,
                initialIndex = initialIndex,
                isExternal = true
            )
            onLoaded()
        }
    }

    var pendingDeleteItem: MediaItem? = null

    fun closeViewer() {
        _viewerState.value = null
    }

    suspend fun requestDeleteItem(context: Context, item: MediaItem): DeleteRequestResult {
        return repository.deleteItem(context, item)
    }

    fun onItemDeleted(context: Context, item: MediaItem) {
        _viewerState.value?.let { cur ->
            val deletedIndex = cur.items.indexOfFirst { it.id == item.id || it.uriString == item.uriString }
            val newItems = cur.items.filterNot { it.id == item.id || it.uriString == item.uriString }
            if (newItems.isEmpty()) {
                _viewerState.value = null
            } else {
                val targetIndex = if (deletedIndex != -1) {
                    deletedIndex.coerceAtMost(newItems.size - 1)
                } else {
                    cur.initialIndex.coerceAtMost(newItems.size - 1)
                }
                _viewerState.value = cur.copy(items = newItems, initialIndex = targetIndex)
            }
        }
        loadMedia(context)
    }

    fun executeDeleteAfterPermission(context: Context, item: MediaItem, onDone: (Boolean) -> Unit) {
        viewModelScope.launch {
            val success = repository.directDelete(context, item)
            if (success) {
                onItemDeleted(context, item)
            }
            onDone(success)
        }
    }

    fun deleteMediaItem(context: Context, item: MediaItem, onDone: (Boolean) -> Unit) {
        viewModelScope.launch {
            when (val result = repository.deleteItem(context, item)) {
                is DeleteRequestResult.Success -> {
                    onItemDeleted(context, item)
                    onDone(true)
                }
                is DeleteRequestResult.NeedsUserConsent -> {
                    // Handled via Activity launcher
                    onDone(false)
                }
                is DeleteRequestResult.Failed -> {
                    onDone(false)
                }
            }
        }
    }

    fun refreshAfterEdit(context: Context) {
        loadMedia(context)
    }
}
