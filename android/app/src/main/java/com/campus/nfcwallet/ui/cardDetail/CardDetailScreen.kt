package com.campus.nfcwallet.ui.cardDetail

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.*
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// ============================================================================
// 主题配色 — 深色科技风（蓝紫色调）
// ============================================================================
object CardDetailColors {
    val Background = Color(0xFF0D1117)
    val Surface = Color(0xFF161B22)
    val SurfaceElevated = Color(0xFF1C2128)
    val BorderColor = Color(0xFF30363D)
    val AccentBlue = Color(0xFF58A6FF)
    val AccentCyan = Color(0xFF56D4DD)
    val AccentGreen = Color(0xFF3FB950)
    val AccentOrange = Color(0xFFD29922)
    val AccentRed = Color(0xFFF85149)
    val AccentPurple = Color(0xFFBC8CFF)
    val Gold = Color(0xFFFFD700)
    val TextPrimary = Color(0xFFF0F6FC)
    val TextSecondary = Color(0xFF8B949E)
    val TextDim = Color(0xFF484F58)
    val BorderSoft = Color(0x4458A6FF)
}

// ============================================================================
// Data Models
// ============================================================================
data class ParticipantDetail(
    val id: Int,
    val name: String,
    val cardUid: String,
    val className: String?,
    val studentNo: String?,
    val status: String,
    val createdAt: String?,
)

data class AccountDetail(
    val balance: Double,
    val creditBorrowed: Double,
    val creditFeePaid: Double,
)

data class LoanSummary(
    val activeCount: Int,
    val totalDebt: Double,
)

data class StockHoldingDetail(
    val boothId: Int,
    val boothName: String,
    val shares: Int,
    val totalInvested: Double,
)

data class TransactionDetail(
    val id: Int,
    val type: String,
    val amount: Double,
    val balanceBefore: Double?,
    val balanceAfter: Double?,
    val remark: String?,
    val createdAt: String?,
)

data class CardDetailUiState(
    val cardUid: String? = null,
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val participant: ParticipantDetail? = null,
    val account: AccountDetail? = null,
    val loans: LoanSummary? = null,
    val stockHoldings: List<StockHoldingDetail> = emptyList(),
    val transactions: List<TransactionDetail> = emptyList(),
) {
    val hasData: Boolean get() = participant != null
}

// ============================================================================
// 主界面
// ============================================================================
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CardDetailScreen(
    state: CardDetailUiState,
    onReset: () -> Unit,
    onDismissError: () -> Unit,
    onLogout: () -> Unit,
) {
    Scaffold(
        containerColor = CardDetailColors.Background,
        topBar = { TopBar(onLogout = onLogout, onReset = onReset, hasData = state.hasData) },
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
        ) {
            if (!state.hasData && !state.isLoading) {
                // 等待刷卡
                NfcWaitingSection()
            } else if (state.isLoading) {
                // 加载中
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center,
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        CircularProgressIndicator(
                            color = CardDetailColors.AccentBlue,
                            strokeWidth = 3.dp,
                        )
                        Spacer(Modifier.height(16.dp))
                        Text(
                            "正在查询卡片信息...",
                            color = CardDetailColors.TextSecondary,
                            fontSize = 14.sp,
                        )
                    }
                }
            } else {
                // 展示数据
                DetailContent(state = state)
            }
        }

        // 错误提示
        if (state.errorMessage != null) {
            AlertDialog(
                onDismissRequest = onDismissError,
                containerColor = CardDetailColors.Surface,
                title = {
                    Text("查询失败", color = CardDetailColors.AccentRed)
                },
                text = {
                    Text(state.errorMessage, color = CardDetailColors.TextPrimary)
                },
                confirmButton = {
                    TextButton(onClick = onDismissError) {
                        Text("确定", color = CardDetailColors.AccentBlue)
                    }
                },
            )
        }
    }
}

// ============================================================================
// 顶部栏
// ============================================================================
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TopBar(onLogout: () -> Unit, onReset: () -> Unit, hasData: Boolean) {
    TopAppBar(
        title = {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .width(4.dp)
                        .height(24.dp)
                        .background(
                            Brush.verticalGradient(
                                listOf(CardDetailColors.AccentBlue, CardDetailColors.AccentCyan)
                            )
                        )
                )
                Spacer(Modifier.width(12.dp))
                Column {
                    Text(
                        "刷卡查看明细",
                        style = TextStyle(
                            color = CardDetailColors.TextPrimary,
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 1.sp,
                        ),
                    )
                    Text(
                        "NFC Card Inspector",
                        style = TextStyle(
                            color = CardDetailColors.TextDim,
                            fontSize = 11.sp,
                            letterSpacing = 1.sp,
                        ),
                    )
                }
            }
        },
        actions = {
            if (hasData) {
                IconButton(onClick = onReset) {
                    Icon(
                        Icons.Default.Refresh,
                        contentDescription = "重新刷卡",
                        tint = CardDetailColors.AccentBlue,
                    )
                }
            }
            IconButton(onClick = onLogout) {
                Icon(
                    Icons.Default.Logout,
                    contentDescription = "退出",
                    tint = CardDetailColors.TextSecondary,
                )
            }
        },
        colors = TopAppBarDefaults.topAppBarColors(
            containerColor = CardDetailColors.Surface,
        ),
    )
}

// ============================================================================
// NFC 等待区
// ============================================================================
@Composable
private fun NfcWaitingSection() {
    val infiniteTransition = rememberInfiniteTransition(label = "nfc_pulse")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 1.0f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "alpha",
    )

    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center,
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Box(
                modifier = Modifier.size(160.dp),
                contentAlignment = Alignment.Center,
            ) {
                Canvas(modifier = Modifier.fillMaxSize()) {
                    for (i in 0..2) {
                        val scale = 1f + i * 0.15f
                        drawCircle(
                            color = CardDetailColors.AccentBlue.copy(alpha = pulseAlpha / (i + 1)),
                            radius = size.minDimension / 2 * scale,
                            style = Stroke(width = 2.dp.toPx()),
                        )
                    }
                }
                Icon(
                    imageVector = Icons.Default.Nfc,
                    contentDescription = "NFC",
                    tint = CardDetailColors.AccentBlue,
                    modifier = Modifier.size(72.dp),
                )
            }
            Spacer(Modifier.height(24.dp))
            Text(
                "请将学生卡贴近设备",
                style = TextStyle(
                    color = CardDetailColors.TextPrimary,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Medium,
                    letterSpacing = 2.sp,
                ),
            )
            Spacer(Modifier.height(8.dp))
            Text(
                "刷卡后将显示该用户的全部明细信息",
                style = TextStyle(
                    color = CardDetailColors.TextDim,
                    fontSize = 13.sp,
                ),
            )
        }
    }
}

// ============================================================================
// 详情内容
// ============================================================================
@Composable
private fun DetailContent(state: CardDetailUiState) {
    val participant = state.participant ?: return
    val account = state.account ?: AccountDetail(0.0, 0.0, 0.0)
    val loans = state.loans ?: LoanSummary(0, 0.0)

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        contentPadding = PaddingValues(vertical = 12.dp),
    ) {
        // 用户基本信息卡片
        item {
            ParticipantInfoCard(participant)
        }

        // 账户概览
        item {
            AccountOverviewCard(account, loans)
        }

        // 股票持仓
        if (state.stockHoldings.isNotEmpty()) {
            item {
                StockHoldingsCard(state.stockHoldings)
            }
        }

        // 交易流水标题
        item {
            SectionHeader(
                icon = Icons.Default.Receipt,
                title = "交易流水",
                subtitle = "共 ${state.transactions.size} 条记录",
            )
        }

        // 交易流水列表
        if (state.transactions.isEmpty()) {
            item {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 32.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    Text("暂无交易记录", color = CardDetailColors.TextDim, fontSize = 14.sp)
                }
            }
        } else {
            itemsIndexed(state.transactions) { index, txn ->
                TransactionItem(txn, index)
            }
        }

        item { Spacer(Modifier.height(24.dp)) }
    }
}

// ============================================================================
// 用户信息卡片
// ============================================================================
@Composable
private fun ParticipantInfoCard(participant: ParticipantDetail) {
    InfoCard {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // 头像
            Box(
                modifier = Modifier
                    .size(56.dp)
                    .clip(CircleShape)
                    .background(
                        Brush.linearGradient(
                            listOf(CardDetailColors.AccentBlue, CardDetailColors.AccentPurple)
                        )
                    ),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = participant.name.take(1),
                    style = TextStyle(
                        color = Color.White,
                        fontSize = 24.sp,
                        fontWeight = FontWeight.Bold,
                    ),
                )
            }

            Spacer(Modifier.width(16.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    participant.name,
                    style = TextStyle(
                        color = CardDetailColors.TextPrimary,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold,
                    ),
                )
                Spacer(Modifier.height(4.dp))
                if (!participant.className.isNullOrBlank()) {
                    Text(
                        participant.className,
                        style = TextStyle(
                            color = CardDetailColors.TextSecondary,
                            fontSize = 13.sp,
                        ),
                    )
                }
                if (!participant.studentNo.isNullOrBlank()) {
                    Text(
                        "学号: ${participant.studentNo}",
                        style = TextStyle(
                            color = CardDetailColors.TextDim,
                            fontSize = 12.sp,
                        ),
                    )
                }
            }

            // 状态标签
            StatusBadge(participant.status)
        }

        Spacer(Modifier.height(12.dp))
        HorizontalDivider(color = CardDetailColors.BorderColor, thickness = 0.5.dp)
        Spacer(Modifier.height(8.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            InfoChip(label = "卡号", value = participant.cardUid)
            InfoChip(label = "ID", value = "#${participant.id}")
        }
    }
}

@Composable
private fun StatusBadge(status: String) {
    val (color, label) = when (status) {
        "active" -> CardDetailColors.AccentGreen to "正常"
        "inactive" -> CardDetailColors.TextDim to "已退卡"
        "blocked" -> CardDetailColors.AccentRed to "已冻结"
        else -> CardDetailColors.TextDim to status
    }
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(12.dp))
            .background(color.copy(alpha = 0.15f))
            .border(1.dp, color.copy(alpha = 0.4f), RoundedCornerShape(12.dp))
            .padding(horizontal = 10.dp, vertical = 4.dp),
    ) {
        Text(label, color = color, fontSize = 12.sp, fontWeight = FontWeight.Medium)
    }
}

@Composable
private fun InfoChip(label: String, value: String) {
    Column {
        Text(label, color = CardDetailColors.TextDim, fontSize = 10.sp)
        Text(value, color = CardDetailColors.TextSecondary, fontSize = 12.sp, fontWeight = FontWeight.Medium)
    }
}

// ============================================================================
// 账户概览卡片
// ============================================================================
@Composable
private fun AccountOverviewCard(account: AccountDetail, loans: LoanSummary) {
    InfoCard {
        SectionHeader(icon = Icons.Default.AccountBalanceWallet, title = "账户概览")
        Spacer(Modifier.height(12.dp))

        // 余额大字
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text("当前余额", color = CardDetailColors.TextDim, fontSize = 12.sp)
                Spacer(Modifier.height(4.dp))
                Text(
                    String.format("¥%.2f", account.balance),
                    style = TextStyle(
                        color = CardDetailColors.Gold,
                        fontSize = 32.sp,
                        fontWeight = FontWeight.Bold,
                    ),
                )
            }
        }

        Spacer(Modifier.height(16.dp))

        // 信贷和贷款信息
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly,
        ) {
            StatItem(
                label = "累计借款",
                value = String.format("¥%.2f", account.creditBorrowed),
                color = CardDetailColors.AccentOrange,
            )
            StatItem(
                label = "手续费",
                value = String.format("¥%.2f", account.creditFeePaid),
                color = CardDetailColors.TextSecondary,
            )
            StatItem(
                label = "未清贷款",
                value = if (loans.activeCount > 0) "${loans.activeCount}笔 ¥${String.format("%.2f", loans.totalDebt)}" else "无",
                color = if (loans.activeCount > 0) CardDetailColors.AccentRed else CardDetailColors.AccentGreen,
            )
        }
    }
}

@Composable
private fun StatItem(label: String, value: String, color: Color) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(label, color = CardDetailColors.TextDim, fontSize = 11.sp)
        Spacer(Modifier.height(4.dp))
        Text(
            value,
            color = color,
            fontSize = 13.sp,
            fontWeight = FontWeight.SemiBold,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
    }
}

// ============================================================================
// 股票持仓卡片
// ============================================================================
@Composable
private fun StockHoldingsCard(holdings: List<StockHoldingDetail>) {
    InfoCard {
        SectionHeader(icon = Icons.Default.TrendingUp, title = "股票持仓", subtitle = "${holdings.size} 只")
        Spacer(Modifier.height(12.dp))

        holdings.forEach { holding ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 6.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        holding.boothName,
                        color = CardDetailColors.TextPrimary,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium,
                    )
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text(
                        "${holding.shares} 股",
                        color = CardDetailColors.AccentCyan,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                    )
                    Text(
                        "投入 ¥${String.format("%.2f", holding.totalInvested)}",
                        color = CardDetailColors.TextDim,
                        fontSize = 11.sp,
                    )
                }
            }
        }
    }
}

// ============================================================================
// 交易流水项
// ============================================================================
@Composable
private fun TransactionItem(txn: TransactionDetail, index: Int) {
    val (icon, color, typeLabel) = getTransactionStyle(txn.type)
    val isIncome = txn.type in listOf("recharge", "loan_issue", "stock_sell", "refund")

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .background(if (index % 2 == 0) CardDetailColors.Surface else CardDetailColors.SurfaceElevated)
            .padding(horizontal = 14.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // 类型图标
        Box(
            modifier = Modifier
                .size(36.dp)
                .clip(CircleShape)
                .background(color.copy(alpha = 0.12f)),
            contentAlignment = Alignment.Center,
        ) {
            Icon(icon, contentDescription = null, tint = color, modifier = Modifier.size(18.dp))
        }

        Spacer(Modifier.width(12.dp))

        // 类型和备注
        Column(modifier = Modifier.weight(1f)) {
            Text(
                typeLabel,
                color = CardDetailColors.TextPrimary,
                fontSize = 14.sp,
                fontWeight = FontWeight.Medium,
            )
            if (!txn.remark.isNullOrBlank()) {
                Text(
                    txn.remark,
                    color = CardDetailColors.TextDim,
                    fontSize = 11.sp,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            if (txn.createdAt != null) {
                Text(
                    formatTime(txn.createdAt),
                    color = CardDetailColors.TextDim,
                    fontSize = 10.sp,
                )
            }
        }

        // 金额
        Column(horizontalAlignment = Alignment.End) {
            Text(
                "${if (isIncome) "+" else "-"}¥${String.format("%.2f", txn.amount)}",
                color = if (isIncome) CardDetailColors.AccentGreen else CardDetailColors.AccentRed,
                fontSize = 15.sp,
                fontWeight = FontWeight.Bold,
            )
            if (txn.balanceAfter != null) {
                Text(
                    "余额 ¥${String.format("%.2f", txn.balanceAfter)}",
                    color = CardDetailColors.TextDim,
                    fontSize = 10.sp,
                )
            }
        }
    }
}

private fun getTransactionStyle(type: String): Triple<ImageVector, Color, String> {
    return when (type) {
        "pay" -> Triple(Icons.Default.ShoppingCart, CardDetailColors.AccentRed, "消费")
        "recharge" -> Triple(Icons.Default.AddCard, CardDetailColors.AccentGreen, "充值")
        "loan_issue" -> Triple(Icons.Default.AccountBalance, CardDetailColors.AccentOrange, "贷款发放")
        "loan_fee" -> Triple(Icons.Default.MoneyOff, CardDetailColors.TextSecondary, "贷款手续费")
        "loan_repay" -> Triple(Icons.Default.CreditScore, CardDetailColors.AccentBlue, "贷款还款")
        "stock_buy" -> Triple(Icons.Default.TrendingUp, CardDetailColors.AccentPurple, "买入股票")
        "stock_sell" -> Triple(Icons.Default.TrendingDown, CardDetailColors.AccentCyan, "卖出股票")
        "refund" -> Triple(Icons.Default.Replay, CardDetailColors.AccentGreen, "退款")
        "correction" -> Triple(Icons.Default.Build, CardDetailColors.TextSecondary, "调整")
        "transfer_in" -> Triple(Icons.Default.CallReceived, CardDetailColors.AccentGreen, "转入")
        "transfer_out" -> Triple(Icons.Default.CallMade, CardDetailColors.AccentRed, "转出")
        else -> Triple(Icons.Default.SwapHoriz, CardDetailColors.TextSecondary, type)
    }
}

private fun formatTime(isoTime: String): String {
    return try {
        // "2024-01-15T10:30:00" -> "01-15 10:30"
        val parts = isoTime.split("T")
        if (parts.size == 2) {
            val datePart = parts[0].substring(5) // "01-15"
            val timePart = parts[1].substring(0, 5) // "10:30"
            "$datePart $timePart"
        } else {
            isoTime.take(16)
        }
    } catch (_: Exception) {
        isoTime.take(16)
    }
}

// ============================================================================
// 通用组件
// ============================================================================
@Composable
private fun InfoCard(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit,
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(CardDetailColors.Surface)
            .border(1.dp, CardDetailColors.BorderColor, RoundedCornerShape(12.dp))
            .padding(16.dp),
        content = content,
    )
}

@Composable
private fun SectionHeader(
    icon: ImageVector,
    title: String,
    subtitle: String? = null,
) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(
            icon,
            contentDescription = null,
            tint = CardDetailColors.AccentBlue,
            modifier = Modifier.size(18.dp),
        )
        Spacer(Modifier.width(8.dp))
        Text(
            title,
            color = CardDetailColors.TextPrimary,
            fontSize = 15.sp,
            fontWeight = FontWeight.SemiBold,
        )
        if (subtitle != null) {
            Spacer(Modifier.width(8.dp))
            Text(
                subtitle,
                color = CardDetailColors.TextDim,
                fontSize = 12.sp,
            )
        }
    }
}
