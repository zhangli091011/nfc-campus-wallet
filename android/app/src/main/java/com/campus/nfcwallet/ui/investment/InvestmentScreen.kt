package com.campus.nfcwallet.ui.investment

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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay

// ============================================================================
// 主题配色（黑金风）
// ============================================================================
object InvestmentColors {
    val Background = Color(0xFF0A0A0F)
    val SurfaceDeep = Color(0xFF14141C)
    val SurfaceElevated = Color(0xFF1A1A24)
    val Gold = Color(0xFFFFD700)
    val GoldSoft = Color(0xFFE6B800)
    val GoldDim = Color(0xFF8C7200)
    val TextPrimary = Color(0xFFF5F5F5)
    val TextSecondary = Color(0xFFB0B0B0)
    val TextDim = Color(0xFF707070)
    val ErrorRed = Color(0xFFFF4444)
    val SuccessGreen = Color(0xFF00FF88)
    val BorderGold = Color(0x66FFD700)
}

// ============================================================================
// UI State
// ============================================================================
data class BoothOption(val id: Int, val name: String, val className: String)

data class HoldingInfo(
    val boothId: Int,
    val boothName: String,
    val className: String,
    val shares: Int,
    val currentPrice: Double,
    val marketValue: Double,
)

data class InvestmentUiState(
    val cardUid: String? = null,
    val participantName: String? = null,
    val accountBalance: Double = 0.0,  // 主账户余额（元）
    val booths: List<BoothOption> = emptyList(),
    val selectedBooth: BoothOption? = null,
    val sharesInput: String = "",
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val successMessage: String? = null,
    // 卖出相关
    val currentTab: Int = 0,  // 0=买入, 1=卖出
    val holdings: List<HoldingInfo> = emptyList(),
    val selectedHolding: HoldingInfo? = null,
    val sellSharesInput: String = "",
    // 实名认证弹窗
    val showVerificationDialog: Boolean = false,
    val verificationParticipantId: Int? = null,
)

// ============================================================================
// 投资办理界面
// ============================================================================
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InvestmentScreen(
    state: InvestmentUiState,
    onBoothSelected: (BoothOption) -> Unit,
    onSharesChanged: (String) -> Unit,
    onConfirmInvestment: () -> Unit,
    onDismissMessage: () -> Unit,
    onLogout: () -> Unit = {},
    onTabChanged: (Int) -> Unit = {},
    onHoldingSelected: (HoldingInfo) -> Unit = {},
    onSellSharesChanged: (String) -> Unit = {},
    onConfirmSell: () -> Unit = {},
    onDismissVerification: () -> Unit = {},
    onSubmitVerification: (String, String) -> Unit = { _, _ -> },
    getCurrentPrice: (Int) -> Double = { 5.0 },
) {
    // 浮动买入价 = 当前动态股价
    val buyPricePerShare = state.selectedBooth?.let { getCurrentPrice(it.id) } ?: 5.0
    val totalAmount = state.sharesInput.toIntOrNull()?.let { it * buyPricePerShare } ?: 0.0
    // 卖出使用所选持仓的当前动态股价（预估结算价）
    val sellPricePerShare = state.selectedHolding?.let { getCurrentPrice(it.boothId) } ?: 5.0
    val sellTotal = state.sellSharesInput.toIntOrNull()?.let { it * sellPricePerShare } ?: 0.0

    Scaffold(
        containerColor = InvestmentColors.Background,
        topBar = {
            InvestmentTopBar(onLogout = onLogout)
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // NFC 感应区
            NfcSensorCard(
                cardUid = state.cardUid,
                participantName = state.participantName,
                isWaiting = state.cardUid == null,
            )

            // 余额信息（卡片读取后显示）
            AnimatedVisibility(
                visible = state.participantName != null,
                enter = fadeIn() + expandVertically(),
                exit = fadeOut() + shrinkVertically(),
            ) {
                BalanceDisplayCard(
                    accountBalance = state.accountBalance,
                )
            }

            // 买入/卖出 Tab 切换
            AnimatedVisibility(
                visible = state.participantName != null,
                enter = fadeIn() + expandVertically(),
                exit = fadeOut() + shrinkVertically(),
            ) {
                TradeTabRow(
                    selectedTab = state.currentTab,
                    onTabSelected = onTabChanged,
                )
            }

            // 买入表单
            AnimatedVisibility(
                visible = state.participantName != null && state.currentTab == 0,
                enter = fadeIn() + expandVertically(),
                exit = fadeOut() + shrinkVertically(),
            ) {
                InvestmentFormCard(
                    booths = state.booths,
                    selectedBooth = state.selectedBooth,
                    sharesInput = state.sharesInput,
                    pricePerShare = buyPricePerShare,
                    totalAmount = totalAmount,
                    onBoothSelected = onBoothSelected,
                    onSharesChanged = onSharesChanged,
                    getCurrentPrice = getCurrentPrice,
                )
            }

            // 确认买入按钮
            AnimatedVisibility(
                visible = state.participantName != null && state.currentTab == 0,
                enter = fadeIn() + expandVertically(),
            ) {
                ConfirmButton(
                    enabled = !state.isLoading &&
                            state.selectedBooth != null &&
                            state.sharesInput.toIntOrNull()?.let { it > 0 } == true &&
                            totalAmount <= state.accountBalance,
                    isLoading = state.isLoading,
                    onClick = onConfirmInvestment,
                    label = "确认买入",
                )
            }

            // 卖出表单
            AnimatedVisibility(
                visible = state.participantName != null && state.currentTab == 1,
                enter = fadeIn() + expandVertically(),
                exit = fadeOut() + shrinkVertically(),
            ) {
                SellFormCard(
                    holdings = state.holdings,
                    selectedHolding = state.selectedHolding,
                    sellSharesInput = state.sellSharesInput,
                    pricePerShare = sellPricePerShare,
                    sellTotal = sellTotal,
                    onHoldingSelected = onHoldingSelected,
                    onSellSharesChanged = onSellSharesChanged,
                )
            }

            // 确认卖出按钮
            AnimatedVisibility(
                visible = state.participantName != null && state.currentTab == 1,
                enter = fadeIn() + expandVertically(),
            ) {
                ConfirmButton(
                    enabled = !state.isLoading &&
                            state.selectedHolding != null &&
                            state.sellSharesInput.toIntOrNull()?.let { it > 0 } == true &&
                            (state.sellSharesInput.toIntOrNull() ?: 0) <= (state.selectedHolding?.shares ?: 0),
                    isLoading = state.isLoading,
                    onClick = onConfirmSell,
                    label = "确认抛售",
                    isSell = true,
                )
            }

            Spacer(Modifier.height(24.dp))
        }

        // 消息提示
        if (state.errorMessage != null) {
            HighTechSnackbar(
                message = state.errorMessage,
                isError = true,
                onDismiss = onDismissMessage,
            )
        }
        if (state.successMessage != null) {
            HighTechSnackbar(
                message = state.successMessage,
                isError = false,
                onDismiss = onDismissMessage,
            )
        }
    }

    // 实名认证弹窗
    if (state.showVerificationDialog) {
        VerificationDialog(
            onDismiss = onDismissVerification,
            onConfirm = onSubmitVerification,
        )
    }
}

// ============================================================================
// 顶部 Header
// ============================================================================
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun InvestmentTopBar(onLogout: () -> Unit) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        InvestmentColors.SurfaceDeep,
                        InvestmentColors.Background,
                    )
                )
            )
            .border(
                width = 0.5.dp,
                brush = Brush.horizontalGradient(
                    colors = listOf(
                        Color.Transparent,
                        InvestmentColors.Gold,
                        Color.Transparent,
                    )
                ),
                shape = RoundedCornerShape(0.dp),
            )
            .padding(horizontal = 16.dp, vertical = 18.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // 金色装饰条
            Box(
                modifier = Modifier
                    .width(4.dp)
                    .height(36.dp)
                    .background(
                        Brush.verticalGradient(
                            colors = listOf(
                                InvestmentColors.GoldDim,
                                InvestmentColors.Gold,
                                InvestmentColors.GoldDim,
                            )
                        )
                    )
            )
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "官方中央银行",
                    style = TextStyle(
                        color = InvestmentColors.Gold,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 2.sp,
                    ),
                )
                Text(
                    text = "模拟投资办理终端",
                    style = TextStyle(
                        color = InvestmentColors.TextSecondary,
                        fontSize = 12.sp,
                        letterSpacing = 1.sp,
                    ),
                )
            }
            IconButton(onClick = onLogout) {
                Icon(
                    imageVector = Icons.Default.Logout,
                    contentDescription = "退出",
                    tint = InvestmentColors.GoldSoft,
                )
            }
        }
    }
}

// ============================================================================
// NFC 感应区
// ============================================================================
@Composable
private fun NfcSensorCard(
    cardUid: String?,
    participantName: String?,
    isWaiting: Boolean,
) {
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
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 1.0f,
        targetValue = 1.4f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Restart,
        ),
        label = "scale",
    )

    TechCard(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            if (isWaiting) {
                // 等待贴卡状态
                Box(
                    modifier = Modifier.size(140.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    // 外圈脉冲
                    Canvas(modifier = Modifier.fillMaxSize()) {
                        val strokeWidth = 2.dp.toPx()
                        for (i in 0..2) {
                            val scale = 1f + i * 0.2f * pulseScale
                            drawCircle(
                                color = InvestmentColors.Gold.copy(alpha = pulseAlpha / (i + 1)),
                                radius = size.minDimension / 2 * scale,
                                style = Stroke(width = strokeWidth),
                            )
                        }
                    }
                    // 中心图标
                    Icon(
                        imageVector = Icons.Default.Nfc,
                        contentDescription = "NFC",
                        tint = InvestmentColors.Gold,
                        modifier = Modifier.size(64.dp),
                    )
                }
                Spacer(Modifier.height(16.dp))
                Text(
                    text = "请将学生卡贴近设备",
                    style = TextStyle(
                        color = InvestmentColors.TextPrimary,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Medium,
                        letterSpacing = 1.sp,
                    ),
                )
                Text(
                    text = "等待 NFC 感应...",
                    style = TextStyle(
                        color = InvestmentColors.TextDim,
                        fontSize = 12.sp,
                    ),
                    modifier = Modifier.padding(top = 6.dp),
                )
            } else {
                // 已读取状态
                Icon(
                    imageVector = Icons.Default.CheckCircle,
                    contentDescription = "Success",
                    tint = InvestmentColors.SuccessGreen,
                    modifier = Modifier.size(56.dp),
                )
                Spacer(Modifier.height(12.dp))
                Text(
                    text = "✓ 识别成功",
                    style = TextStyle(
                        color = InvestmentColors.SuccessGreen,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp,
                    ),
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = participantName ?: "",
                    style = TextStyle(
                        color = InvestmentColors.Gold,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.SemiBold,
                    ),
                )
                Text(
                    text = "卡号: ${cardUid ?: "-"}",
                    style = TextStyle(
                        color = InvestmentColors.TextSecondary,
                        fontSize = 12.sp,
                        letterSpacing = 1.sp,
                    ),
                    modifier = Modifier.padding(top = 4.dp),
                )
            }
        }
    }
}

// ============================================================================
// 余额展示卡片
// ============================================================================
@Composable
private fun BalanceDisplayCard(
    accountBalance: Double,
) {
    TechCard(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.Center,
        ) {
            BalanceItem(
                label = "账户余额",
                amount = accountBalance,
                color = InvestmentColors.Gold,
                modifier = Modifier.fillMaxWidth(),
            )
        }
    }
}

@Composable
private fun BalanceItem(
    label: String,
    amount: Double,
    color: Color,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = label,
            style = TextStyle(
                color = InvestmentColors.TextDim,
                fontSize = 12.sp,
                letterSpacing = 1.sp,
            ),
        )
        Spacer(Modifier.height(4.dp))
        Text(
            text = String.format("¥%.2f", amount),
            style = TextStyle(
                color = color,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
            ),
        )
    }
}

// ============================================================================
// 投资表单
// ============================================================================
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun InvestmentFormCard(
    booths: List<BoothOption>,
    selectedBooth: BoothOption?,
    sharesInput: String,
    pricePerShare: Double,
    totalAmount: Double,
    onBoothSelected: (BoothOption) -> Unit,
    onSharesChanged: (String) -> Unit,
    getCurrentPrice: (Int) -> Double = { 5.0 },
) {
    TechCard(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
        ) {
            SectionLabel(text = "投资摊位")
            Spacer(Modifier.height(8.dp))
            BoothDropdown(
                booths = booths,
                selectedBooth = selectedBooth,
                onBoothSelected = onBoothSelected,
                getCurrentPrice = getCurrentPrice,
            )

            Spacer(Modifier.height(20.dp))
            SectionLabel(text = "购买股数")
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = sharesInput,
                onValueChange = { newVal ->
                    if (newVal.all { it.isDigit() } && newVal.length <= 6) {
                        onSharesChanged(newVal)
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                placeholder = {
                    Text(
                        "请输入股数",
                        color = InvestmentColors.TextDim,
                    )
                },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = InvestmentColors.TextPrimary,
                    unfocusedTextColor = InvestmentColors.TextPrimary,
                    focusedBorderColor = InvestmentColors.Gold,
                    unfocusedBorderColor = InvestmentColors.BorderGold,
                    cursorColor = InvestmentColors.Gold,
                    focusedContainerColor = InvestmentColors.Background,
                    unfocusedContainerColor = InvestmentColors.Background,
                ),
                singleLine = true,
                shape = RoundedCornerShape(8.dp),
            )

            Spacer(Modifier.height(16.dp))

            // 总额显示
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(8.dp))
                    .background(InvestmentColors.Background)
                    .border(
                        1.dp,
                        InvestmentColors.BorderGold,
                        RoundedCornerShape(8.dp),
                    )
                    .padding(horizontal = 16.dp, vertical = 14.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column {
                    Text(
                        "单价",
                        style = TextStyle(
                            color = InvestmentColors.TextDim,
                            fontSize = 10.sp,
                        ),
                    )
                    Text(
                        String.format("¥%.2f / 股", pricePerShare),
                        style = TextStyle(
                            color = InvestmentColors.TextSecondary,
                            fontSize = 13.sp,
                        ),
                    )
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text(
                        "合计金额",
                        style = TextStyle(
                            color = InvestmentColors.GoldDim,
                            fontSize = 10.sp,
                            letterSpacing = 1.sp,
                        ),
                    )
                    Text(
                        String.format("¥%.2f", totalAmount),
                        style = TextStyle(
                            color = InvestmentColors.Gold,
                            fontSize = 22.sp,
                            fontWeight = FontWeight.Bold,
                        ),
                    )
                }
            }
        }
    }
}

@Composable
private fun SectionLabel(text: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(
            modifier = Modifier
                .width(3.dp)
                .height(14.dp)
                .background(InvestmentColors.Gold)
        )
        Spacer(Modifier.width(8.dp))
        Text(
            text = text,
            style = TextStyle(
                color = InvestmentColors.TextPrimary,
                fontSize = 14.sp,
                fontWeight = FontWeight.Medium,
                letterSpacing = 1.sp,
            ),
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun BoothDropdown(
    booths: List<BoothOption>,
    selectedBooth: BoothOption?,
    onBoothSelected: (BoothOption) -> Unit,
    getCurrentPrice: (Int) -> Double = { 5.0 },
) {
    var expanded by remember { mutableStateOf(false) }

    ExposedDropdownMenuBox(
        expanded = expanded,
        onExpandedChange = { expanded = it },
    ) {
        OutlinedTextField(
            value = selectedBooth?.let { "${it.name} - ${it.className}" } ?: "",
            onValueChange = {},
            readOnly = true,
            placeholder = {
                Text(
                    "请选择投资摊位",
                    color = InvestmentColors.TextDim,
                )
            },
            trailingIcon = {
                Icon(
                    imageVector = if (expanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                    contentDescription = null,
                    tint = InvestmentColors.Gold,
                )
            },
            colors = OutlinedTextFieldDefaults.colors(
                focusedTextColor = InvestmentColors.TextPrimary,
                unfocusedTextColor = InvestmentColors.TextPrimary,
                focusedBorderColor = InvestmentColors.Gold,
                unfocusedBorderColor = InvestmentColors.BorderGold,
                focusedContainerColor = InvestmentColors.Background,
                unfocusedContainerColor = InvestmentColors.Background,
            ),
            shape = RoundedCornerShape(8.dp),
            modifier = Modifier
                .menuAnchor()
                .fillMaxWidth(),
        )
        ExposedDropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false },
            modifier = Modifier.background(InvestmentColors.SurfaceElevated),
        ) {
            if (booths.isEmpty()) {
                DropdownMenuItem(
                    text = {
                        Text(
                            "暂无可投资摊位",
                            color = InvestmentColors.TextDim,
                        )
                    },
                    onClick = {},
                )
            } else {
                booths.forEach { booth ->
                    DropdownMenuItem(
                        text = {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(
                                        booth.name,
                                        color = InvestmentColors.TextPrimary,
                                        fontWeight = FontWeight.Medium,
                                    )
                                    Text(
                                        booth.className,
                                        color = InvestmentColors.TextDim,
                                        fontSize = 11.sp,
                                    )
                                }
                                Text(
                                    String.format("¥%.2f", getCurrentPrice(booth.id)),
                                    color = InvestmentColors.Gold,
                                    fontSize = 13.sp,
                                    fontWeight = FontWeight.Bold,
                                )
                            }
                        },
                        onClick = {
                            onBoothSelected(booth)
                            expanded = false
                        },
                    )
                }
            }
        }
    }
}

// ============================================================================
// 确认按钮
// ============================================================================
@Composable
private fun ConfirmButton(
    enabled: Boolean,
    isLoading: Boolean,
    onClick: () -> Unit,
    label: String = "确认投资",
    isSell: Boolean = false,
) {
    val bgColor = if (isSell) Color(0xFFFF6B35) else InvestmentColors.Gold
    val bgColorDim = if (isSell) Color(0xFF8C3A1D) else InvestmentColors.GoldDim

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(64.dp)
            .clip(RoundedCornerShape(12.dp))
            .background(
                if (enabled) {
                    Brush.horizontalGradient(
                        colors = listOf(bgColorDim, bgColor, bgColorDim)
                    )
                } else {
                    SolidColor(InvestmentColors.SurfaceElevated)
                }
            )
            .border(
                width = 1.dp,
                color = if (enabled) bgColor else InvestmentColors.TextDim,
                shape = RoundedCornerShape(12.dp),
            )
            .clickable(enabled = enabled && !isLoading) { onClick() },
        contentAlignment = Alignment.Center,
    ) {
        if (isLoading) {
            CircularProgressIndicator(
                color = InvestmentColors.Background,
                strokeWidth = 3.dp,
                modifier = Modifier.size(28.dp),
            )
        } else {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = if (isSell) Icons.Default.TrendingDown else Icons.Default.Check,
                    contentDescription = null,
                    tint = if (enabled) InvestmentColors.Background else InvestmentColors.TextDim,
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    text = label,
                    style = TextStyle(
                        color = if (enabled) InvestmentColors.Background else InvestmentColors.TextDim,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 4.sp,
                    ),
                )
            }
        }
    }
}

// ============================================================================
// 买入/卖出 Tab 切换
// ============================================================================
@Composable
private fun TradeTabRow(
    selectedTab: Int,
    onTabSelected: (Int) -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .background(InvestmentColors.SurfaceDeep)
            .border(1.dp, InvestmentColors.BorderGold, RoundedCornerShape(10.dp))
            .padding(4.dp),
        horizontalArrangement = Arrangement.SpaceEvenly,
    ) {
        // 买入 Tab
        Box(
            modifier = Modifier
                .weight(1f)
                .clip(RoundedCornerShape(8.dp))
                .background(
                    if (selectedTab == 0) InvestmentColors.Gold else Color.Transparent
                )
                .clickable { onTabSelected(0) }
                .padding(vertical = 12.dp),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = "买入",
                style = TextStyle(
                    color = if (selectedTab == 0) InvestmentColors.Background else InvestmentColors.TextSecondary,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 2.sp,
                ),
            )
        }
        // 卖出 Tab
        Box(
            modifier = Modifier
                .weight(1f)
                .clip(RoundedCornerShape(8.dp))
                .background(
                    if (selectedTab == 1) Color(0xFFFF6B35) else Color.Transparent
                )
                .clickable { onTabSelected(1) }
                .padding(vertical = 12.dp),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = "卖出",
                style = TextStyle(
                    color = if (selectedTab == 1) InvestmentColors.Background else InvestmentColors.TextSecondary,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 2.sp,
                ),
            )
        }
    }
}

// ============================================================================
// 卖出表单
// ============================================================================
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SellFormCard(
    holdings: List<HoldingInfo>,
    selectedHolding: HoldingInfo?,
    sellSharesInput: String,
    pricePerShare: Double,
    sellTotal: Double,
    onHoldingSelected: (HoldingInfo) -> Unit,
    onSellSharesChanged: (String) -> Unit,
) {
    TechCard(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
        ) {
            SectionLabel(text = "选择持仓")
            Spacer(Modifier.height(8.dp))

            if (holdings.isEmpty()) {
                Text(
                    text = "暂无持仓股票",
                    style = TextStyle(
                        color = InvestmentColors.TextDim,
                        fontSize = 14.sp,
                    ),
                    modifier = Modifier.padding(vertical = 16.dp),
                )
            } else {
                HoldingDropdown(
                    holdings = holdings,
                    selectedHolding = selectedHolding,
                    onHoldingSelected = onHoldingSelected,
                )

                if (selectedHolding != null) {
                    Spacer(Modifier.height(12.dp))
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(6.dp))
                            .background(InvestmentColors.Background)
                            .padding(12.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Text(
                            text = "可卖出",
                            style = TextStyle(color = InvestmentColors.TextDim, fontSize = 12.sp),
                        )
                        Text(
                            text = "${selectedHolding.shares} 股",
                            style = TextStyle(
                                color = InvestmentColors.SuccessGreen,
                                fontSize = 14.sp,
                                fontWeight = FontWeight.Bold,
                            ),
                        )
                    }
                }

                Spacer(Modifier.height(20.dp))
                SectionLabel(text = "卖出股数")
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(
                    value = sellSharesInput,
                    onValueChange = { newVal ->
                        if (newVal.all { it.isDigit() } && newVal.length <= 6) {
                            onSellSharesChanged(newVal)
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    placeholder = {
                        Text("请输入卖出股数", color = InvestmentColors.TextDim)
                    },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = InvestmentColors.TextPrimary,
                        unfocusedTextColor = InvestmentColors.TextPrimary,
                        focusedBorderColor = Color(0xFFFF6B35),
                        unfocusedBorderColor = InvestmentColors.BorderGold,
                        cursorColor = Color(0xFFFF6B35),
                        focusedContainerColor = InvestmentColors.Background,
                        unfocusedContainerColor = InvestmentColors.Background,
                    ),
                    singleLine = true,
                    shape = RoundedCornerShape(8.dp),
                )

                Spacer(Modifier.height(16.dp))

                // 卖出总额显示
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(InvestmentColors.Background)
                        .border(1.dp, InvestmentColors.BorderGold, RoundedCornerShape(8.dp))
                        .padding(horizontal = 16.dp, vertical = 14.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column {
                        Text(
                            "当前股价",
                            style = TextStyle(color = InvestmentColors.TextDim, fontSize = 10.sp),
                        )
                        Text(
                            String.format("¥%.2f / 股", pricePerShare),
                            style = TextStyle(color = InvestmentColors.TextSecondary, fontSize = 13.sp),
                        )
                    }
                    Column(horizontalAlignment = Alignment.End) {
                        Text(
                            "预计到账",
                            style = TextStyle(
                                color = Color(0xFF8C3A1D),
                                fontSize = 10.sp,
                                letterSpacing = 1.sp,
                            ),
                        )
                        Text(
                            String.format("¥%.2f", sellTotal),
                            style = TextStyle(
                                color = Color(0xFFFF6B35),
                                fontSize = 22.sp,
                                fontWeight = FontWeight.Bold,
                            ),
                        )
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun HoldingDropdown(
    holdings: List<HoldingInfo>,
    selectedHolding: HoldingInfo?,
    onHoldingSelected: (HoldingInfo) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }

    ExposedDropdownMenuBox(
        expanded = expanded,
        onExpandedChange = { expanded = it },
    ) {
        OutlinedTextField(
            value = selectedHolding?.let { "${it.boothName} (${it.shares}股)" } ?: "",
            onValueChange = {},
            readOnly = true,
            placeholder = {
                Text("请选择要卖出的持仓", color = InvestmentColors.TextDim)
            },
            trailingIcon = {
                Icon(
                    imageVector = if (expanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                    contentDescription = null,
                    tint = Color(0xFFFF6B35),
                )
            },
            colors = OutlinedTextFieldDefaults.colors(
                focusedTextColor = InvestmentColors.TextPrimary,
                unfocusedTextColor = InvestmentColors.TextPrimary,
                focusedBorderColor = Color(0xFFFF6B35),
                unfocusedBorderColor = InvestmentColors.BorderGold,
                focusedContainerColor = InvestmentColors.Background,
                unfocusedContainerColor = InvestmentColors.Background,
            ),
            shape = RoundedCornerShape(8.dp),
            modifier = Modifier
                .menuAnchor()
                .fillMaxWidth(),
        )
        ExposedDropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false },
            modifier = Modifier.background(InvestmentColors.SurfaceElevated),
        ) {
            holdings.forEach { holding ->
                DropdownMenuItem(
                    text = {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                        ) {
                            Column {
                                Text(
                                    holding.boothName,
                                    color = InvestmentColors.TextPrimary,
                                    fontWeight = FontWeight.Medium,
                                )
                                Text(
                                    holding.className,
                                    color = InvestmentColors.TextDim,
                                    fontSize = 11.sp,
                                )
                            }
                            Text(
                                "${holding.shares}股",
                                color = InvestmentColors.SuccessGreen,
                                fontWeight = FontWeight.Bold,
                            )
                        }
                    },
                    onClick = {
                        onHoldingSelected(holding)
                        expanded = false
                    },
                )
            }
        }
    }
}

// ============================================================================
// 高科技感 Snackbar
// ============================================================================
@Composable
private fun HighTechSnackbar(
    message: String,
    isError: Boolean,
    onDismiss: () -> Unit,
) {
    LaunchedEffect(message) {
        delay(3500)
        onDismiss()
    }

    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.BottomCenter,
    ) {
        Row(
            modifier = Modifier
                .padding(20.dp)
                .clip(RoundedCornerShape(10.dp))
                .background(InvestmentColors.SurfaceElevated)
                .border(
                    1.dp,
                    if (isError) InvestmentColors.ErrorRed else InvestmentColors.SuccessGreen,
                    RoundedCornerShape(10.dp),
                )
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                imageVector = if (isError) Icons.Default.Error else Icons.Default.CheckCircle,
                contentDescription = null,
                tint = if (isError) InvestmentColors.ErrorRed else InvestmentColors.SuccessGreen,
                modifier = Modifier.size(22.dp),
            )
            Spacer(Modifier.width(10.dp))
            Text(
                text = message,
                style = TextStyle(
                    color = InvestmentColors.TextPrimary,
                    fontSize = 14.sp,
                ),
                modifier = Modifier.weight(1f, fill = false),
            )
        }
    }
}

// ============================================================================
// 通用科技感卡片
// ============================================================================
@Composable
private fun TechCard(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    Box(
        modifier = modifier
            .shadow(
                elevation = 4.dp,
                shape = RoundedCornerShape(12.dp),
                ambientColor = InvestmentColors.Gold,
                spotColor = InvestmentColors.Gold,
            )
            .clip(RoundedCornerShape(12.dp))
            .background(
                Brush.linearGradient(
                    colors = listOf(
                        InvestmentColors.SurfaceDeep,
                        InvestmentColors.SurfaceElevated,
                    ),
                    start = Offset.Zero,
                    end = Offset.Infinite,
                )
            )
            .drawBehind {
                // 金色细边框
                val stroke = 0.8.dp.toPx()
                drawRoundRect(
                    brush = Brush.linearGradient(
                        colors = listOf(
                            InvestmentColors.Gold.copy(alpha = 0.6f),
                            InvestmentColors.Gold.copy(alpha = 0.1f),
                            InvestmentColors.Gold.copy(alpha = 0.6f),
                        )
                    ),
                    style = Stroke(width = stroke),
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(12.dp.toPx()),
                )
            },
    ) {
        content()
    }
}

// ============================================================================
// 实名认证弹窗
// ============================================================================
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun VerificationDialog(
    onDismiss: () -> Unit,
    onConfirm: (String, String) -> Unit,
) {
    var name by remember { mutableStateOf("") }
    var className by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = InvestmentColors.SurfaceElevated,
        titleContentColor = InvestmentColors.Gold,
        textContentColor = InvestmentColors.TextPrimary,
        title = {
            Text("实名认证", fontWeight = FontWeight.Bold)
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(
                    text = "该卡片尚未实名，请输入持卡人信息后继续操作",
                    color = InvestmentColors.TextSecondary,
                    fontSize = 13.sp,
                )
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("姓名（必填）") },
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = InvestmentColors.TextPrimary,
                        unfocusedTextColor = InvestmentColors.TextPrimary,
                        focusedBorderColor = InvestmentColors.Gold,
                        unfocusedBorderColor = InvestmentColors.BorderGold,
                        focusedLabelColor = InvestmentColors.Gold,
                        unfocusedLabelColor = InvestmentColors.TextDim,
                        cursorColor = InvestmentColors.Gold,
                    ),
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = className,
                    onValueChange = { className = it },
                    label = { Text("班级（必填）") },
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = InvestmentColors.TextPrimary,
                        unfocusedTextColor = InvestmentColors.TextPrimary,
                        focusedBorderColor = InvestmentColors.Gold,
                        unfocusedBorderColor = InvestmentColors.BorderGold,
                        focusedLabelColor = InvestmentColors.Gold,
                        unfocusedLabelColor = InvestmentColors.TextDim,
                        cursorColor = InvestmentColors.Gold,
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
                Text("确认", color = if (name.isNotBlank() && className.isNotBlank()) InvestmentColors.Gold else InvestmentColors.TextDim)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("取消", color = InvestmentColors.TextSecondary)
            }
        },
    )
}
