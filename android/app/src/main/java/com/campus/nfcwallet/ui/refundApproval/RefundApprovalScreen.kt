package com.campus.nfcwallet.ui.refundApproval

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

object RefundApprovalColors {
    val Background = Color(0xFF0F1923)
    val Surface = Color(0xFF1A2B3C)
    val Elevated = Color(0xFF243B50)
    val AccentBlue = Color(0xFF42A5F5)
    val AccentGreen = Color(0xFF66BB6A)
    val AccentRed = Color(0xFFEF5350)
    val AccentAmber = Color(0xFFFFCA28)
    val TextPrimary = Color(0xFFF0F0F0)
    val TextSecondary = Color(0xFFB0BEC5)
    val TextDim = Color(0xFF607D8B)
    val Border = Color(0xFF37474F)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RefundApprovalScreen(
    state: RefundApprovalUiState,
    onApprove: (Int) -> Unit,
    onReject: (Int) -> Unit,
    onFilterChange: (String) -> Unit,
    onRefresh: () -> Unit,
    onDismissMessage: () -> Unit,
) {
    Scaffold(
        containerColor = RefundApprovalColors.Background,
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("退款申请审批", color = RefundApprovalColors.TextPrimary, fontSize = 17.sp, fontWeight = FontWeight.Bold)
                        Text("REFUND REQUEST APPROVAL", color = RefundApprovalColors.TextDim, fontSize = 10.sp, letterSpacing = 2.sp)
                    }
                },
                actions = {
                    IconButton(onClick = onRefresh) {
                        Icon(Icons.Default.Refresh, "刷新", tint = RefundApprovalColors.AccentBlue)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = RefundApprovalColors.Background),
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp),
        ) {
            // 筛选按钮
            FilterRow(currentFilter = state.filter, onFilterChange = onFilterChange)

            Spacer(modifier = Modifier.height(12.dp))

            // 列表
            if (state.isLoading) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(color = RefundApprovalColors.AccentBlue)
                }
            } else if (state.requests.isEmpty()) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text("暂无退款申请", color = RefundApprovalColors.TextDim, fontSize = 14.sp)
                }
            } else {
                LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    items(state.requests) { item ->
                        RefundRequestCard(
                            item = item,
                            isProcessing = state.isProcessing,
                            onApprove = { onApprove(item.id) },
                            onReject = { onReject(item.id) },
                        )
                    }
                }
            }
        }
    }

    // 消息提示
    if (state.successMessage != null) {
        AlertDialog(
            onDismissRequest = onDismissMessage,
            containerColor = RefundApprovalColors.Surface,
            title = { Text("操作成功", color = RefundApprovalColors.AccentGreen) },
            text = { Text(state.successMessage, color = RefundApprovalColors.TextPrimary) },
            confirmButton = {
                TextButton(onClick = onDismissMessage) {
                    Text("确定", color = RefundApprovalColors.AccentBlue)
                }
            },
        )
    }

    if (state.errorMessage != null) {
        AlertDialog(
            onDismissRequest = onDismissMessage,
            containerColor = RefundApprovalColors.Surface,
            title = { Text("错误", color = RefundApprovalColors.AccentRed) },
            text = { Text(state.errorMessage, color = RefundApprovalColors.TextPrimary) },
            confirmButton = {
                TextButton(onClick = onDismissMessage) {
                    Text("确定", color = RefundApprovalColors.AccentBlue)
                }
            },
        )
    }
}

@Composable
private fun FilterRow(currentFilter: String, onFilterChange: (String) -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        FilterChip(label = "待审批", value = "pending", current = currentFilter, onClick = onFilterChange)
        FilterChip(label = "已通过", value = "approved", current = currentFilter, onClick = onFilterChange)
        FilterChip(label = "已驳回", value = "rejected", current = currentFilter, onClick = onFilterChange)
        FilterChip(label = "全部", value = "all", current = currentFilter, onClick = onFilterChange)
    }
}

@Composable
private fun FilterChip(label: String, value: String, current: String, onClick: (String) -> Unit) {
    val isSelected = current == value
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(16.dp))
            .background(if (isSelected) RefundApprovalColors.AccentBlue else RefundApprovalColors.Surface)
            .border(1.dp, if (isSelected) RefundApprovalColors.AccentBlue else RefundApprovalColors.Border, RoundedCornerShape(16.dp))
            .clickable { onClick(value) }
            .padding(horizontal = 14.dp, vertical = 6.dp),
    ) {
        Text(
            text = label,
            color = if (isSelected) Color.White else RefundApprovalColors.TextSecondary,
            fontSize = 13.sp,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
        )
    }
}

@Composable
private fun RefundRequestCard(
    item: RefundRequestItem,
    isProcessing: Boolean,
    onApprove: () -> Unit,
    onReject: () -> Unit,
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, RefundApprovalColors.Border, RoundedCornerShape(12.dp))
            .background(RefundApprovalColors.Surface)
            .padding(16.dp),
    ) {
        Column {
            // 头部：申请人 + 金额
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column {
                    Text(item.requesterName, color = RefundApprovalColors.TextPrimary, fontSize = 15.sp, fontWeight = FontWeight.Bold)
                    if (item.cardUid != null) {
                        Text("卡号: ${item.cardUid}", color = RefundApprovalColors.TextDim, fontSize = 11.sp)
                    }
                }
                Text(
                    "¥${"%.2f".format(item.txnAmount)}",
                    color = RefundApprovalColors.AccentRed,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            // 原因
            Text("原因: ${item.reason}", color = RefundApprovalColors.TextSecondary, fontSize = 12.sp)

            Spacer(modifier = Modifier.height(4.dp))

            // 时间
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(
                    "申请: ${item.createdAt?.take(16)?.replace("T", " ") ?: "-"}",
                    color = RefundApprovalColors.TextDim,
                    fontSize = 11.sp,
                )
                val statusColor = when (item.status) {
                    "pending" -> RefundApprovalColors.AccentAmber
                    "approved" -> RefundApprovalColors.AccentGreen
                    "rejected" -> RefundApprovalColors.AccentRed
                    else -> RefundApprovalColors.TextDim
                }
                val statusLabel = when (item.status) {
                    "pending" -> "待审批"
                    "approved" -> "已通过"
                    "rejected" -> "已驳回"
                    else -> item.status
                }
                Text(statusLabel, color = statusColor, fontSize = 12.sp, fontWeight = FontWeight.Bold)
            }

            // 操作按钮（仅 pending 状态）
            if (item.status == "pending") {
                Spacer(modifier = Modifier.height(12.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Button(
                        onClick = onApprove,
                        enabled = !isProcessing,
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(8.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = RefundApprovalColors.AccentGreen,
                            contentColor = Color.White,
                        ),
                    ) {
                        Icon(Icons.Default.CheckCircle, null, modifier = Modifier.size(16.dp))
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("通过", fontSize = 13.sp, fontWeight = FontWeight.Bold)
                    }
                    OutlinedButton(
                        onClick = onReject,
                        enabled = !isProcessing,
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(8.dp),
                        colors = ButtonDefaults.outlinedButtonColors(
                            contentColor = RefundApprovalColors.AccentRed,
                        ),
                    ) {
                        Icon(Icons.Default.Close, null, modifier = Modifier.size(16.dp))
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("驳回", fontSize = 13.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
}
