package com.campus.nfcwallet.ui.cardReturn

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.EaseInOutSine
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AccountCircle
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.CreditScore
import androidx.compose.material.icons.filled.ExitToApp
import androidx.compose.material.icons.filled.MonetizationOn
import androidx.compose.material.icons.filled.Nfc
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Divider
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// ============================================================================
// 主题配色 — 深邃藏青 + 橙金色（退卡终端）
// ============================================================================
object CardReturnColors {
    val DeepBg = Color(0xFF0B1929)
    val SurfaceBg = Color(0xFF122240)
    val ElevatedBg = Color(0xFF1A3058)
    val BorderColor = Color(0xFF243B5E)
    val AccentGold = Color(0xFFE8C471)
    val AccentBright = Color(0xFFF5DB8F)
    val AccentDim = Color(0xFF9E9A8F)
    val TextPrimary = Color(0xFFF0EDE5)
    val TextSecondary = Color(0xFFB8B4A8)
    val TextDim = Color(0xFF6B6860)
    val SuccessGreen = Color(0xFF4CAF50)
    val ErrorRed = Color(0xFFE53935)
    val WarningAmber = Color(0xFFFF8F00)
    val BorderSoft = Color(0x44E8C471)
}

// ============================================================================
// UI State
// ============================================================================
data class CardReturnUiState(
    val cardUid: String? = null,
    val participantId: Int? = null,
    val participantName: String? = null,
    val className: String? = null,
    val balance: Double = 0.0,
    val loanAmount: Double = 0.0,
    val loanCount: Int = 0,
    val isLoadingInfo: Boolean = false,
    val isLoading: Boolean = false,
    val isSuccess: Boolean = false,
    val errorMessage: String? = null,
    // 结果
    val resultRefunded: Double = 0.0,
    val resultLoanRepaid: Double = 0.0,
    val resultRemainingDebt: Double = 0.0,
    val resultMode: String? = null, // "repay_first" or "direct_refund"
) {
    val hasCard: Boolean get() = cardUid != null
    val isInfoReady: Boolean get() = participantId != null && !isLoadingInfo
    val hasLoan: Boolean get() = loanCount > 0 && loanAmount > 0
}

// ============================================================================
// 主界面
// ============================================================================
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CardReturnScreen(
    state: CardReturnUiState,
    onReturnWithRepay: () -> Unit,
    onReturnWithoutRepay: () -> Unit,
    onReset: () -> Unit,
    onDismissError: () -> Unit,
    onLogout: () -> Unit,
) {
    Scaffold(
        containerColor = CardReturnColors.DeepBg,
        topBar = { TopBar(onLogout = onLogout) },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp, vertical = 12.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            NfcScanSection(cardDetected = state.hasCard)

            Spacer(modifier = Modifier.height(16.dp))

            // 加载持卡人信息中
            AnimatedVisibility(
                visible = state.hasCard && state.isLoadingInfo,
                enter = fadeIn() + expandVertically(),
                exit = fadeOut() + shrinkVertically(),
            ) {
                LoadingCard(text = "读取持卡人信息...")
            }

            // 信息展示及退卡操作
            AnimatedVisibility(
                visible = state.isInfoReady && !state.isSuccess,
                enter = fadeIn() + expandVertically(),
                exit = fadeOut() + shrinkVertically(),
            ) {
                Column {
                    ParticipantInfoCard(
                        name = state.participantName ?: "-",
                        className = state.className ?: "-",
                        cardUid = state.cardUid ?: "-",
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    AccountSummaryCard(
                        balance = state.balance,
                        loanAmount = state.loanAmount,
                        loanCount = state.loanCount,
                    )

                    Spacer(modifier = Modifier.height(20.dp))

                    ReturnModeSection(
                        state = state,
                        onReturnWithRepay = onReturnWithRepay,
                        onReturnWithoutRepay = onReturnWithoutRepay,
                    )
                }
            }

            // 成功结果
            AnimatedVisibility(
                visible = state.isSuccess,
                enter = fadeIn() + expandVertically(),
                exit = fadeOut() + shrinkVertically(),
            ) {
                SuccessResultCard(
                    refunded = state.resultRefunded,
                    loanRepaid = state.resultLoanRepaid,
                    remainingDebt = state.resultRemainingDebt,
                    mode = state.resultMode,
                    onReset = onReset,
                )
            }
        }
    }

    // 错误弹窗
    if (state.errorMessage != null) {
        AlertDialog(
            onDismissRequest = onDismissError,
            containerColor = CardReturnColors.SurfaceBg,
            titleContentColor = CardReturnColors.ErrorRed,
            textContentColor = CardReturnColors.TextPrimary,
            title = { Text("操作失败") },
            text = { Text(state.errorMessage) },
            confirmButton = {
                TextButton(onClick = onDismissError) {
                    Text("确定", color = CardReturnColors.AccentGold)
                }
            },
        )
    }
}

// ============================================================================
// 顶部栏
// ============================================================================
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TopBar(onLogout: () -> Unit) {
    TopAppBar(
        title = {
            Column {
                Text(
                    text = "退卡办理终端",
                    color = CardReturnColors.AccentBright,
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp,
                )
                Text(
                    text = "CARD RETURN TERMINAL",
                    color = CardReturnColors.AccentDim,
                    fontSize = 10.sp,
                    letterSpacing = 2.sp,
                )
            }
        },
        actions = {
            IconButton(onClick = onLogout) {
                Icon(
                    Icons.Default.ExitToApp,
                    contentDescription = "退出",
                    tint = CardReturnColors.AccentDim,
                )
            }
        },
        colors = TopAppBarDefaults.topAppBarColors(
            containerColor = CardReturnColors.DeepBg,
        ),
    )
}

// ============================================================================
// NFC 感应区
// ============================================================================
@Composable
private fun NfcScanSection(cardDetected: Boolean) {
    val infiniteTransition = rememberInfiniteTransition(label = "nfc_pulse")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = EaseInOutSine),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "pulse_alpha",
    )
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 0.85f,
        targetValue = 1.15f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = EaseInOutSine),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "pulse_scale",
    )

    SoftCard(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            if (!cardDetected) {
                Box(
                    contentAlignment = Alignment.Center,
                    modifier = Modifier.size(100.dp),
                ) {
                    Canvas(modifier = Modifier.size(100.dp)) {
                        drawCircle(
                            color = CardReturnColors.AccentGold.copy(alpha = pulseAlpha * 0.3f),
                            radius = size.minDimension / 2 * pulseScale,
                            style = Stroke(width = 2.dp.toPx()),
                        )
                    }
                    Canvas(modifier = Modifier.size(60.dp)) {
                        drawCircle(
                            color = CardReturnColors.AccentGold.copy(alpha = 0.6f),
                            radius = size.minDimension / 2,
                            style = Stroke(width = 1.5.dp.toPx()),
                        )
                    }
                    Icon(
                        Icons.Default.Nfc,
                        contentDescription = "NFC",
                        tint = CardReturnColors.AccentGold.copy(alpha = pulseAlpha),
                        modifier = Modifier.size(36.dp),
                    )
                }
                Spacer(modifier = Modifier.height(12.dp))
                Text(
                    text = "请将要退还的学生卡贴近设备",
                    color = CardReturnColors.TextSecondary,
                    fontSize = 14.sp,
                )
                Text(
                    text = "AWAITING CARD CONTACT",
                    color = CardReturnColors.TextDim,
                    fontSize = 10.sp,
                    letterSpacing = 2.sp,
                )
            } else {
                Icon(
                    Icons.Default.CheckCircle,
                    contentDescription = "已识别",
                    tint = CardReturnColors.SuccessGreen,
                    modifier = Modifier.size(48.dp),
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "卡片已识别",
                    color = CardReturnColors.SuccessGreen,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Medium,
                )
            }
        }
    }
}

// ============================================================================
// 加载卡片
// ============================================================================
@Composable
private fun LoadingCard(text: String) {
    SoftCard(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            CircularProgressIndicator(
                modifier = Modifier.size(24.dp),
                color = CardReturnColors.AccentGold,
                strokeWidth = 2.dp,
            )
            Spacer(modifier = Modifier.width(12.dp))
            Text(
                text = text,
                color = CardReturnColors.TextPrimary,
                fontSize = 14.sp,
            )
        }
    }
}

// ============================================================================
// 持卡人信息
// ============================================================================
@Composable
private fun ParticipantInfoCard(name: String, className: String, cardUid: String) {
    SoftCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            SectionLabel(text = "持卡人信息", icon = Icons.Default.AccountCircle)
            Spacer(modifier = Modifier.height(12.dp))
            InfoRow(label = "姓名", value = name)
            Spacer(modifier = Modifier.height(8.dp))
            InfoRow(label = "班级", value = className)
            Spacer(modifier = Modifier.height(8.dp))
            InfoRow(label = "卡片 UID", value = cardUid)
        }
    }
}

// ============================================================================
// 账户概览
// ============================================================================
@Composable
private fun AccountSummaryCard(balance: Double, loanAmount: Double, loanCount: Int) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(
                width = 1.5.dp,
                brush = Brush.linearGradient(
                    colors = listOf(CardReturnColors.AccentGold, CardReturnColors.AccentDim),
                ),
                shape = RoundedCornerShape(12.dp),
            )
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        CardReturnColors.ElevatedBg,
                        CardReturnColors.SurfaceBg,
                    ),
                ),
            )
            .padding(20.dp),
    ) {
        Column {
            SectionLabel(text = "账户概览", icon = Icons.Default.MonetizationOn)
            Spacer(modifier = Modifier.height(16.dp))

            AmountRow(
                label = "当前余额",
                value = "¥${"%.2f".format(balance)}",
                valueColor = CardReturnColors.SuccessGreen,
                isBold = true,
                fontSize = 20.sp,
            )

            Spacer(modifier = Modifier.height(12.dp))
            Divider(color = CardReturnColors.BorderSoft, thickness = 1.dp)
            Spacer(modifier = Modifier.height(12.dp))

            AmountRow(
                label = "未清贷款笔数",
                value = "$loanCount 笔",
                valueColor = if (loanCount > 0) CardReturnColors.WarningAmber else CardReturnColors.TextSecondary,
            )

            Spacer(modifier = Modifier.height(8.dp))

            AmountRow(
                label = "待偿还贷款总额",
                value = "¥${"%.2f".format(loanAmount)}",
                valueColor = if (loanAmount > 0) CardReturnColors.WarningAmber else CardReturnColors.TextSecondary,
                isBold = loanAmount > 0,
            )
        }
    }
}

// ============================================================================
// 退卡模式选择
// ============================================================================
@Composable
private fun ReturnModeSection(
    state: CardReturnUiState,
    onReturnWithRepay: () -> Unit,
    onReturnWithoutRepay: () -> Unit,
) {
    Column(modifier = Modifier.fillMaxWidth()) {
        SectionLabel(text = "请选择退卡方式", icon = Icons.Default.CreditScore)
        Spacer(modifier = Modifier.height(12.dp))

        // 模式1: 余额先偿还贷款
        ReturnModeCard(
            title = "余额先偿还贷款",
            description = if (state.hasLoan) {
                val repay = minOf(state.balance, state.loanAmount)
                val refund = maxOf(0.0, state.balance - state.loanAmount)
                "从余额 ¥${"%.2f".format(state.balance)} 中扣除 ¥${"%.2f".format(repay)} 偿还贷款，" +
                    "剩余 ¥${"%.2f".format(refund)} 退还给持卡人。未清贷款将保留用于追偿。"
            } else {
                "持卡人当前无未清贷款，此模式等同于直接全额退还。"
            },
            accentColor = CardReturnColors.AccentGold,
            isLoading = state.isLoading,
            isEnabled = !state.isLoading,
            onClick = onReturnWithRepay,
        )

        Spacer(modifier = Modifier.height(12.dp))

        // 模式2: 直接全额退还
        ReturnModeCard(
            title = "直接全额退还余额",
            description = if (state.hasLoan) {
                "全额退还余额 ¥${"%.2f".format(state.balance)}，贷款 ¥${"%.2f".format(state.loanAmount)} 另行偿还。" +
                    "未清贷款将保留用于追偿。"
            } else {
                "全额退还余额 ¥${"%.2f".format(state.balance)}。"
            },
            accentColor = CardReturnColors.WarningAmber,
            isLoading = state.isLoading,
            isEnabled = !state.isLoading,
            onClick = onReturnWithoutRepay,
        )

        if (state.hasLoan) {
            Spacer(modifier = Modifier.height(16.dp))
            WarningStrip(
                text = "该持卡人存在未清贷款，退卡后贷款记录将保留，" +
                    "系统会自动标记为 card_returned 以便后续追偿。"
            )
        }
    }
}

@Composable
private fun ReturnModeCard(
    title: String,
    description: String,
    accentColor: Color,
    isLoading: Boolean,
    isEnabled: Boolean,
    onClick: () -> Unit,
) {
    SoftCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = title,
                color = accentColor,
                fontSize = 15.sp,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = description,
                color = CardReturnColors.TextSecondary,
                fontSize = 12.sp,
                lineHeight = 18.sp,
            )
            Spacer(modifier = Modifier.height(12.dp))
            Button(
                onClick = onClick,
                enabled = isEnabled,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp),
                shape = RoundedCornerShape(10.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = accentColor,
                    contentColor = CardReturnColors.DeepBg,
                    disabledContainerColor = CardReturnColors.BorderColor,
                    disabledContentColor = CardReturnColors.TextDim,
                ),
            ) {
                if (isLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        color = CardReturnColors.DeepBg,
                        strokeWidth = 2.dp,
                    )
                } else {
                    Text(
                        text = "确认执行",
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                    )
                }
            }
        }
    }
}

// ============================================================================
// 成功结果卡片
// ============================================================================
@Composable
private fun SuccessResultCard(
    refunded: Double,
    loanRepaid: Double,
    remainingDebt: Double,
    mode: String?,
    onReset: () -> Unit,
) {
    SoftCard(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Icon(
                Icons.Default.CheckCircle,
                contentDescription = "成功",
                tint = CardReturnColors.SuccessGreen,
                modifier = Modifier.size(56.dp),
            )
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = "退卡办理成功",
                color = CardReturnColors.SuccessGreen,
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
            )

            if (mode == "repay_first") {
                Text(
                    text = "模式：余额先偿还贷款",
                    color = CardReturnColors.TextSecondary,
                    fontSize = 12.sp,
                )
            } else if (mode == "direct_refund") {
                Text(
                    text = "模式：直接全额退还",
                    color = CardReturnColors.TextSecondary,
                    fontSize = 12.sp,
                )
            }

            Spacer(modifier = Modifier.height(20.dp))

            Column(modifier = Modifier.fillMaxWidth()) {
                AmountRow(
                    label = "退还现金",
                    value = "¥${"%.2f".format(refunded)}",
                    valueColor = CardReturnColors.SuccessGreen,
                    isBold = true,
                    fontSize = 20.sp,
                )
                Spacer(modifier = Modifier.height(12.dp))
                AmountRow(
                    label = "本次偿还贷款",
                    value = "¥${"%.2f".format(loanRepaid)}",
                    valueColor = CardReturnColors.AccentGold,
                )
                Spacer(modifier = Modifier.height(8.dp))
                AmountRow(
                    label = "剩余未偿还贷款",
                    value = "¥${"%.2f".format(remainingDebt)}",
                    valueColor = if (remainingDebt > 0) CardReturnColors.WarningAmber else CardReturnColors.TextSecondary,
                )
            }

            Spacer(modifier = Modifier.height(20.dp))

            if (refunded > 0) {
                Text(
                    text = "请向持卡人现场退还现金 ¥${"%.2f".format(refunded)}",
                    color = CardReturnColors.WarningAmber,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Medium,
                )
                Spacer(modifier = Modifier.height(16.dp))
            }

            OutlinedButton(
                onClick = onReset,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp),
                colors = ButtonDefaults.outlinedButtonColors(
                    contentColor = CardReturnColors.AccentGold,
                ),
            ) {
                Icon(
                    Icons.Default.Refresh,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp),
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text("办理下一张", fontWeight = FontWeight.Medium)
            }
        }
    }
}

// ============================================================================
// 通用组件
// ============================================================================
@Composable
private fun SoftCard(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    Box(
        modifier = modifier
            .shadow(8.dp, RoundedCornerShape(12.dp))
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, CardReturnColors.BorderSoft, RoundedCornerShape(12.dp))
            .background(CardReturnColors.SurfaceBg),
    ) {
        content()
    }
}

@Composable
private fun SectionLabel(text: String, icon: androidx.compose.ui.graphics.vector.ImageVector) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(
            icon,
            contentDescription = null,
            tint = CardReturnColors.AccentBright,
            modifier = Modifier.size(18.dp),
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = text,
            color = CardReturnColors.AccentBright,
            fontSize = 13.sp,
            fontWeight = FontWeight.Bold,
            letterSpacing = 0.5.sp,
        )
    }
}

@Composable
private fun InfoRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = label,
            color = CardReturnColors.TextDim,
            fontSize = 12.sp,
        )
        Text(
            text = value,
            color = CardReturnColors.TextPrimary,
            fontSize = 13.sp,
            fontWeight = FontWeight.Medium,
        )
    }
}

@Composable
private fun AmountRow(
    label: String,
    value: String,
    valueColor: Color,
    isBold: Boolean = false,
    fontSize: androidx.compose.ui.unit.TextUnit = 15.sp,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = label,
            color = CardReturnColors.TextSecondary,
            fontSize = 12.sp,
        )
        Text(
            text = value,
            color = valueColor,
            fontSize = fontSize,
            fontWeight = if (isBold) FontWeight.Bold else FontWeight.Medium,
        )
    }
}

@Composable
private fun WarningStrip(text: String) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .border(
                1.dp,
                CardReturnColors.WarningAmber.copy(alpha = 0.5f),
                RoundedCornerShape(8.dp),
            )
            .background(CardReturnColors.WarningAmber.copy(alpha = 0.08f))
            .padding(12.dp),
    ) {
        Row(verticalAlignment = Alignment.Top) {
            Icon(
                Icons.Default.Warning,
                contentDescription = null,
                tint = CardReturnColors.WarningAmber,
                modifier = Modifier.size(16.dp),
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = text,
                color = CardReturnColors.WarningAmber,
                fontSize = 11.sp,
                lineHeight = 16.sp,
            )
        }
    }
}
