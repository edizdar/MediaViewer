package com.example.mediaviewer.ui.dialogs

import androidx.compose.runtime.Composable

@Composable
fun LanguageSelectionDialog(
    onDismiss: () -> Unit,
    onLanguageSelected: (String) -> Unit,
    onCheckUpdates: (() -> Unit)? = null
) {
    SettingsDialog(
        onDismiss = onDismiss,
        onLanguageSelected = onLanguageSelected,
        onCheckUpdates = onCheckUpdates
    )
}
