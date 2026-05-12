import { useState, useRef, useCallback, useEffect } from 'react'

interface TermsModalProps {
  visible: boolean
  onClose: () => void
  onConfirm: () => void
}

const TermsModal = ({ visible, onClose, onConfirm }: TermsModalProps) => {
  const [hasScrolledToBottom, setHasScrolledToBottom] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  // 重置滚动状态
  useEffect(() => {
    if (visible) {
      setHasScrolledToBottom(false)
      if (scrollRef.current) {
        scrollRef.current.scrollTop = 0
      }
    }
  }, [visible])

  // 监听滚动事件
  const handleScroll = useCallback(() => {
    const el = scrollRef.current
    if (!el) return
    const threshold = 60 // 距底部60px即视为已读完
    const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < threshold
    if (isAtBottom) {
      setHasScrolledToBottom(true)
    }
  }, [])

  if (!visible) return null

  return (
    <div className="terms-modal-overlay" onClick={onClose}>
      <div className="terms-modal-card" onClick={(e) => e.stopPropagation()}>
        {/* 标题 */}
        <div className="terms-modal-header">
          <h2 className="terms-modal-title">商家服务协议</h2>
          <button className="terms-modal-close" onClick={onClose}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>

        {/* 滚动内容区 */}
        <div
          className="terms-modal-content"
          ref={scrollRef}
          onScroll={handleScroll}
        >
          <div className="terms-content-inner">
            <h3>宇华校园沙盒市场商家服务条款</h3>
            <p className="terms-update-date">最后更新日期：2026年5月1日</p>

            <h4>第一章 总则</h4>
            <p>
              欢迎您加入宇华校园沙盒经济平台（以下简称"本平台"）。本平台是由宇华教育集团主办的校园财商教育实践项目，旨在通过模拟市场经济环境，培养学生的商业思维、财务管理能力和团队协作精神。
            </p>
            <p>
              本协议适用于所有在本平台注册为商家（摊位经营者）的用户。在您完成注册流程前，请务必仔细阅读本协议全部条款。一旦您点击"同意"或完成注册，即视为您已充分理解并接受本协议的全部内容。
            </p>

            <h4>第二章 平台货币与经济体系</h4>
            <p>
              2.1 本平台使用虚拟货币"沙盒币"（Sandbox Coin，简称SC）作为唯一流通货币。沙盒币不具有任何法定货币价值，不可兑换为人民币或其他法定货币。
            </p>
            <p>
              2.2 沙盒币的初始发放由平台央行统一管理。每位参与者在活动开始时将获得等额初始资金，具体金额由当期活动规则确定。
            </p>
            <p>
              2.3 <strong>零提现声明</strong>：本平台所有虚拟资产（包括但不限于沙盒币余额、股票持仓、信用额度）均不支持任何形式的提现、转出或兑换为实物/现金。平台结束后所有虚拟资产将清零。
            </p>
            <p>
              2.4 平台保留根据宏观经济调控需要，调整货币供应量、利率、税率等经济参数的权利。此类调整将提前通过平台公告通知。
            </p>

            <h4>第三章 商家注册与经营资质</h4>
            <p>
              3.1 商家注册需提供真实的班级信息和商铺名称。禁止使用虚假信息注册。
            </p>
            <p>
              3.2 每个班级最多可注册3个商铺。商铺名称不得包含违法、低俗或侵犯他人权益的内容。
            </p>
            <p>
              3.3 商家经营类目需在注册时明确声明，包括但不限于：食品饮料、手工艺品、文创产品、服务类（如美甲、似颜绘）、娱乐类（如桌游租赁）等。
            </p>
            <p>
              3.4 食品类商家需额外提交食品安全承诺书，并确保所售食品符合校园食品安全管理规定。
            </p>

            <h4>第四章 经营规范</h4>
            <p>
              4.1 商家必须明码标价。所有商品/服务的价格必须在摊位显著位置公示，且与系统录入价格一致。
            </p>
            <p>
              4.2 禁止哄抬物价。单个商品定价不得超过成本价的300%（特殊手工艺品除外，需提交成本凭证审核）。
            </p>
            <p>
              4.3 禁止虚假交易。包括但不限于：自买自卖刷单、与其他商家串通制造虚假流水、利用系统漏洞进行非正常交易。
            </p>
            <p>
              4.4 商家应保持经营场所整洁，活动结束后需自行清理摊位区域。未按要求清理的，将扣除信用积分。
            </p>
            <p>
              4.5 所有交易必须通过NFC刷卡系统完成。禁止线下私自收取沙盒币或进行任何绕过系统的交易行为。
            </p>

            <h4>第五章 信用积分制度</h4>
            <p>
              5.1 每位商家初始信用积分为100分。信用积分将影响商家在平台的经营权限和贷款额度。
            </p>
            <p>
              5.2 加分项：按时提交成本凭证（+5分/次）、获得消费者好评（+2分/次）、参与平台公益活动（+10分/次）、连续经营无违规（+3分/天）。
            </p>
            <p>
              5.3 扣分项：未明码标价（-10分/次）、虚假交易（-30分/次）、哄抬物价（-20分/次）、未按时清理摊位（-5分/次）、消费者有效投诉（-15分/次）。
            </p>
            <p>
              5.4 信用积分低于60分的商家将被暂停经营资格24小时；低于30分将被永久取消本期活动经营资格。
            </p>
            <p>
              5.5 信用积分将作为平台央行发放贷款的重要参考指标。高信用商家可享受更低利率和更高额度。
            </p>

            <h4>第六章 风控责任与合规要求</h4>
            <p>
              6.1 商家有义务配合平台的风控审计。平台有权随时要求商家提供经营数据、成本凭证和交易明细。
            </p>
            <p>
              6.2 商家需在每个经营日结束后24小时内提交当日成本凭证（Cost Evidence），包括原材料采购凭证、人工成本说明等。
            </p>
            <p>
              6.3 平台设有自动风控系统，对异常交易模式（如短时间内大量同金额交易、非营业时间交易等）进行监控。触发风控预警的交易将被暂时冻结，待人工审核后处理。
            </p>
            <p>
              6.4 商家不得利用系统漏洞或技术手段获取不正当利益。发现漏洞应及时向平台管理员报告。
            </p>
            <p>
              6.5 商家之间的资金往来（如进货、合作分成）需通过平台的"商户间转账"功能完成，并注明交易用途。
            </p>

            <h4>第七章 投资与金融服务</h4>
            <p>
              7.1 商家可使用经营所得参与平台股票市场投资。投资行为需遵守平台证券交易规则。
            </p>
            <p>
              7.2 商家可向平台央行申请经营贷款。贷款审批将综合考虑信用积分、经营流水、还款能力等因素。
            </p>
            <p>
              7.3 贷款逾期将产生罚息并扣除信用积分。连续逾期超过3天的，平台有权冻结商家账户直至还清欠款。
            </p>
            <p>
              7.4 禁止利用贷款资金进行高风险投机行为。平台有权对贷款资金用途进行追踪审计。
            </p>

            <h4>第八章 退款与售后</h4>
            <p>
              8.1 消费者有权在交易完成后30分钟内申请退款。商家应积极配合合理的退款请求。
            </p>
            <p>
              8.2 退款申请需经平台管理员审核。审核通过后，资金将原路退回消费者账户。
            </p>
            <p>
              8.3 商家无正当理由拒绝退款的，将扣除信用积分并可能面临经营限制。
            </p>
            <p>
              8.4 对于已消耗的服务类商品（如已食用的食品），原则上不支持退款，但商家应对质量问题负责。
            </p>

            <h4>第九章 数据与隐私</h4>
            <p>
              9.1 平台将收集商家的经营数据用于教学分析和平台运营优化。数据仅在校园教育场景内使用。
            </p>
            <p>
              9.2 商家的个人信息（姓名、班级）仅用于平台内部管理，不会向第三方披露。
            </p>
            <p>
              9.3 平台活动结束后，所有交易数据将保留用于教学案例分析，但会进行匿名化处理。
            </p>
            <p>
              9.4 商家有权要求查看自己的完整交易记录和信用积分变动明细。
            </p>

            <h4>第十章 违规处理</h4>
            <p>
              10.1 轻微违规（首次）：口头警告 + 扣除信用积分5-10分。
            </p>
            <p>
              10.2 一般违规：书面警告 + 扣除信用积分15-30分 + 暂停经营24小时。
            </p>
            <p>
              10.3 严重违规：取消本期活动经营资格 + 通报班主任。
            </p>
            <p>
              10.4 特别严重违规（如利用技术手段作弊、组织大规模虚假交易）：永久取消平台参与资格 + 通报学校教务处。
            </p>

            <h4>第十一章 免责声明</h4>
            <p>
              11.1 本平台为教育实践项目，不构成任何真实商业活动。平台不对商家的"经营亏损"承担任何责任。
            </p>
            <p>
              11.2 因不可抗力（如网络故障、系统维护）导致的交易中断或数据丢失，平台将尽力恢复但不承担赔偿责任。
            </p>
            <p>
              11.3 平台保留在活动期间修改规则的权利。规则修改将提前公告，已完成的交易不受影响。
            </p>

            <h4>第十二章 附则</h4>
            <p>
              12.1 本协议自商家完成注册之日起生效，至当期活动结束之日终止。
            </p>
            <p>
              12.2 本协议的最终解释权归宇华校园沙盒经济平台管理委员会所有。
            </p>
            <p>
              12.3 如有任何疑问，请联系平台管理员或指导教师。
            </p>

            <div className="terms-footer-note">
              ── 宇华校园沙盒经济平台管理委员会 ──
            </div>
          </div>
        </div>

        {/* 底部确认按钮 */}
        <div className="terms-modal-footer">
          {!hasScrolledToBottom && (
            <p className="terms-scroll-hint">↓ 请滚动阅读完整条款后确认</p>
          )}
          <button
            className={`terms-confirm-btn ${hasScrolledToBottom ? 'active' : 'disabled'}`}
            disabled={!hasScrolledToBottom}
            onClick={onConfirm}
          >
            确认阅读
          </button>
        </div>
      </div>
    </div>
  )
}

export default TermsModal
