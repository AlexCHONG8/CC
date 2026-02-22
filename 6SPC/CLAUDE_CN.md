# CLAUDE_CN.md

本文档为 Claude Code (claude.ai/code) 提供在此代码库中工作的指导。

## 项目概述

**6SPC 分析报告工具**是一个医疗器械质量控制系统，将手写 QC 检验记录数字化为符合 **ISO 13485** 标准的统计过程控制（SPC）分析报告。该工具使用 AI 驱动的 OCR（MinerU）从扫描的检验记录中提取测量数据，并自动生成 Cp/Cpk/Pp/Ppk 指数和控制图表。

### 应用场景
- **原材料进货检验（IQC）**：塑料注射部件的尺寸验证
- **生产过程控制**：批量生产中的质量监控
- **供应商质量管理**：来料检验报告自动化生成

## 构建与设置命令

- **安装依赖**：`pip install -r requirements.txt`
- **环境配置**：`.env` 文件必须包含 `OCR_API_KEY`（MinerU Token）
- **虚拟环境**：需要 Python 3.9+（项目使用 `.venv`）

## 执行与测试

- **CLI 逻辑测试**（计算和 OCR 保护逻辑）：`python3 main.py`
- **交互式仪表板**（Streamlit UI）：`python3 -m streamlit run src/verify_ui.py`
- **示例测试文件**：`sample_scan.pdf` 用于测试 OCR API 流程

## 系统架构

### 核心数据流程

```
扫描上传 → OCR 提取 → 数据清洗 → SPC 计算 → 交互式验证 → HTML 报告
```

### 核心组件

#### 1. **OCRService** (`src/ocr_service.py`)
MinerU API v4 客户端封装，负责文档数字化。

**关键功能**：
- 包装 MinerU API v4 客户端进行 PDF/图像数字化
- API 密钥不可用时返回模拟数据（优雅降级）
- 将 Markdown 表格解析为结构化维度数据集
- 支持多维度检测（每个文档多个参数）
- 逻辑保护：处理缺失小数点、单位噪声、不完整提取

**MinerU API 工作流程**：
```
1. 请求上传 URL → 2. 上传文件（PUT） → 3. 创建提取任务 → 4. 轮询结果
```

#### 2. **SPCEngine** (`src/spc_engine.py`)
统计计算引擎，负责过程能力指数计算。

**关键功能**：
- 计算过程能力指数（Cp/Cpk：潜在能力）和性能指数（Pp/Ppk：整体性能）
- 子组分析用于 X-bar/R 图（默认 n=5，可配置）
- 使用 R-bar/d2 方法进行子组内标准差估计
- 合规标准：Cpk ≥ 1.33 = PASS，否则 FAIL

**统计方法说明**：
- **std_overall**：整体标准差（使用所有数据计算，反映长期性能）
- **std_within**：子组内标准差（使用 R-bar/d2 估计，反映潜在能力）
- **d2 因子**：n=5 时为 2.326，n=2 时为 1.128

#### 3. **Streamlit UI** (`src/verify_ui.py`)
人机交互验证仪表板。

**关键功能**：
- 支持多维度的可展开区域显示
- 实时可编辑数据表格，自动重新计算统计量
- 三图表可视化：单值读数图、X-bar 图、R-图
- 高端医疗级设计系统（青色/蓝绿色配色方案）
- HTML 预览模式（MVP 阶段暂不生成 PDF）

#### 4. **CLI Orchestrator** (`main.py`)
端到端演示，展示 OCR → SPC 流水线。

### 数据结构

#### 维度数据集（Dimension Set）
*由 OCR 返回，被 SPC 消费*
```python
{
    "header": {
        "batch_id": str,           # 批次标识符
        "dimension_name": str,     # 被测参数名称
        "usl": float,              # 上规格限
        "lsl": float               # 下规格限
    },
    "measurements": List[float]    # 原始测量值
}
```

#### SPC 计算结果（SPC Results）
*由 calculate_stats 返回*
```python
{
    "mean": float,
    "std_overall": float,         # 整体标准差
    "std_within": float,          # 子组内估计
    "cp": float, "cpk": float,    # 潜在能力指数
    "pp": float, "ppk": float,    # 整体性能指数
    "cpk_status": "PASS" | "FAIL",
    "subgroups": {
        "x_bar": List[float],      # 子组均值
        "r": List[float],          # 子组极差
        "size": int                # 子组大小（默认 5）
    }
}
```

## 6 SPC 图表完整说明

### 现有图表（已实现）

#### 1. 单值读数图（Individual Readings Plot）
**用途**：展示所有原始测量数据点，直观反映数据分布和趋势。

**关键元素**：
- 每个测量值的折线图
- USL/LSL 规格限虚线（红色）
- 数据点标记显示所有测量值

**统计意义**：快速识别异常值、数据漂移、测量系统问题。

#### 2. X-bar 图（均值控制图）
**用途**：监控子组均值的变化，检测过程中心的偏移。

**关键元素**：
- 子组均值折线（n=5，可配置）
- USL/LSL 规格限
- 总均值线（实线，绿色）
- 控制限（UCL/LCL，基于 ±3σ）

**统计意义**：
- 中心线表示过程平均性能
- 点超出控制限表明过程失控
- 连续点在同一侧提示系统性偏移

**控制限计算**：
```
UCL = X_double_bar + A2 * R_bar
LCL = X_double_bar - A2 * R_bar
```
其中 A2 为常数（n=5 时 A2=0.577）

#### 3. R-图（极差控制图）
**用途**：监控子组内变异，检测过程一致性的变化。

**关键元素**：
- 子组极差折线
- R-bar 中心线
- 控制限（UCL/LCL）

**统计意义**：
- 反映过程短期变异
- R 图失控表明过程稳定性恶化
- 必须与 X-bar 图联合分析

**控制限计算**：
```
UCL = D4 * R_bar
LCL = D3 * R_bar
```
其中 D3、D4 为常数（n=5 时 D3=0, D4=2.114）

### 待实现图表（MVP 后续功能）

#### 4. 直方图（Histogram）
**用途**：展示数据分布形状，验证正态分布假设。

**关键元素**：
- 频数分布柱状图
- 正态分布拟合曲线
- 规格限（USL/LSL）标记
- 均值线

**统计意义**：
- 识别分布形态：正态、偏态、双峰
- 评估过程中心与规格中心的偏移
- 计算超出规格限的百分比

**实现要点**：
- 使用 `numpy.histogram` 计算频数
- 使用 `scipy.stats.norm` 拟合正态曲线
- Streamlit 可用 `plotly.histogram` 或 `altair`

#### 5. 正态概率图（Normal Probability Plot）
**用途**：检验数据是否符合正态分布（Q-Q 图）。

**关键元素**：
- 观测值分位数 vs. 理论正态分位数散点图
- 参考直线（理论正态分布）
- 置信区间带

**统计意义**：
- 数据点沿直线分布 → 正态分布假设成立
- 系统性偏离 → 非正态分布，需考虑数据变换
- 尾部偏离 → 存在异常值或混合分布

**实现方法**：
```python
from scipy import stats
import matplotlib.pyplot as plt

stats.probplot(data, dist="norm", plot=plt)
```

**正态性检验**：可添加 Shapiro-Wilk 或 Anderson-Darling 检验的 p 值。

#### 6. 过程能力图（Capability Plot / Six-Pack）
**用途**：综合展示过程能力指数和规格限关系。

**关键元素**：
- 正态分布曲线（基于均值和标准差）
- USL/LSL 垂直标记线
- 目标值线（Target，如有）
- Cp、Cpk、Pp、Ppk 指数显示
- 超出规格的概率百分比

**统计意义**：
- 可视化过程分布与规格的关系
- 直观展示改进空间
- 支持哑铃图（Before/After）对比

**计算**：
```python
# 超出规格的概率
ppm_usl = (1 - norm.cdf(USL, mean, std)) * 1e6
ppm_lsl = norm.cdf(LSL, mean, std) * 1e6
total_ppm = ppm_usl + ppm_lsl
```

### 图表组合使用策略

**MVP 阶段**（当前）：
- 单值图 + X-bar 图 + R-图 → 基础 SPC 分析

**完整 6 SPC**（后续迭代）：
- 上述 3 个 + 直方图 + 正态概率图 + 能力图 → 完整统计分析

**显示建议**：
- 使用 Streamlit 的 `tabs` 或 `columns` 组织图表
- 提供"快速查看"模式（仅 3 个核心图）vs"完整分析"模式（6 个图）
- 支持图表导出为 PNG/SVG

## OCR 逻辑保护

系统处理常见的手写识别错误：

| 错误类型 | 示例 | 修正逻辑 |
|---------|------|---------|
| 缺失小数点 | `102` → `10.2` | 如果 USL=10.5，推断应为小数 |
| 单位噪声 | `10.1mm` → `10.1` | 剥离非数字字符 |
| OCR 误读 | `10O`（字母 O）→ `10.0` | 智能字符替换 |
| 不完整提取 | 50 点仅提取 10 点 | ⚠️ 完整性警报 |

**实现位置**：`src/ocr_service.py:_parse_markdown_to_json()`

## 项目标准

- **代码风格**：PEP 8 Python 代码规范
- **OCR 集成**：所有 OCR 操作必须使用 `src/ocr_service.py` 中的 `OCRService`
- **统计逻辑**：所有 SPC 数学计算（Cp、Cpk、Pp、Ppk）必须在 `src/spc_engine.py` 中的 `SPCEngine` 中
- **UI 框架**：所有验证界面和报告使用 Streamlit
- **错误处理**：API 不可用时优雅降级到模拟数据
- **测试数据**：真实 QC 扫描件位于 `Scan PDF/` 目录

## 环境变量

- `OCR_API_KEY`：MinerU API 令牌用于 OCR 处理

## 数据验证功能（MVP 阶段）

### 异常值自动检测（3σ 原则）
- 检测超出 ±3σ 的数据点
- 在 UI 中高亮显示可疑值
- 提供一键修正建议

### OCR 误读智能修正
- 根据规格限自动推断缺失小数点
- 检测并替换单位混淆（如 `mm`、`cm`）
- 字符相似度修正（`O` → `0`，`l` → `1`）

### 实时正态性检验
- 用户编辑数据时自动计算 Shapiro-Wilk p 值
- 正态性假设不成立时显示警告
- 建议数据变换（Box-Cox、对数变换）

## 性能考虑（MVP 优先）

- 当前优先级：功能正确性 > 性能优化
- 典型场景：50-200 个测量点的单批次分析
- 响应时间目标：< 5 秒（不含 OCR 处理时间）
- 后续优化：大规模并发处理、缓存机制

## 医疗器械合规要点（ISO 13485）

### 数据完整性
- 所有数据修改必须可追溯
- 电子签名支持（后续功能）
- 审计日志记录

### 文档控制
- 自动生成唯一报告编号
- 版本控制和变更历史
- 批次追溯性

### 统计有效性
- 遵循 ASTM E2281 标准进行过程能力计算
- 正态分布假设检验
- 最小样本量要求（建议 n ≥ 30）

## 测试数据

- **示例 QC 扫描件**：`Scan PDF/` 目录包含真实检验记录
- **测试文件**：`sample_scan.pdf`（项目根目录）用于 API 流程验证

## 开发工作流

1. **新增统计指标**：在 `SPCEngine` 中添加计算逻辑
2. **新增图表**：在 `verify_ui.py` 中添加 Plotly 图表
3. **修改 OCR 逻辑**：在 `OCRService._parse_markdown_to_json()` 中添加解析规则
4. **UI 改进**：遵循现有的设计系统（青色主题、圆角卡片）

## 常见问题

**Q: Cpk < 1.33 时系统如何处理？**
A: 系统标记为 "FAIL" 并高亮显示红色，但不阻止用户批准报告（由质量工程师判断）。

**Q: 如何处理非正态分布数据？**
A: MVP 阶段显示警告，后续迭代支持 Box-Cox 变换和非参数统计方法。

**Q: OCR 识别率如何？**
A: 取决于扫描质量。印刷表格识别率 >95%，手写数据约 70-90%，需要人工验证。
