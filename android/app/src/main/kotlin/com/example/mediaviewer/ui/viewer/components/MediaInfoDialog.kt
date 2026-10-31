package com.example.mediaviewer.ui.viewer.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.mediaviewer.R
import com.example.mediaviewer.model.MediaItem
import com.example.mediaviewer.model.MediaType
import com.example.mediaviewer.ui.theme.AccentBlue
import com.example.mediaviewer.ui.theme.DarkBorder
import com.example.mediaviewer.ui.theme.DarkSurface
import com.example.mediaviewer.ui.theme.TextMuted
import com.example.mediaviewer.ui.theme.TextPrimary
import com.example.mediaviewer.ui.theme.TextSecondary

@Composable
fun MediaInfoDialog(
    item: MediaItem,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = DarkSurface,
        shape = RoundedCornerShape(16.dp),
        title = {
            Text(
                text = stringResource(R.string.file_info),
                style = MaterialTheme.typography.titleMedium.copy(
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary
                )
            )
        },
        text = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                InfoRow(label = stringResource(R.string.file_name), value = item.name)
                HorizontalDivider(color = DarkBorder, thickness = 0.5.dp)

                InfoRow(label = stringResource(R.string.file_size), value = item.formattedSize)
                HorizontalDivider(color = DarkBorder, thickness = 0.5.dp)

                InfoRow(label = stringResource(R.string.file_mime), value = item.mimeType)
                HorizontalDivider(color = DarkBorder, thickness = 0.5.dp)

                if (item.mediaType == MediaType.IMAGE || item.mediaType == MediaType.VIDEO) {
                    if (item.resolutionText.isNotEmpty()) {
                        InfoRow(label = stringResource(R.string.file_resolution), value = item.resolutionText)
                        HorizontalDivider(color = DarkBorder, thickness = 0.5.dp)
                    }
                }

                if (item.mediaType == MediaType.VIDEO || item.mediaType == MediaType.AUDIO) {
                    if (item.formattedDuration.isNotEmpty()) {
                        InfoRow(label = stringResource(R.string.file_duration), value = item.formattedDuration)
                        HorizontalDivider(color = DarkBorder, thickness = 0.5.dp)
                    }
                }

                InfoRow(label = stringResource(R.string.file_date), value = item.formattedDate)

                if (!item.path.isNullOrEmpty()) {
                    HorizontalDivider(color = DarkBorder, thickness = 0.5.dp)
                    InfoRow(label = stringResource(R.string.file_path), value = item.path)
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text(
                    text = stringResource(R.string.close),
                    color = AccentBlue,
                    fontWeight = FontWeight.SemiBold
                )
            }
        }
    )
}

@Composable
private fun InfoRow(label: String, value: String) {
    Column {
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall.copy(
                color = TextMuted,
                fontSize = 11.sp
            )
        )
        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium.copy(
                color = TextPrimary,
                fontWeight = FontWeight.Medium
            )
        )
    }
}
