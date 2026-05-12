package com.campus.nfcwallet.ui.refund

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.*
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.campus.nfcwallet.models.Transaction
import kotlinx.coroutines.delay

// ============================================================================
// 主题配色 — 深蓝 + 黑金 + 警告红（退款管理专用）
// ============================================================================
object RefundColors {
    val Background = Color(0xFF080C14)          // 最深背景
    val SurfaceDark = Color(0xFF0F1520)         // 卡片背景
    val SurfaceElevated = Color(0xFF161E2E)     // 悬浮面板
    val SurfaceSelected = Color(0xFF1A2540)     // 选中态
    val Gold = Color(0xFFFFD700)                // 金色强调
    val GoldSoft = Color(0xFFE6B800)            // 柔和金
    val GoldDim = Color(0xFF8C7200)             // 暗金
    val DangerRed = Color(0xFFFF3B3B)           // 警告红（退款状态）
    val DangerRedDim = Color(0xFFCC2020)        // 暗红
    val DangerRedBg = Color(0x33FF3B3B)         // 红色背景
    val TextPrimary = Color(0xFFF5F5F5)         // 主文字
    val TextSecondary = Color(0xFFB0B0B0)       // 次要文字
    val TextDim = Color(0xFF606878)             // 暗淡文字
    val SuccessGreen = Color(0xFF00E676)        // 成功绿
    val BorderGold = Color(0x44FFD700)          // 半透明金边
    val BorderRed = Color(0x44FF3B3B)           // 半透明红边
    val BlueTint = Color(0xFF1E88E5)            // 蓝色点缀
}

// ============================================================================
// 退款管理主界面
// ============================================================================
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RefundManagerScreen(
    state: RefundUiState,
    onTransactionSelected: (Transaction) -> Unit,
    onInitiateRefund: () -> Unit,
    onConfirmRefund: () -> Unit,
    onDismissRefundDialog: () -> Unit,
    onClearCardFilter: () -> Unit,
    onClearSelection: () -> Unit,
    onDismissError: () -> Unit,
    onDismissSuccess: () -> Unit,
    onLogout: () -> Unit = {},
) {
    Scaffold(
        containerColor = RefundColors.Background,
        topBar = {
            RefundTopBar(onLogout = onLogout)
        },
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
        ) {
            Column(
                modifier = Modifier.fillMaxSize(),
            ) {
                // NFC 感应提示区
                NfcScanCard(
                    cardUid = state.cardUid,
                    filterByCard = state.filterByCard,
                    onClearFilter = onClearCardFilter,
                )

                // 交易列表
                TransactionListSection(
                    transactions = state.transactions,
                    selectedTransaction = state.selectedTransaction,
                    isLoading = state.isLoadingList,
                    filterByCard = state.filterByCard,
                    onTransactionSelected = onTransactionSelected,
                    modifier = Modifier.weight(1f),
                )

                // 底部操作区（选中交易后显示）
                AnimatedVisibility(
                    visible = state.selectedTransaction != null,
                    enter = fadeIn() + expandVertically(),
                    exit = fadeOut() + shrinkVertically(),
                ) {
                    RefundActionBar(
                        transaction = state.selectedTransaction,
                        isProcessing = state.isProcessing,
                        onInitiateRefund = onInitiateRefund,
                        onCancel = onClearSelection,
                    )
                }
            }

            // 退款确认对话框
            if (state.showRefundDialog) {
                RefundConfirmDialog(
                    transaction = state.selectedTransaction,
                    onConfirm = onConfirmRefund,
                    onDismiss = onDismissRefundDialog,
                )
            }

            // 错误提示
            if (state.errorMessage != null) {
                Snackbar(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(16.dp),
                    containerColor = RefundColors.DangerRedBg,
                    contentColor = RefundColors.DangerRed,
                    action = {
                        TextButton(onClick = onDismissError) {
                            Text("关闭", color = RefundColors.Gold)
                        }
                    },
                ) {
                    Text(state.errorMessage)
                }
            }

            // 成功提示
            if (state.successMessage != null) {
                Snackbar(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(16.dp),
                    containerColor = Color(0xFF0A2E1A),
                    contentColor = RefundColors.SuccessGreen,
                    action = {
                        TextButton(onClick = onDismissSuccess) {
                            Text("关闭", color = RefundColors.Gold)
                        }
                    },
                ) {
                    Text(state.successMessage)
                }
            }

            // 处理中遮罩
            if (state.isProcessing) {
                ProcessingOverlay()
            }
        }
    }
}

// ============================================================================
// 顶部导航栏
// ============================================================================
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun RefundTopBar(onLogout: () -> Unit) {
    TopAppBar(
        title = {
            Column {
                Text(
                    text = "摊位售后与退款管理",
                    color = RefundColors.TextPrimary,
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp,
                    letterSpacing = 0.5.sp,
                )
                Text(
                    text = "BOOTH AFTER-SALES · REFUND TERMINAL",
                    color = RefundColors.TextDim,
                    fontSize = 10.sp,
                    letterSpacing = 2.sp,
                )
            }
        },
        navigationIcon = {
            Icon(
                imageVector = Icons.Filled.CurrencyExchange,
                contentDescription = null,
                tint = RefundColors.DangerRed,
                modifier = Modifier
                    .padding(start = 12.dp)
                    .size(24.dp),
            )
        },
        actions = {
            IconButton(onClick = onLogout) {
                Icon(
                    imageVector = Icons.Filled.Logout,
                    contentDescription = "退出",
                    tint = RefundColors.TextSecondary,
                )
            }
        },
        colors = TopAppBarDefaults.topAppBarColors(
            containerColor = RefundColors.SurfaceDark,
        ),
    )
}

// ============================================================================
// NFC 感应卡片区
// ============================================================================
@Composable
private fun NfcScanCard(
    cardUid: String?,
    filterByCard: Boolean,
    onClearFilter: () -> Unit,
) {
    val infiniteTransition = rememberInfiniteTransition(label = "nfc_pulse")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = EaseInOutCubic),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "pulse_alpha",
    )

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = RefundColors.SurfaceDark),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .border(
                    width = 1.dp,
                    brush = Brush.linearGradient(
                        colors = if (filterByCard) {
                            listOf(RefundColors.Gold, RefundColors.GoldDim)
                        } else {
                            listOf(RefundColors.BorderGold, Color.Transparent)
                        },
                    ),
                    shape = RoundedCornerShape(16.dp),
                )
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // NFC 图标 + 脉冲动画
            Box(
                contentAlignment = Alignment.Center,
                modifier = Modifier.size(48.dp),
            ) {
                if (!filterByCard) {
                    Canvas(modifier = Modifier.size(48.dp)) {
                        drawCircle(
                            color = RefundColors.Gold.copy(alpha = pulseAlpha * 0.3f),
                            radius = size.minDimension / 2,
                        )
                    }
                }
                Icon(
                    imageVector = Icons.Filled.Nfc,
                    contentDescription = null,
                    tint = if (filterByCard) RefundColors.Gold else RefundColors.GoldSoft.copy(alpha = pulseAlpha),
                    modifier = Modifier.size(28.dp),
                )
            }

            Spacer(modifier = Modifier.width(12.dp))

            Column(modifier = Modifier.weight(1f)) {
                if (filterByCard && cardUid != null) {
                    Text(
                        text = "已筛选卡片",
                        color = RefundColors.Gold,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.SemiBold,
                    )
                    Text(
                        text = "UID: $cardUid",
                        color = RefundColors.TextSecondary,
                        fontSize = 12.sp,
                    )
                } else {
                    Text(
                        text = "贴卡查询订单",
                        color = RefundColors.TextPrimary,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium,
                    )
                    Text(
                        text = "将 NFC 卡片贴近设备，查询该卡在本摊位的历史订单",
                        color = RefundColors.TextDim,
                        fontSize = 12.sp,
                    )
                }
            }

            if (filterByCard) {
                IconButton(onClick = onClearFilter) {
                    Icon(
                        imageVector = Icons.Filled.Close,
                        contentDescription = "清除筛选",
                        tint = RefundColors.TextSecondary,
                    )
                }
            }
        }
    }
}

// ============================================================================
// 交易列表区域
// ============================================================================
@Composable
private fun TransactionListSection(
    transactions: List<Transaction>,
    selectedTransaction: Transaction?,
    isLoading: Boolean,
    filterByCard: Boolean,
    onTransactionSelected: (Transaction) -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier) {
        // 标题行
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = if (filterByCard) "卡片订单记录" else "最近交易流水",
                color = RefundColors.TextPrimary,
                fontSize = 16.sp,
                fontWeight = FontWeight.SemiBold,
            )
            Spacer(modifier = Modifier.weight(1f))
            Text(
                text = "${transactions.size} 条记录",
                color = RefundColors.TextDim,
                fontSize = 12.sp,
            )
        }

        if (isLoading) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center,
            ) {
                CircularProgressIndicator(
                    color = RefundColors.Gold,
                    strokeWidth = 2.dp,
                    modifier = Modifier.size(32.dp),
                )
            }
        } else if (transactions.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center,
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        imageVector = Icons.Filled.ReceiptLong,
                        contentDescription = null,
                        tint = RefundColors.TextDim,
                        modifier = Modifier.size(48.dp),
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "暂无交易记录",
                        color = RefundColors.TextDim,
                        fontSize = 14.sp,
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxWidth(),
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 4.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                items(transactions, key = { it.id }) { transaction ->
                    TransactionItem(
                        transaction = transaction,
                        isSelected = selectedTransaction?.id == transaction.id,
                        onClick = { onTransactionSelected(transaction) },
                    )
                }
            }
        }
    }
}

// ============================================================================
// 单条交易项
// ============================================================================
@Composable
private fun TransactionItem(
    transaction: Transaction,
    isSelected: Boolean,
    onClick: () -> Unit,
) {
    val isRefunded = transaction.type == "refund"
    val borderColor = when {
        isSelected -> RefundColors.Gold
        isRefunded -> RefundColors.DangerRed.copy(alpha = 0.5f)
        else -> Color.Transparent
    }
    val bgColor = when {
        isSelected -> RefundColors.SurfaceSelected
        else -> RefundColors.SurfaceDark
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(
                width = if (isSelected || isRefunded) 1.dp else 0.dp,
                color = borderColor,
                shape = RoundedCornerShape(12.dp),
            )
            .clickable(enabled = !isRefunded) { onClick() },
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = bgColor),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // 类型图标
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(CircleShape)
                    .background(
                        when {
                            isRefunded -> RefundColors.DangerRedBg
                            transaction.type == "payment" -> Color(0x22FFD700)
                            else -> Color(0x2200E676)
                        },
                    ),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    imageVector = when {
                        isRefunded -> Icons.Filled.Undo
                        transaction.type == "payment" -> Icons.Filled.ShoppingCart
                        else -> Icons.Filled.AddCard
                    },
                    contentDescription = null,
                    tint = when {
                        isRefunded -> RefundColors.DangerRed
                        transaction.type == "payment" -> RefundColors.Gold
                        else -> RefundColors.SuccessGreen
                    },
                    modifier = Modifier.size(20.dp),
                )
            }

            Spacer(modifier = Modifier.width(12.dp))

            // 交易信息
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = when (transaction.type) {
                            "payment" -> "消费"
                            "recharge" -> "充值"
                            "refund" -> "已退款"
                            else -> transaction.type ?: "未知"
                        },
                        color = if (isRefunded) RefundColors.DangerRed else RefundColors.TextPrimary,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium,
                    )
                    if (isRefunded) {
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "不可撤销",
                            color = RefundColors.DangerRedDim,
                            fontSize = 10.sp,
                            modifier = Modifier
                                .background(
                                    RefundColors.DangerRedBg,
                                    RoundedCornerShape(4.dp),
                                )
                                .padding(horizontal = 4.dp, vertical = 1.dp),
                        )
                    }
                }
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = "订单 #${transaction.id} · ${transaction.createdAt ?: ""}",
                    color = RefundColors.TextDim,
                    fontSize = 11.sp,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }

            // 金额
            Text(
                text = "${if (transaction.type == "payment") "-" else "+"}¥${"%.2f".format(transaction.amount)}",
                color = when {
                    isRefunded -> RefundColors.DangerRed
                    transaction.type == "payment" -> RefundColors.TextPrimary
                    else -> RefundColors.SuccessGreen
                },
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
            )
        }
    }
}

// ============================================================================
// 底部退款操作栏
// ============================================================================
@Composable
private fun RefundActionBar(
    transaction: Transaction?,
    isProcessing: Boolean,
    onInitiateRefund: () -> Unit,
    onCancel: () -> Unit,
) {
    if (transaction == null) return

    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = RefundColors.SurfaceDark,
        shadowElevation = 8.dp,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .border(
                    width = 1.dp,
                    brush = Brush.verticalGradient(
                        colors = listOf(RefundColors.BorderGold, Color.Transparent),
                    ),
                    shape = RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp),
                )
                .padding(16.dp),
        ) {
            // 选中订单摘要
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(
                    imageVector = Icons.Filled.Receipt,
                    contentDescription = null,
                    tint = RefundColors.Gold,
                    modifier = Modifier.size(20.dp),
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "订单 #${transaction.id}",
                    color = RefundColors.TextPrimary,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Medium,
                )
                Spacer(modifier = Modifier.weight(1f))
                Text(
                    text = "¥${"%.2f".format(transaction.amount)}",
                    color = RefundColors.Gold,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            // 操作按钮
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                OutlinedButton(
                    onClick = onCancel,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = RefundColors.TextSecondary,
                    ),
                    border = ButtonDefaults.outlinedButtonBorder.copy(
                        brush = Brush.linearGradient(
                            listOf(RefundColors.TextDim, RefundColors.TextDim),
                        ),
                    ),
                ) {
                    Text("取消")
                }

                Button(
                    onClick = onInitiateRefund,
                    modifier = Modifier.weight(2f),
                    enabled = !isProcessing,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = RefundColors.DangerRed,
                        contentColor = Color.White,
                    ),
                    shape = RoundedCornerShape(12.dp),
                ) {
                    Icon(
                        imageVector = Icons.Filled.Undo,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp),
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "发起退款",
                        fontWeight = FontWeight.Bold,
                    )
                }
            }
        }
    }
}

// ============================================================================
// 退款确认对话框（简单确认，无 PIN 码）
// ============================================================================
@Composable
private fun RefundConfirmDialog(
    transaction: Transaction?,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit,
) {
    if (transaction == null) return

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = RefundColors.SurfaceElevated,
        shape = RoundedCornerShape(20.dp),
        title = {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Filled.Warning,
                    contentDescription = null,
                    tint = RefundColors.DangerRed,
                    modifier = Modifier.size(24.dp),
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "确认退款",
                    color = RefundColors.TextPrimary,
                    fontWeight = FontWeight.Bold,
                )
            }
        },
        text = {
            Column {
                // 警告信息
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = RefundColors.DangerRedBg,
                    ),
                    shape = RoundedCornerShape(12.dp),
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Icon(
                            imageVector = Icons.Filled.ErrorOutline,
                            contentDescription = null,
                            tint = RefundColors.DangerRed,
                            modifier = Modifier.size(20.dp),
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "确定退款 ¥${"%.2f".format(transaction.amount)} 吗？\n此操作不可撤销。",
                            color = RefundColors.DangerRed,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Medium,
                        )
                    }
                }

                Spacer(modifier = Modifier.height(12.dp))

                Text(
                    text = "订单 #${transaction.id}",
                    color = RefundColors.TextSecondary,
                    fontSize = 12.sp,
                )
            }
        },
        confirmButton = {
            Button(
                onClick = onConfirm,
                colors = ButtonDefaults.buttonColors(
                    containerColor = RefundColors.DangerRed,
                    contentColor = Color.White,
                ),
                shape = RoundedCornerShape(10.dp),
            ) {
                Icon(
                    imageVector = Icons.Filled.Warning,
                    contentDescription = null,
                    modifier = Modifier.size(16.dp),
                )
                Spacer(modifier = Modifier.width(4.dp))
                Text("执行退款", fontWeight = FontWeight.Bold)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("取消", color = RefundColors.TextSecondary)
            }
        },
    )
}

// ============================================================================
// 处理中遮罩
// ============================================================================
@Composable
private fun ProcessingOverlay() {
    val infiniteTransition = rememberInfiniteTransition(label = "processing")
    val rotation by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = LinearEasing),
        ),
        label = "rotation",
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black.copy(alpha = 0.7f))
            .clickable(enabled = false) {},
        contentAlignment = Alignment.Center,
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            CircularProgressIndicator(
                color = RefundColors.Gold,
                strokeWidth = 3.dp,
                modifier = Modifier.size(48.dp),
            )
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "正在处理退款...",
                color = RefundColors.TextPrimary,
                fontSize = 16.sp,
                fontWeight = FontWeight.Medium,
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "请勿关闭页面",
                color = RefundColors.TextDim,
                fontSize = 12.sp,
            )
        }
    }
}
