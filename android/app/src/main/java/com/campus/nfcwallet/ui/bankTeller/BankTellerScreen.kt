package com.campus.nfcwallet.ui.bankTeller

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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
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
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay

// ============================================================================
// 主题配色 — 深邃藏青 + 铂金色（高端私人银行风格）
// ============================================================================
object BankColors {
    val NavyDeep = Color(0xFF0B1929)          // 最深背景
    val NavySurface = Color(0xFF122240)       // 卡片背景
    val NavyElevated = Color(0xFF1A3058)      // 悬浮面板
    val NavyLight = Color(0xFF243B5E)         // 边框/分割线
    val Platinum = Color(0xFFE8E4D9)          // 铂金强调色
    val PlatinumBright = Color(0xFFF5F1E6)    // 高亮铂金
    val PlatinumDim = Color(0xFF9E9A8F)       // 暗淡铂金
    val TextPrimary = Color(0xFFF0EDE5)       // 主文字
    val TextSecondary = Color(0xFFB8B4A8)     // 次要文字
    val TextDim = Color(0xFF6B6860)           // 暗淡文字
    val SuccessGreen = Color(0xFF4CAF50)      // 成功绿
    val ErrorRed = Color(0xFFE53935)          // 错误红
    val WarningAmber = Color(0xFFFF8F00)      // 警告琥珀
    val BorderPlatinum = Color(0x44E8E4D9)    // 半透明铂金边框
}

// ============================================================================
// UI State
// ============================================================================
data class BankTellerUiState(
    val cardUid: String? = null,
    val participantName: String? = null,
    val participantId: Int? = null,
    val selectedAmount: Int? = null,
    val paperworkConfirmed: Boolean = false,
    val isLoading: Boolean = false,
    val isSuccess: Boolean = false,
    val errorMessage: String? = null,
    val resultNewBalance: Double? = null,
    val resultDisbursedAmount: Double? = null,
    // 实名认证弹窗
    val showVerificationDialog: Boolean = false,
    val verificationParticipantId: Int? = null,
) {
    val feeRate: Double get() = 0.05
    val feeAmount: Double get() = (selectedAmount ?: 0) * feeRate
    val disbursedAmount: Double get() = (selectedAmount ?: 0) - feeAmount
    val canSubmit: Boolean
        get() = cardUid != null && selectedAmount != null && paperworkConfirmed && !isLoading
}

// ============================================================================
// 银行柜员操作界面
// ============================================================================
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BankTellerScreen(
    state: BankTellerUiState,
    onAmountSelected: (Int) -> Unit,
    onPaperworkChecked: (Boolean) -> Unit,
    onConfirmIssuance: () -> Unit,
    onReset: () -> Unit,
    onDismissError: () -> Unit,
    onLogout: () -> Unit = {},
    onDismissVerification: () -> Unit = {},
    onSubmitVerification: (String, String) -> Unit = { _, _ -> },
) {
    Scaffold(
        containerColor = BankColors.NavyDeep,
        topBar = {
            BankTopBar(onLogout = onLogout)
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp, vertical = 12.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            // NFC 感应区
            NfcScanSection(cardDetected = state.cardUid != null)

            Spacer(modifier = Modifier.height(16.dp))

            // 贴卡后显示的放款表单
            AnimatedVisibility(
                visible = state.cardUid != null,
                enter = fadeIn() + expandVertically(),
                exit = fadeOut() + shrinkVertically(),
            ) {
                Column {
                    // 持卡人信息
                    CardHolderInfoSection(
                        cardUid = state.cardUid ?: "",
                        participantName = state.participantName ?: "识别中...",
                    )

                    Spacer(modifier = Modifier.height(20.dp))

                    // 放款金额选择
                    AmountSelectionSection(
                        selectedAmount = state.selectedAmount,
                        onAmountSelected = onAmountSelected,
                    )

                    Spacer(modifier = Modifier.height(20.dp))

                    // 动态结算面板
                    AnimatedVisibility(
                        visible = state.selectedAmount != null,
                        enter = fadeIn() + expandVertically(),
                        exit = fadeOut() + shrinkVertically(),
                    ) {
                        SettlementPanel(
                            principal = state.selectedAmount ?: 0,
                            feeAmount = state.feeAmount,
                            disbursedAmount = state.disbursedAmount,
                        )
                    }

                    Spacer(modifier = Modifier.height(20.dp))

                    // 安全确认区
                    SafetyConfirmSection(
                        checked = state.paperworkConfirmed,
                        onCheckedChange = onPaperworkChecked,
                    )

                    Spacer(modifier = Modifier.height(24.dp))

                    // 确认按钮
                    IssuanceButton(
                        enabled = state.canSubmit,
                        isLoading = state.isLoading,
                        onClick = onConfirmIssuance,
                    )
                }
            }

            // 成功结果展示
            if (state.isSuccess) {
                Spacer(modifier = Modifier.height(24.dp))
                SuccessResultCard(
                    disbursedAmount = state.resultDisbursedAmount ?: 0.0,
                    newBalance = state.resultNewBalance ?: 0.0,
                    onReset = onReset,
                )
            }
        }
    }

    // 错误弹窗
    if (state.errorMessage != null) {
        AlertDialog(
            onDismissRequest = onDismissError,
            containerColor = BankColors.NavySurface,
            titleContentColor = BankColors.ErrorRed,
            textContentColor = BankColors.TextPrimary,
            title = { Text("操作失败") },
            text = { Text(state.errorMessage) },
            confirmButton = {
                TextButton(onClick = onDismissError) {
                    Text("确定", color = BankColors.Platinum)
                }
            },
        )
    }

    // 实名认证弹窗
    if (state.showVerificationDialog) {
        BankVerificationDialog(
            onDismiss = onDismissVerification,
            onConfirm = onSubmitVerification,
        )
    }
}

// ============================================================================
// 顶部栏
// ============================================================================
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun BankTopBar(onLogout: () -> Unit) {
    TopAppBar(
        title = {
            Column {
                Text(
                    text = "中央银行 - 信用垫资发行终端",
                    color = BankColors.PlatinumBright,
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp,
                )
                Text(
                    text = "CENTRAL BANK · CREDIT ADVANCE TERMINAL",
                    color = BankColors.PlatinumDim,
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
                    tint = BankColors.PlatinumDim,
                )
            }
        },
        colors = TopAppBarDefaults.topAppBarColors(
            containerColor = BankColors.NavyDeep,
        ),
    )
}

// ============================================================================
// NFC 感应区 — 带脉冲动画
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

    BankCard(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            if (!cardDetected) {
                // NFC 等待动画
                Box(
                    contentAlignment = Alignment.Center,
                    modifier = Modifier.size(100.dp),
                ) {
                    // 外圈脉冲
                    Canvas(modifier = Modifier.size(100.dp)) {
                        drawCircle(
                            color = BankColors.Platinum.copy(alpha = pulseAlpha * 0.3f),
                            radius = size.minDimension / 2 * pulseScale,
                            style = Stroke(width = 2.dp.toPx()),
                        )
                    }
                    // 内圈
                    Canvas(modifier = Modifier.size(60.dp)) {
                        drawCircle(
                            color = BankColors.Platinum.copy(alpha = 0.6f),
                            radius = size.minDimension / 2,
                            style = Stroke(width = 1.5.dp.toPx()),
                        )
                    }
                    // NFC 图标
                    Icon(
                        Icons.Default.Nfc,
                        contentDescription = "NFC",
                        tint = BankColors.Platinum.copy(alpha = pulseAlpha),
                        modifier = Modifier.size(36.dp),
                    )
                }
                Spacer(modifier = Modifier.height(12.dp))
                Text(
                    text = "请将学生 NFC 卡片贴近设备",
                    color = BankColors.TextSecondary,
                    fontSize = 14.sp,
                )
                Text(
                    text = "AWAITING CARD CONTACT",
                    color = BankColors.TextDim,
                    fontSize = 10.sp,
                    letterSpacing = 2.sp,
                )
            } else {
                // 已识别
                Icon(
                    Icons.Default.CheckCircle,
                    contentDescription = "已识别",
                    tint = BankColors.SuccessGreen,
                    modifier = Modifier.size(48.dp),
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "卡片已识别",
                    color = BankColors.SuccessGreen,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Medium,
                )
            }
        }
    }
}

// ============================================================================
// 持卡人信息展示
// ============================================================================
@Composable
private fun CardHolderInfoSection(cardUid: String, participantName: String) {
    BankCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            SectionLabel("持卡人信息")
            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                InfoField(label = "卡片 UID", value = cardUid)
                InfoField(
                    label = "学生姓名",
                    value = maskName(participantName),
                )
            }
        }
    }
}

// ============================================================================
// 放款金额输入（自由输入，无金额限制）
// ============================================================================
@Composable
private fun AmountSelectionSection(
    selectedAmount: Int?,
    onAmountSelected: (Int) -> Unit,
) {
    var inputText by remember { mutableStateOf(selectedAmount?.toString() ?: "") }
    val quickAmounts = listOf(50, 100, 200, 500)

    BankCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            SectionLabel("放款金额")
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "输入任意金额（元），扣除5%手续费后到账",
                color = BankColors.TextDim,
                fontSize = 11.sp,
            )
            Spacer(modifier = Modifier.height(16.dp))

            // 自由输入框
            OutlinedTextField(
                value = inputText,
                onValueChange = { value ->
                    // 只允许数字
                    val filtered = value.filter { it.isDigit() }
                    inputText = filtered
                    val amount = filtered.toIntOrNull()
                    if (amount != null && amount > 0) {
                        onAmountSelected(amount)
                    }
                },
                label = { Text("金额（元）") },
                placeholder = { Text("请输入放款金额") },
                prefix = { Text("¥ ", color = BankColors.Platinum, fontWeight = FontWeight.Bold) },
                singleLine = true,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = BankColors.PlatinumBright,
                    unfocusedTextColor = BankColors.TextPrimary,
                    focusedBorderColor = BankColors.Platinum,
                    unfocusedBorderColor = BankColors.BorderPlatinum,
                    focusedLabelColor = BankColors.Platinum,
                    unfocusedLabelColor = BankColors.TextDim,
                    cursorColor = BankColors.Platinum,
                ),
                modifier = Modifier.fillMaxWidth(),
            )

            Spacer(modifier = Modifier.height(12.dp))

            // 快捷金额按钮
            Text(
                text = "快捷选择",
                color = BankColors.TextDim,
                fontSize = 11.sp,
            )
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                quickAmounts.forEach { amount ->
                    val isSelected = selectedAmount == amount
                    AmountChip(
                        amount = amount,
                        isSelected = isSelected,
                        onClick = {
                            inputText = amount.toString()
                            onAmountSelected(amount)
                        },
                        modifier = Modifier.weight(1f),
                    )
                }
            }
        }
    }
}

@Composable
private fun AmountChip(
    amount: Int,
    isSelected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val bgColor = if (isSelected) BankColors.Platinum else Color.Transparent
    val textColor = if (isSelected) BankColors.NavyDeep else BankColors.Platinum
    val borderColor = if (isSelected) BankColors.Platinum else BankColors.BorderPlatinum

    Box(
        modifier = modifier
            .clip(RoundedCornerShape(8.dp))
            .border(1.dp, borderColor, RoundedCornerShape(8.dp))
            .background(bgColor)
            .clickable { onClick() }
            .padding(vertical = 14.dp),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            text = "¥$amount",
            color = textColor,
            fontSize = 16.sp,
            fontWeight = FontWeight.Bold,
        )
    }
}

// ============================================================================
// 动态结算面板（重点视觉凸显）
// ============================================================================
@Composable
private fun SettlementPanel(
    principal: Int,
    feeAmount: Double,
    disbursedAmount: Double,
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(
                width = 1.5.dp,
                brush = Brush.linearGradient(
                    colors = listOf(BankColors.Platinum, BankColors.PlatinumDim),
                ),
                shape = RoundedCornerShape(12.dp),
            )
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        BankColors.NavyElevated,
                        BankColors.NavySurface,
                    ),
                ),
            )
            .padding(20.dp),
    ) {
        Column {
            Text(
                text = "结算明细",
                color = BankColors.PlatinumBright,
                fontSize = 13.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.sp,
            )
            Spacer(modifier = Modifier.height(16.dp))

            // 名义借款
            SettlementRow(
                label = "名义借款金额",
                value = "¥${principal}",
                valueColor = BankColors.TextPrimary,
            )

            Spacer(modifier = Modifier.height(8.dp))

            // 手续费
            SettlementRow(
                label = "扣除5%手续费",
                value = "-¥${"%.2f".format(feeAmount)}",
                valueColor = BankColors.WarningAmber,
            )

            Spacer(modifier = Modifier.height(12.dp))

            // 分割线
            Divider(
                color = BankColors.BorderPlatinum,
                thickness = 1.dp,
            )

            Spacer(modifier = Modifier.height(12.dp))

            // 实际到账
            SettlementRow(
                label = "实际到账额度",
                value = "¥${"%.2f".format(disbursedAmount)}",
                valueColor = BankColors.SuccessGreen,
                isBold = true,
                fontSize = 20.sp,
            )
        }
    }
}

@Composable
private fun SettlementRow(
    label: String,
    value: String,
    valueColor: Color,
    isBold: Boolean = false,
    fontSize: androidx.compose.ui.unit.TextUnit = 16.sp,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = label,
            color = BankColors.TextSecondary,
            fontSize = 13.sp,
        )
        Text(
            text = value,
            color = valueColor,
            fontSize = fontSize,
            fontWeight = if (isBold) FontWeight.Bold else FontWeight.Medium,
        )
    }
}

// ============================================================================
// 安全确认区
// ============================================================================
@Composable
private fun SafetyConfirmSection(
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .border(
                width = 1.dp,
                color = if (checked) BankColors.SuccessGreen.copy(alpha = 0.5f)
                else BankColors.WarningAmber.copy(alpha = 0.5f),
                shape = RoundedCornerShape(8.dp),
            )
            .background(
                if (checked) BankColors.SuccessGreen.copy(alpha = 0.05f)
                else BankColors.WarningAmber.copy(alpha = 0.05f),
            )
            .clickable { onCheckedChange(!checked) }
            .padding(16.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Checkbox(
                checked = checked,
                onCheckedChange = onCheckedChange,
                colors = CheckboxDefaults.colors(
                    checkedColor = BankColors.SuccessGreen,
                    uncheckedColor = BankColors.WarningAmber,
                    checkmarkColor = Color.White,
                ),
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = "我已确认该生已签署纸质《垫资承诺书》并按下指纹",
                color = if (checked) BankColors.SuccessGreen else BankColors.WarningAmber,
                fontSize = 13.sp,
                fontWeight = FontWeight.Medium,
            )
        }
    }
}

// ============================================================================
// 确认发行按钮
// ============================================================================
@Composable
private fun IssuanceButton(
    enabled: Boolean,
    isLoading: Boolean,
    onClick: () -> Unit,
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier
            .fillMaxWidth()
            .height(56.dp),
        shape = RoundedCornerShape(12.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = BankColors.Platinum,
            contentColor = BankColors.NavyDeep,
            disabledContainerColor = BankColors.NavyLight,
            disabledContentColor = BankColors.TextDim,
        ),
        elevation = ButtonDefaults.buttonElevation(
            defaultElevation = 4.dp,
            pressedElevation = 1.dp,
        ),
    ) {
        if (isLoading) {
            CircularProgressIndicator(
                modifier = Modifier.size(24.dp),
                color = BankColors.NavyDeep,
                strokeWidth = 2.dp,
            )
            Spacer(modifier = Modifier.width(12.dp))
            Text("处理中...", fontWeight = FontWeight.Bold, fontSize = 16.sp)
        } else {
            Icon(
                Icons.Default.AccountBalance,
                contentDescription = null,
                modifier = Modifier.size(20.dp),
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = "确认发行信用额度",
                fontWeight = FontWeight.Bold,
                fontSize = 16.sp,
            )
        }
    }
}

// ============================================================================
// 成功结果卡片
// ============================================================================
@Composable
private fun SuccessResultCard(
    disbursedAmount: Double,
    newBalance: Double,
    onReset: () -> Unit,
) {
    BankCard(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Icon(
                Icons.Default.Verified,
                contentDescription = "成功",
                tint = BankColors.SuccessGreen,
                modifier = Modifier.size(56.dp),
            )
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = "信用额度发行成功",
                color = BankColors.SuccessGreen,
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly,
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("实际到账", color = BankColors.TextSecondary, fontSize = 12.sp)
                    Text(
                        "¥${"%.2f".format(disbursedAmount)}",
                        color = BankColors.PlatinumBright,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold,
                    )
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("账户余额", color = BankColors.TextSecondary, fontSize = 12.sp)
                    Text(
                        "¥${"%.2f".format(newBalance)}",
                        color = BankColors.PlatinumBright,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold,
                    )
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            OutlinedButton(
                onClick = onReset,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp),
                colors = ButtonDefaults.outlinedButtonColors(
                    contentColor = BankColors.Platinum,
                ),
                border = ButtonDefaults.outlinedButtonBorder.copy(
                    brush = Brush.linearGradient(
                        listOf(BankColors.Platinum, BankColors.PlatinumDim),
                    ),
                ),
            ) {
                Text("办理下一笔", fontWeight = FontWeight.Medium)
            }
        }
    }
}

// ============================================================================
// 通用组件
// ============================================================================

/** 银行风格卡片容器 */
@Composable
private fun BankCard(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    Box(
        modifier = modifier
            .shadow(8.dp, RoundedCornerShape(12.dp))
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, BankColors.BorderPlatinum, RoundedCornerShape(12.dp))
            .background(BankColors.NavySurface)
    ) {
        content()
    }
}

/** 区块标签 */
@Composable
private fun SectionLabel(text: String) {
    Text(
        text = text,
        color = BankColors.PlatinumBright,
        fontSize = 13.sp,
        fontWeight = FontWeight.Bold,
        letterSpacing = 0.5.sp,
    )
}

/** 信息字段 */
@Composable
private fun InfoField(label: String, value: String) {
    Column {
        Text(
            text = label,
            color = BankColors.TextDim,
            fontSize = 11.sp,
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = value,
            color = BankColors.TextPrimary,
            fontSize = 14.sp,
            fontWeight = FontWeight.Medium,
        )
    }
}

/** 姓名脱敏：保留首字，其余用 * 替代 */
private fun maskName(name: String): String {
    if (name.length <= 1) return name
    return name.first() + "*".repeat(name.length - 1)
}

// ============================================================================
// 实名认证弹窗
// ============================================================================
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun BankVerificationDialog(
    onDismiss: () -> Unit,
    onConfirm: (String, String) -> Unit,
) {
    var name by remember { mutableStateOf("") }
    var className by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = BankColors.NavySurface,
        titleContentColor = BankColors.PlatinumBright,
        textContentColor = BankColors.TextPrimary,
        title = {
            Text("实名认证", fontWeight = FontWeight.Bold)
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(
                    text = "该卡片尚未实名，办理信用垫资需先完成实名认证",
                    color = BankColors.TextSecondary,
                    fontSize = 13.sp,
                )
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("姓名（必填）") },
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = BankColors.TextPrimary,
                        unfocusedTextColor = BankColors.TextPrimary,
                        focusedBorderColor = BankColors.Platinum,
                        unfocusedBorderColor = BankColors.BorderPlatinum,
                        focusedLabelColor = BankColors.Platinum,
                        unfocusedLabelColor = BankColors.TextDim,
                        cursorColor = BankColors.Platinum,
                    ),
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = className,
                    onValueChange = { className = it },
                    label = { Text("班级（必填）") },
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = BankColors.TextPrimary,
                        unfocusedTextColor = BankColors.TextPrimary,
                        focusedBorderColor = BankColors.Platinum,
                        unfocusedBorderColor = BankColors.BorderPlatinum,
                        focusedLabelColor = BankColors.Platinum,
                        unfocusedLabelColor = BankColors.TextDim,
                        cursorColor = BankColors.Platinum,
                    ),
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = { if (name.isNotBlank() && className.isNotBlank()) onConfirm(name.trim(), className.trim()) },
                enabled = name.isNotBlank() && className.isNotBlank(),
            ) {
                Text(
                    "确认",
                    color = if (name.isNotBlank() && className.isNotBlank()) BankColors.Platinum else BankColors.TextDim,
                )
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("取消", color = BankColors.TextSecondary)
            }
        },
    )
}
