"""
AI-Powered Analysis Engine for Plastic Injection Hot Runner Process Control
Provides intelligent comments and improvement suggestions based on SPC data.
"""

from typing import Dict, List
from datetime import datetime


class PlasticInjectionAnalyzer:
    """Analyze SPC data for plastic injection hot runner systems"""

    def __init__(self):
        # Plastic injection specific thresholds
        self.CPK_EXCELLENT = 1.67  # 6-sigma level
        self.CPK_CAPABLE = 1.33   # 4-sigma level
        self.CPK_ACCEPTABLE = 1.00  # 3-sigma level
        self.PPM_EXCELLENT = 100
        self.PPM_GOOD = 1000
        self.PPM_ACCEPTABLE = 10000

    def analyze_dimension(self, dim_data: Dict, stats: Dict) -> Dict:
        """
        Generate comprehensive analysis for one dimension.

        Returns:
            {
                'status': 'EXCELLENT' | 'GOOD' | 'ACCEPTABLE' | 'NEEDS_IMPROVEMENT' | 'CRITICAL',
                'status_emoji': str,
                'overall_assessment': str,
                'capability_analysis': str,
                'stability_analysis': str,
                'improvement_actions': List[str],
                'hot_runner_tips': List[str],
                'risk_level': 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
            }
        """
        cp = stats['cp']
        cpk = stats['cpk']
        pp = stats['pp']
        ppk = stats['ppk']
        mean = stats['mean']
        std_overall = stats['std_overall']
        std_within = stats['std_within']

        usl = dim_data['header']['usl']
        lsl = dim_data['header']['lsl']
        target = (usl + lsl) / 2 if usl and lsl else None

        # Calculate PPM
        measurements = dim_data['measurements']
        ppm_above = ((m > usl for m in measurements) if usl else 0)
        ppm_above = sum(ppm_above) / len(measurements) * 1e6 if usl else 0
        ppm_below = ((m < lsl for m in measurements) if lsl else 0)
        ppm_below = sum(ppm_below) / len(measurements) * 1e6 if lsl else 0
        ppm_total = ppm_above + ppm_below

        # Determine status
        status, emoji, risk = self._determine_status(cpk, ppm_total)

        # Generate analysis
        analysis = {
            'status': status,
            'status_emoji': emoji,
            'risk_level': risk,
            'overall_assessment': self._generate_overall_assessment(
                cp, cpk, pp, ppk, ppm_total, status
            ),
            'capability_analysis': self._analyze_capability(
                cp, cpk, pp, ppk, target, mean, usl, lsl
            ),
            'stability_analysis': self._analyze_stability(
                std_within, std_overall, measurements
            ),
            'improvement_actions': self._generate_improvement_actions(
                cpk, ppk, mean, target, std_overall, usl, lsl
            ),
            'hot_runner_tips': self._generate_hot_runner_tips(
                dim_data['header']['dimension_name'], cpk, std_overall
            )
        }

        return analysis

    def _determine_status(self, cpk: float, ppm: float) -> tuple:
        """Determine overall process status"""
        if cpk >= self.CPK_EXCELLENT and ppm <= self.PPM_EXCELLENT:
            return "EXCELLENT", "🏆", "LOW"
        elif cpk >= self.CPK_CAPABLE and ppm <= self.PPM_GOOD:
            return "GOOD", "✅", "LOW"
        elif cpk >= self.CPK_ACCEPTABLE and ppm <= self.PPM_ACCEPTABLE:
            return "ACCEPTABLE", "⚠️", "MEDIUM"
        elif cpk < 1.0 or ppm > 50000:
            return "CRITICAL", "🚨", "CRITICAL"
        else:
            return "NEEDS_IMPROVEMENT", "🔧", "HIGH"

    def _generate_overall_assessment(self, cp: float, cpk: float, pp: float,
                                     ppk: float, ppm: float, status: str) -> str:
        """Generate overall assessment text"""
        if status == "EXCELLENT":
            return (
                f"**优秀工艺表现** - 工艺能力卓越 (Cpk={cpk:.2f})，"
                f"缺陷率极低 (PPM={ppm:.0f})。热流道系统运行稳定，"
                f"建议保持当前参数设置并持续监控。"
            )
        elif status == "GOOD":
            return (
                f"**良好工艺表现** - 工艺能力充足 (Cpk={cpk:.2f})，"
                f"质量控制良好 (PPM={ppm:.0f})。热流道温度控制稳定，"
                f"建议定期监控关键参数。"
            )
        elif status == "ACCEPTABLE":
            return (
                f"**可接受工艺表现** - 工艺能力基本满足 (Cpk={cpk:.2f})，"
                f"但有改进空间。缺陷率 (PPM={ppm:.0f}) 需关注，"
                f"建议优化热流道参数。"
            )
        elif status == "CRITICAL":
            return (
                f"**工艺能力严重不足** - Cpk={cpk:.2f} < 1.0，"
                f"工艺不受控。高缺陷率 (PPM={ppm:.0f}) 需立即采取纠正措施，"
                f"检查热流道系统状态。"
            )
        else:
            return (
                f"**需要改善** - 当前工艺能力不足 (Cpk={cpk:.2f})，"
                f"PPM={ppm:.0f}。建议分析变异源并优化工艺参数。"
            )

    def _analyze_capability(self, cp: float, cpk: float, pp: float, ppk: float,
                           target: float, mean: float, usl: float, lsl: float) -> str:
        """Analyze process capability indices"""
        analysis = []

        # Cp vs Cpk comparison (centering)
        if cp > cpk + 0.3:
            shift_percent = ((cp - cpk) / cp * 100)
            analysis.append(
                f"⚠️ **工艺未对中**: Cp({cp:.2f}) > Cpk({cpk:.2f})，"
                f"均值偏离目标约 {shift_percent:.1f}%。"
                f"建议调整工艺均值至目标值 ({target:.3f})。"
            )
        elif abs(cpk - cp) < 0.1:
            analysis.append(
                f"✅ **工艺对中良好**: Cp({cp:.2f}) ≈ Cpk({cpk:.2f})，"
                f"均值居中，热流道温度均匀性良好。"
            )

        # Potential vs Overall performance
        if pp < cp - 0.2:
            analysis.append(
                f"⚠️ **存在特殊原因变异**: Pp({pp:.2f}) < Cp({cp:.2f})，"
                f"可能有异常干扰因素。建议检查批次间一致性。"
            )

        # Process centering
        if target:
            deviation = abs(mean - target) / (usl - lsl) * 100
            if deviation > 15:
                analysis.append(
                    f"🔴 **严重偏移**: 均值 ({mean:.4f}) 偏离目标 {deviation:.1f}%，"
                    f"需立即调整热流道温度或注射压力。"
                )
            elif deviation > 8:
                analysis.append(
                    f"⚠️ **中度偏移**: 均值 ({mean:.4f}) 偏离目标 {deviation:.1f}%，"
                    f"建议微调工艺参数。"
                )

        return "\n\n".join(analysis) if analysis else "✅ 工艺能力分析正常，无明显问题。"

    def _analyze_stability(self, std_within: float, std_overall: float,
                          measurements: List[float]) -> str:
        """Analyze process stability"""
        analysis = []

        # Compare within vs overall variation
        if std_overall > std_within * 1.5:
            analysis.append(
                f"⚠️ **工艺不稳定**: 整体标准差 ({std_overall:.4f}) "
                f"显著大于组内标准差 ({std_within:.4f})，"
                f"存在批次间变异或漂移。建议检查：\n"
                f"  • 热流道温度稳定性\n"
                f"  • 原材料批次一致性\n"
                f"  • 冷却时间一致性"
            )

        # Detect drift using first vs last half
        n = len(measurements)
        first_half_mean = sum(measurements[:n//2]) / (n//2)
        second_half_mean = sum(measurements[n//2:]) / (n - n//2)
        drift = abs(second_half_mean - first_half_mean)

        if drift > std_overall * 0.5:
            direction = "上升" if second_half_mean > first_half_mean else "下降"
            analysis.append(
                f"📈 **检测到趋势**: 数据呈现{direction}趋势 "
                f"(漂移量={drift:.4f})，可能是热流道温度漂移或模具磨损。"
            )

        return "\n\n".join(analysis) if analysis else "✅ 工艺稳定性良好，变异主要来自随机因素。"

    def _generate_improvement_actions(self, cpk: float, ppk: float, mean: float,
                                     target: float, std: float, usl: float, lsl: float) -> List[str]:
        """Generate actionable improvement suggestions"""
        actions = []

        # Low Cpk actions
        if cpk < 1.33:
            if std > (usl - lsl) / 6:
                actions.append(
                    "🔧 **降低变异**: 减小标准差可显著提升Cpk\n"
                    "  • 优化热流道温度控制 (±1°C)\n"
                    "  • 检查加热圈和热电偶\n"
                    "  • 稳定注射压力和速度\n"
                    "  • 确保冷却系统一致性"
                )

            if target and abs(mean - target) > (usl - lsl) * 0.1:
                actions.append(
                    "🎯 **调整工艺中心**: 将均值调向目标值\n"
                    "  • 调整热流道温度设定值\n"
                    "  • 微调注射行程或保压压力\n"
                    "  • 检查浇口尺寸是否均匀"
                )

        # Ppk vs Cpk gap
        if ppk < cpk - 0.3:
            actions.append(
                "📊 **减少批次间变异**: 提升长期稳定性\n"
                "  • 标准化操作流程\n"
                "  • 定期维护热流道系统\n"
                "  • 使用同一批次原材料\n"
                "  • 记录并监控关键参数"
            )

        # General optimization
        if cpk >= 1.33 and cpk < 1.67:
            actions.append(
                "⬆️ **向6-sigma迈进**: 从良好到卓越\n"
                "  • 实施统计过程控制(SPC)\n"
                "  • 采用DOE优化参数\n"
                "  • 考虑升级热流道系统\n"
                "  • 培训操作人员"
            )

        return actions if actions else ["✅ 保持当前工艺参数，继续监控"]

    def _generate_hot_runner_tips(self, dimension_name: str, cpk: float, std: float) -> List[str]:
        """Generate hot runner system specific tips"""
        tips = []

        # Hot runner temperature control
        if cpk < 1.33:
            tips.extend([
                "🌡️ **热流道温度优化**:\n"
                "  • 检查各温区温度是否在设定值±2°C内\n"
                "  • 热电偶是否准确安装和校准\n"
                "  • 加热圈是否老化不均匀\n"
                "  • 考虑增加PID参数优化",
                "🔗 **热流道系统检查**:\n"
                "  • 浇口是否有堵塞或磨损\n"
                "  • 阀针 timing 是否一致\n"
                "  • 热膨胀是否考虑\n"
                "  • 是否需要热流道清洗"
            ])

        # Dimension-specific tips
        if any(keyword in dimension_name for keyword in ['尺寸', '外径', '内径', '孔径']):
            tips.append(
                "📐 **尺寸控制要点**:\n"
                "  • 关注冷却时间一致性\n"
                "  • 检查顶出是否导致变形\n"
                "  • 监控模具温度分布\n"
                "  • 考虑模温机精度"
            )

        # High standard deviation tips
        if std > 0:
            tips.append(
                "🎛️ **工艺参数优化**:\n"
                "  • 降低注射速度以减少剪切热\n"
                "  • 优化保压切换点\n"
                "  • 检查原料塑化均匀性\n"
                "  • 螺杆转速是否稳定"
            )

        return tips

    def generate_executive_summary(self, analyses: List[Dict]) -> Dict:
        """Generate executive summary across all dimensions"""
        total = len(analyses)
        excellent = sum(1 for a in analyses if a['status'] == 'EXCELLENT')
        good = sum(1 for a in analyses if a['status'] == 'GOOD')
        acceptable = sum(1 for a in analyses if a['status'] == 'ACCEPTABLE')
        needs_work = sum(1 for a in analyses if a['status'] in ['NEEDS_IMPROVEMENT', 'CRITICAL'])

        critical_dims = [i for i, a in enumerate(analyses, 1) if a['risk_level'] == 'CRITICAL']
        high_risk_dims = [i for i, a in enumerate(analyses, 1) if a['risk_level'] == 'HIGH']

        return {
            'total_dimensions': total,
            'pass_rate': ((excellent + good) / total * 100) if total > 0 else 0,
            'status_distribution': {
                'excellent': excellent,
                'good': good,
                'acceptable': acceptable,
                'needs_work': needs_work
            },
            'critical_dimensions': critical_dims,
            'high_risk_dimensions': high_risk_dims,
            'overall_recommendation': self._get_overall_recommendation(
                excellent, good, acceptable, needs_work, total
            )
        }

    def _get_overall_recommendation(self, excellent: int, good: int,
                                   acceptable: int, needs_work: int, total: int) -> str:
        """Generate overall process recommendation"""
        pass_rate = ((excellent + good) / total * 100) if total > 0 else 0

        if pass_rate >= 90:
            return (
                "✅ **整体工艺状态优秀** - 热流道系统运行稳定，"
                "建议保持当前参数设置并实施预防性维护。"
            )
        elif pass_rate >= 70:
            return (
                "⚠️ **整体工艺状态良好** - 大部分尺寸受控，"
                f"建议重点改善 {needs_work} 个问题尺寸以达到更高水平。"
            )
        elif pass_rate >= 50:
            return (
                "🔧 **工艺需要优化** - 约一半尺寸不受控，"
                "建议全面审查热流道系统并优化工艺参数。"
            )
        else:
            return (
                "🚨 **工艺状态严重** - 多数尺寸不受控，"
                "建议立即停机检查热流道系统、温度控制器和工艺设置。"
            )
