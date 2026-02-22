"""
工具函数模块
包含：异常值检测、OCR 修正、正态性检验、历史记录管理等
"""

import numpy as np
import pandas as pd
import json
import os
from datetime import datetime
from scipy import stats
from scipy.stats import shapiro, anderson, boxcox
import re


# ===============================
# 1. 异常值检测（3σ 原则）
# ===============================

def detect_outliers(data, threshold=3.0):
    """
    检测异常值（基于 3σ 原则）

    参数：
        data: 测量值列表
        threshold: 标准差倍数（默认 3）

    返回：
        dict: {
            "outliers_idx": 异常值索引列表,
            "outliers_val": 异常值列表,
            "upper_limit": 上限,
            "lower_limit": 下限,
            "message": 说明文字
        }
    """
    arr = np.array(data)
    mean = np.mean(arr)
    std = np.std(arr, ddof=1)

    upper_limit = mean + threshold * std
    lower_limit = mean - threshold * std

    outliers_mask = (arr > upper_limit) | (arr < lower_limit)
    outliers_idx = np.where(outliers_mask)[0].tolist()
    outliers_val = arr[outliers_idx].tolist()

    return {
        "outliers_idx": outliers_idx,
        "outliers_val": outliers_val,
        "upper_limit": upper_limit,
        "lower_limit": lower_limit,
        "mean": mean,
        "std": std,
        "count": len(outliers_val),
        "message": f"检测到 {len(outliers_val)} 个异常值（超出 ±{threshold}σ）" if outliers_val else "未检测到异常值"
    }


# ===============================
# 2. OCR 智能修正
# ===============================

def smart_correction(value, usl, lsl):
    """
    智能修正 OCR 误读

    规则：
    1. 如果值 > USL * 10，尝试除以 10（缺失小数点）
    2. 如果值包含非数字字符，剥离（单位噪声）
    3. 如果值包含形似字符，替换（O → 0, l → 1）

    参数：
        value: OCR 识别的原始值
        usl: 上规格限
        lsl: 下规格限

    返回：
        修正后的值
    """
    original = value

    # 规则 1：缺失小数点（如 102 → 10.2）
    if isinstance(value, (int, float)):
        # 如果值明显大于 USL，可能是缺失小数点
        if value > usl * 10:
            corrected = value / 10.0
            # 检查修正后是否在合理范围内
            if lsl <= corrected <= usl * 2:  # 允许一定的超出
                return corrected, "缺失小数点修正"

        # 尝试除以 100（如 102 → 1.02）
        if value > usl * 100:
            corrected = value / 100.0
            if lsl <= corrected <= usl * 2:
                return corrected, "缺失小数点修正（÷100）"

    # 规则 2：剥离单位（字符串转数值）
    if isinstance(value, str):
        # 提取数字部分（支持小数和负数）
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", value)
        if numbers:
            corrected = float(numbers[0])
            # 检查是否在合理范围内
            if lsl <= corrected <= usl * 2:
                return corrected, "单位剥离修正"

    # 规则 3：形似字符替换（O → 0, l → 1, I → 1）
    if isinstance(value, str):
        corrected_str = value.replace('O', '0').replace('o', '0')
        corrected_str = corrected_str.replace('l', '1').replace('I', '1')
        try:
            corrected = float(corrected_str)
            if lsl <= corrected <= usl * 2:
                return corrected, "形似字符替换"
        except ValueError:
            pass

    return original, None


def correct_measurements(measurements, usl, lsl):
    """
    批量修正测量数据

    参数：
        measurements: 测量值列表
        usl: 上规格限
        lsl: 下规格限

    返回：
        tuple: (修正后的数据列表, 修正历史列表)
    """
    corrected = []
    corrections = []

    for i, val in enumerate(measurements):
        corrected_val, rule = smart_correction(val, usl, lsl)
        corrected.append(corrected_val)

        if rule is not None and corrected_val != val:
            corrections.append({
                "index": i,
                "original": val,
                "corrected": corrected_val,
                "rule": rule
            })

    return corrected, corrections


# ===============================
# 3. 正态性检验
# ===============================

def normality_test(data, alpha=0.05):
    """
    正态性检验（Shapiro-Wilk + Anderson-Darling）

    参数：
        data: 测量值列表
        alpha: 显著性水平（默认 0.05）

    返回：
        dict: {
            "method": "Shapiro-Wilk" | "Anderson-Darling",
            "statistic": 统计量,
            "p_value": p 值,
            "is_normal": True | False,
            "message": 说明文字,
            "interpretation": 解读建议
        }
    """
    # Shapiro-Wilk 检验（样本量 3-5000）
    if 3 <= len(data) <= 5000:
        statistic, p_value = shapiro(data)
        is_normal = p_value > alpha

        method = "Shapiro-Wilk"
        message = (
            f"Shapiro-Wilk 检验：统计量={statistic:.4f}, p={p_value:.4f}"
        )

        interpretation = (
            "✅ 数据符合正态分布假设" if is_normal
            else "⚠️ 数据可能不符合正态分布（p < 0.05）"
        )

        return {
            "method": method,
            "statistic": statistic,
            "p_value": p_value,
            "is_normal": is_normal,
            "message": message,
            "interpretation": interpretation
        }

    # Anderson-Darling 检验（大样本或小样本）
    else:
        try:
            result = anderson(data)
            # 使用 5% 显著性水平的临界值
            critical_value = result.critical_values[2]  # 5%
            is_normal = result.statistic < critical_value

            method = "Anderson-Darling"
            message = (
                f"Anderson-Darling 检验："
                f"统计量={result.statistic:.4f}, "
                f"临界值(5%)={critical_value:.4f}"
            )

            interpretation = (
                "✅ 数据符合正态分布假设" if is_normal
                else "⚠️ 数据可能不符合正态分布"
            )

            return {
                "method": method,
                "statistic": result.statistic,
                "p_value": None,  # Anderson-Darling 不返回 p 值
                "is_normal": is_normal,
                "message": message,
                "interpretation": interpretation
            }
        except Exception as e:
            # 如果 Anderson-Darling 也失败，返回默认结果
            return {
                "method": "N/A",
                "statistic": None,
                "p_value": None,
                "is_normal": True,  # 假设正态
                "message": f"正态性检验失败：{str(e)}",
                "interpretation": "⚠️ 无法进行正态性检验，假设数据符合正态分布"
            }


def suggest_boxcox(data):
    """
    Box-Cox 变换（将非正态数据转换为正态）

    参数：
        data: 测量值列表

    返回：
        dict: {
            "transformed_data": 变换后的数据,
            "lambda_value": 最优 λ 值,
            "original_normality": 原始数据正态性检验结果,
            "transformed_normality": 变换后正态性检验结果,
            "improvement": 是否改善
        }
    """
    # Box-Cox 要求数据 > 0
    data_array = np.array(data)

    if np.min(data_array) <= 0:
        # 平移数据到正数
        shift = abs(np.min(data_array)) + 0.01
        data_shifted = data_array + shift
        shift_msg = f"数据已平移 {shift:.2f} 以满足 Box-Cox 要求"
    else:
        data_shifted = data_array
        shift_msg = "无需平移"

    try:
        # 执行 Box-Cox 变换
        transformed, lambda_value = boxcox(data_shifted)

        # 检验原始数据和变换后数据的正态性
        original_result = normality_test(data)
        transformed_result = normality_test(transformed.tolist())

        improvement = (
            not original_result["is_normal"] and transformed_result["is_normal"]
        )

        return {
            "transformed_data": transformed.tolist(),
            "lambda_value": lambda_value,
            "shift_msg": shift_msg,
            "original_normality": original_result,
            "transformed_normality": transformed_result,
            "improvement": improvement
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": f"Box-Cox 变换失败：{str(e)}"
        }


# ===============================
# 4. 历史记录管理
# ===============================

class HistoryManager:
    """历史记录管理器"""

    def __init__(self, history_dir="reports_history"):
        """
        初始化历史记录管理器

        参数：
            history_dir: 历史记录存储目录
        """
        self.history_dir = history_dir
        self.index_file = os.path.join(history_dir, "index.json")

        # 创建目录
        os.makedirs(history_dir, exist_ok=True)

        # 初始化索引
        self._init_index()

    def _init_index(self):
        """初始化索引文件"""
        if not os.path.exists(self.index_file):
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump({"records": []}, f, ensure_ascii=False, indent=2)

    def _load_index(self):
        """加载索引"""
        with open(self.index_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_index(self, index):
        """保存索引"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def save_report(self, batch_id, data, stats, metadata=None):
        """
        保存报告记录

        参数：
            batch_id: 批次号
            data: 原始测量数据
            stats: SPC 统计结果
            metadata: 元数据（如文件名、操作员等）

        返回：
            report_id: 报告唯一ID
        """
        # 生成唯一ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_id = f"{batch_id}_{timestamp}"

        # 创建记录
        record = {
            "report_id": report_id,
            "batch_id": batch_id,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "stats": stats,
            "metadata": metadata or {}
        }

        # 保存详细报告
        report_file = os.path.join(self.history_dir, f"{report_id}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        # 更新索引
        index = self._load_index()
        index["records"].append({
            "report_id": report_id,
            "batch_id": batch_id,
            "timestamp": record["timestamp"],
            "cpk": stats.get("cpk", 0),
            "cpk_status": stats.get("cpk_status", "UNKNOWN"),
            "count": len(data),
            "metadata": metadata or {}
        })
        self._save_index(index)

        return report_id

    def search(self, keyword=None, batch_id=None, date_from=None, date_to=None):
        """
        搜索历史记录

        参数：
            keyword: 关键词（批次号、零件名称等）
            batch_id: 批次号（精确匹配）
            date_from: 起始日期（YYYY-MM-DD）
            date_to: 结束日期（YYYY-MM-DD）

        返回：
            list: 匹配的记录列表
        """
        index = self._load_index()
        records = index["records"]

        # 过滤
        filtered = []

        for record in records:
            # 批次号精确匹配
            if batch_id and record["batch_id"] != batch_id:
                continue

            # 关键词搜索
            if keyword:
                keyword_lower = keyword.lower()
                if keyword_lower not in record["batch_id"].lower():
                    continue

            # 日期范围过滤
            if date_from or date_to:
                record_date = datetime.fromisoformat(record["timestamp"]).date()

                if date_from:
                    from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
                    if record_date < from_date:
                        continue

                if date_to:
                    to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
                    if record_date > to_date:
                        continue

            filtered.append(record)

        # 按时间倒序排序
        filtered.sort(key=lambda x: x["timestamp"], reverse=True)

        return filtered

    def get_report(self, report_id):
        """
        获取完整报告

        参数：
            report_id: 报告ID

        返回：
            dict: 完整报告数据
        """
        report_file = os.path.join(self.history_dir, f"{report_id}.json")

        if not os.path.exists(report_file):
            return None

        with open(report_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def delete_report(self, report_id):
        """
        删除报告

        参数：
            report_id: 报告ID

        返回：
            bool: 是否成功删除
        """
        # 删除详细报告文件
        report_file = os.path.join(self.history_dir, f"{report_id}.json")
        if os.path.exists(report_file):
            os.remove(report_file)

        # 更新索引
        index = self._load_index()
        index["records"] = [r for r in index["records"] if r["report_id"] != report_id]
        self._save_index(index)

        return True


# ===============================
# 5. Excel 导出
# ===============================

def export_to_excel(data, stats, header, filename="6SPC_Report.xlsx"):
    """
    导出数据到 Excel

    参数：
        data: 测量数据列表
        stats: SPC 统计结果
        header: 批次信息
        filename: 文件名

    返回：
        文件路径
    """
    import pandas as pd
    from datetime import datetime

    # 创建 Excel Writer
    filepath = filename

    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # Sheet 1: 批次信息
        header_data = {
            "项目": ["批次号", "零件名称", "上规格限 (USL)", "下规格限 (LSL)", "样本量", "均值", "标准差", "Cpk", "Ppk", "状态"],
            "值": [
                header.get("batch_id", ""),
                header.get("dimension_name", ""),
                header.get("usl", ""),
                header.get("lsl", ""),
                stats.get("count", ""),
                f"{stats.get('mean', 0):.4f}",
                f"{stats.get('std_overall', 0):.4f}",
                f"{stats.get('cpk', 0):.4f}",
                f"{stats.get('ppk', 0):.4f}",
                stats.get("cpk_status", "")
            ]
        }
        df_header = pd.DataFrame(header_data)
        df_header.to_excel(writer, sheet_name="批次信息", index=False)

        # Sheet 2: 原始数据
        df_data = pd.DataFrame({
            "序号": range(1, len(data) + 1),
            "测量值": data
        })
        df_data.to_excel(writer, sheet_name="原始数据", index=False)

        # Sheet 3: 子组数据
        if "subgroups" in stats:
            x_bar = stats["subgroups"]["x_bar"]
            r = stats["subgroups"]["r"]
            subgroups_df = pd.DataFrame({
                "子组号": range(1, len(x_bar) + 1),
                "子组均值 (X-bar)": x_bar,
                "子组极差 (R)": r
            })
            subgroups_df.to_excel(writer, sheet_name="子组数据", index=False)

        # Sheet 4: 统计摘要
        summary_data = {
            "指标": ["Cp", "Cpk", "Pp", "Ppk", "均值", "整体标准差", "子组内标准差", "最小值", "最大值", "样本量"],
            "值": [
                f"{stats.get('cp', 0):.4f}",
                f"{stats.get('cpk', 0):.4f}",
                f"{stats.get('pp', 0):.4f}",
                f"{stats.get('ppk', 0):.4f}",
                f"{stats.get('mean', 0):.4f}",
                f"{stats.get('std_overall', 0):.4f}",
                f"{stats.get('std_within', 0):.4f}",
                f"{stats.get('min', 0):.4f}",
                f"{stats.get('max', 0):.4f}",
                stats.get('count', 0)
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name="统计摘要", index=False)

    return filepath


# ===============================
# 6. 控制限计算
# ===============================

def calculate_control_limits(data, subgroup_size=5):
    """
    计算 X-bar 和 R 图的控制限

    参数：
        data: 测量数据列表
        subgroup_size: 子组大小（默认 5）

    返回：
        dict: {
            "x_bar": {
                "ucl": 上控制限,
                "lcl": 下控制限,
                "cl": 中心线
            },
            "r": {
                "ucl": 上控制限,
                "lcl": 下控制限,
                "cl": 中心线
            },
            "constants": {
                "A2": A2常数,
                "D3": D3常数,
                "D4": D4常数,
                "d2": d2常数
            }
        }
    """
    # 常数表（基于子组大小）
    constants_table = {
        2: {"A2": 1.880, "D3": 0, "D4": 3.267, "d2": 1.128},
        3: {"A2": 1.023, "D3": 0, "D4": 2.574, "d2": 1.693},
        4: {"A2": 0.729, "D3": 0, "D4": 2.282, "d2": 2.059},
        5: {"A2": 0.577, "D3": 0, "D4": 2.114, "d2": 2.326},
        6: {"A2": 0.483, "D3": 0, "D4": 2.004, "d2": 2.534},
        7: {"A2": 0.419, "D3": 0.076, "D4": 1.924, "d2": 2.704},
        8: {"A2": 0.373, "D3": 0.136, "D4": 1.864, "d2": 2.847},
        9: {"A2": 0.337, "D3": 0.184, "D4": 1.816, "d2": 2.970},
        10: {"A2": 0.308, "D3": 0.223, "D4": 1.777, "d2": 3.078}
    }

    # 获取常数
    if subgroup_size not in constants_table:
        subgroup_size = 5  # 默认使用 n=5

    constants = constants_table[subgroup_size]
    A2 = constants["A2"]
    D3 = constants["D3"]
    D4 = constants["D4"]

    # 计算子组统计量
    arr = np.array(data)
    subgroups = [arr[i:i + subgroup_size] for i in range(0, len(arr), subgroup_size)]
    subgroups = [sg for sg in subgroups if len(sg) > 0]

    x_bar_values = [np.mean(sg) for sg in subgroups]
    r_values = [np.max(sg) - np.min(sg) for sg in subgroups]

    # 计算中心线
    x_double_bar = np.mean(x_bar_values)
    r_bar = np.mean(r_values)

    # 计算 X-bar 图控制限
    x_bar_ucl = x_double_bar + A2 * r_bar
    x_bar_lcl = x_double_bar - A2 * r_bar
    x_bar_cl = x_double_bar

    # 计算 R 图控制限
    r_ucl = D4 * r_bar
    r_lcl = D3 * r_bar
    r_cl = r_bar

    return {
        "x_bar": {
            "ucl": x_bar_ucl,
            "lcl": x_bar_lcl,
            "cl": x_bar_cl,
            "values": x_bar_values
        },
        "r": {
            "ucl": r_ucl,
            "lcl": r_lcl,
            "cl": r_cl,
            "values": r_values
        },
        "constants": constants,
        "subgroup_size": subgroup_size
    }
