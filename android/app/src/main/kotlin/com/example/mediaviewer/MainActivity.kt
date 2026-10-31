package com.example.mediaviewer

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.animation.Crossfade
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.ui.Modifier
import com.example.mediaviewer.ui.gallery.GalleryScreen
import com.example.mediaviewer.ui.theme.MediaViewerTheme
import com.example.mediaviewer.ui.viewmodel.MediaViewModel
import com.example.mediaviewer.ui.viewer.MediaViewerScreen
import com.example.mediaviewer.util.LanguageManager

class MainActivity : ComponentActivity() {

    private val viewModel: MediaViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        LanguageManager.init(this)
        LanguageManager.applyLocale(this, LanguageManager.getSavedLanguage(this))

        enableEdgeToEdge()

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
                                        viewModel.deleteMediaItem(this@MainActivity, itemToDelete) { success ->
                                            if (success) {
                                                Toast.makeText(this@MainActivity, getString(R.string.delete_success), Toast.LENGTH_SHORT).show()
                                            } else {
                                                Toast.makeText(this@MainActivity, getString(R.string.delete_failed), Toast.LENGTH_SHORT).show()
                                            }
                                        }
                                    },
                                    onModified = {
                                        viewModel.refreshAfterEdit(this@MainActivity)
                                    }
                                )
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
