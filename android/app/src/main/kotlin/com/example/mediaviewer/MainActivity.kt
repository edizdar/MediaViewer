package com.example.mediaviewer

import android.app.Activity
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.IntentSenderRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.animation.Crossfade
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.ui.Modifier
import android.provider.MediaStore
import androidx.lifecycle.lifecycleScope
import com.example.mediaviewer.data.DeleteRequestResult
import com.example.mediaviewer.model.MediaItem
import com.example.mediaviewer.ui.gallery.GalleryScreen
import com.example.mediaviewer.ui.theme.MediaViewerTheme
import com.example.mediaviewer.ui.viewmodel.MediaViewModel
import com.example.mediaviewer.ui.viewer.MediaViewerScreen
import com.example.mediaviewer.util.LanguageManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

class MainActivity : ComponentActivity() {

    private val viewModel: MediaViewModel by viewModels()

    private val deleteLauncher: ActivityResultLauncher<IntentSenderRequest> =
        registerForActivityResult(ActivityResultContracts.StartIntentSenderForResult()) { result ->
            val item = viewModel.pendingDeleteItem
            viewModel.pendingDeleteItem = null

            if (item != null) {
                if (result.resultCode == Activity.RESULT_OK) {
                    if (Build.VERSION.SDK_INT == Build.VERSION_CODES.Q) {
                        viewModel.executeDeleteAfterPermission(this@MainActivity, item) { success ->
                            if (success) {
                                Toast.makeText(this@MainActivity, getString(R.string.delete_success), Toast.LENGTH_SHORT).show()
                            } else {
                                Toast.makeText(this@MainActivity, getString(R.string.delete_failed), Toast.LENGTH_SHORT).show()
                            }
                        }
                    } else {
                        // On Android 11+ (API 30+), MediaStore.createDeleteRequest automatically removes the file upon user consent
                        viewModel.onItemDeleted(this@MainActivity, item)
                        Toast.makeText(this@MainActivity, getString(R.string.delete_success), Toast.LENGTH_SHORT).show()
                    }
                } else if (result.resultCode == Activity.RESULT_CANCELED) {
                    // User explicitly cancelled or denied the system confirmation prompt
                } else {
                    // Custom OEM result codes (Realme UI, ColorOS, MIUI)
                    lifecycleScope.launch {
                        val exists = withContext(Dispatchers.IO) {
                            try {
                                val p = item.path
                                if (p != null && File(p).exists()) {
                                    true
                                } else {
                                    val canonical = viewModel.repository.findCanonicalMediaStoreUri(this@MainActivity, item) ?: item.uri
                                    val cursor = contentResolver.query(canonical, arrayOf(MediaStore.MediaColumns._ID), null, null, null)
                                    val count = cursor?.count ?: 0
                                    cursor?.close()
                                    count > 0
                                }
                            } catch (_: Exception) {
                                false
                            }
                        }
                        if (!exists) {
                            viewModel.onItemDeleted(this@MainActivity, item)
                            Toast.makeText(this@MainActivity, getString(R.string.delete_success), Toast.LENGTH_SHORT).show()
                        } else {
                            Toast.makeText(this@MainActivity, getString(R.string.delete_failed), Toast.LENGTH_SHORT).show()
                        }
                    }
                }
            }
        }

    private fun deleteMediaItemWithPermission(itemToDelete: MediaItem) {
        lifecycleScope.launch {
            when (val result = viewModel.requestDeleteItem(this@MainActivity, itemToDelete)) {
                is DeleteRequestResult.Success -> {
                    viewModel.onItemDeleted(this@MainActivity, itemToDelete)
                    Toast.makeText(this@MainActivity, getString(R.string.delete_success), Toast.LENGTH_SHORT).show()
                }
                is DeleteRequestResult.NeedsUserConsent -> {
                    viewModel.pendingDeleteItem = itemToDelete
                    try {
                        deleteLauncher.launch(
                            IntentSenderRequest.Builder(result.intentSender).build()
                        )
                    } catch (e: Exception) {
                        e.printStackTrace()
                        viewModel.pendingDeleteItem = null
                        Toast.makeText(this@MainActivity, getString(R.string.delete_failed), Toast.LENGTH_SHORT).show()
                    }
                }
                is DeleteRequestResult.Failed -> {
                    Toast.makeText(this@MainActivity, getString(R.string.delete_failed), Toast.LENGTH_SHORT).show()
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R && !com.example.mediaviewer.util.SettingsManager.hasAllFilesAccess()) {
                        android.app.AlertDialog.Builder(this@MainActivity)
                            .setTitle(getString(R.string.all_files_permission_title))
                            .setMessage(getString(R.string.all_files_permission_desc))
                            .setPositiveButton(getString(R.string.all_files_permission_needed)) { _, _ ->
                                com.example.mediaviewer.util.SettingsManager.openAllFilesAccessSettings(this@MainActivity)
                            }
                            .setNegativeButton(android.R.string.cancel, null)
                            .show()
                    }
                }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        LanguageManager.init(this)
        LanguageManager.applyLocale(this, LanguageManager.getSavedLanguage(this))
        com.example.mediaviewer.util.SettingsManager.init(this)

        enableEdgeToEdge(
            statusBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT),
            navigationBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT)
        )

        handleIntent(intent)

        setContent {
            val currentLang by LanguageManager.currentLanguageState

            key(currentLang) {
                MediaViewerTheme {
                    Surface(
                        modifier = Modifier.fillMaxSize(),
                        color = MaterialTheme.colorScheme.background
                    ) {
                        val viewerState by viewModel.viewerState.collectAsState()

                        Crossfade(
                            targetState = viewerState,
                            label = "screen_transition"
                        ) { state ->
                            if (state != null) {
                                key(state.items.size) {
                                    MediaViewerScreen(
                                        items = state.items,
                                        initialIndex = state.initialIndex,
                                        onBack = {
                                            viewModel.closeViewer()
                                            if (state.isExternal) {
                                                finish()
                                            }
                                        },
                                        onDelete = { itemToDelete ->
                                            deleteMediaItemWithPermission(itemToDelete)
                                        },
                                        onModified = {
                                            viewModel.refreshAfterEdit(this@MainActivity)
                                        }
                                    )
                                }
                            } else {
                                GalleryScreen(
                                    viewModel = viewModel,
                                    onItemClick = { items, index ->
                                        viewModel.openMediaItem(items, index)
                                    }
                                )
                            }
                        }
                    }
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIntent(intent)
    }

    private fun handleIntent(intent: Intent?) {
        val uri = intent?.data
        if (intent?.action == Intent.ACTION_VIEW && uri != null) {
            viewModel.openExternalUri(this, uri)
        }
    }
}
