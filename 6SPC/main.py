"""
6SPC Pro Max - CLI 演示工具
展示 v1.0 + v1.5 的所有功能
"""

import sys
from src.ocr_service import OCRService
from src.spc_engine import SPCEngine
from src.utils import (
    detect_outliers,
    correct_measurements,
    normality_test,
    calculate_control_limits
)

def main():
    print("=" * 60)
    print("🛡️ 6SPC Pro Max - 智能质量分析系统 | v1.5")
    print("=" * 60)
    print()

    # 1. 初始化服务
    print("📋 步骤 1: 初始化服务...")
    ocr = OCRService()
    print("✅ OCR 服务已初始化")
    print()

    # 2. 提取数据
    print("📂 步骤 2: 识别扫描件...")
    print("   使用示例文件: sample_scan.pdf")

    try:
        raw_data = ocr.extract_table_data("sample_scan.pdf")
        print(f"✅ 识别成功！提取到 {len(raw_data)} 个参数")
        print()

        # 3. 处理第一个参数
        data = raw_data[0]
        print(f"📊 参数名称: {data['header']['dimension_name']}")
        print(f"   批次号: {data['header']['batch_id']}")
        print(f"   USL: {data['header']['usl']}")
        print(f"   LSL: {data['header']['lsl']}")
        print()

        measurements = data["measurements"]
        print(f"📈 测量数据: {len(measurements)} 个数据点")
        print(f"   前 5 个值: {measurements[:5]}")
        print()

        # 4. 智能修正演示
        print("🔧 步骤 3: OCR 智能修正...")
        corrected, corrections = correct_measurements(
            measurements,
            data["header"]["usl"],
            data["header"]["lsl"]
        )

        if corrections:
            print(f"✅ 已修正 {len(corrections)} 处 OCR 误读:")
            for c in corrections[:3]:  # 只显示前 3 个
                print(f"   - 索引 {c['index']}: {c['original']} → {c['corrected']} ({c['rule']})")
            if len(corrections) > 3:
                print(f"   - ... 还有 {len(corrections) - 3} 处修正")
        else:
            print("ℹ️  未发现需要修正的数据")
        print()

        # 5. 异常值检测
        print("🔍 步骤 4: 异常值检测（3σ 原则）...")
        outlier_result = detect_outliers(corrected)

        if outlier_result["count"] > 0:
            print(f"⚠️  {outlier_result['message']}")
            print(f"   异常值索引: {outlier_result['outliers_idx']}")
            print(f"   异常值: {[f'{v:.4f}' for v in outlier_result['outliers_val']]}")
        else:
            print(f"✅ {outlier_result['message']}")
        print()

        # 6. SPC 计算
        print("📊 步骤 5: 计算 6SPC 统计量...")
        engine = SPCEngine(
            usl=data["header"]["usl"],
            lsl=data["header"]["lsl"]
        )
        stats = engine.calculate_stats(corrected)

        print(f"✅ 统计计算完成:")
        print(f"   均值: {stats['mean']:.4f}")
        print(f"   整体标准差: {stats['std_overall']:.4f}")
        print(f"   子组内标准差: {stats['std_within']:.4f}")
        print(f"   Cp: {stats['cp']:.4f}")
        print(f"   Cpk: {stats['cpk']:.4f}")
        print(f"   Pp: {stats['pp']:.4f}")
        print(f"   Ppk: {stats['ppk']:.4f}")
        print(f"   状态: {stats['cpk_status']} {'✅' if stats['cpk_status'] == 'PASS' else '❌'}")
        print()

        # 7. 正态性检验
        print("📐 步骤 6: 正态性检验...")
        normality_result = normality_test(corrected)
        print(f"   方法: {normality_result['method']}")
        print(f"   {normality_result['interpretation']}")
        print()

        # 8. 控制限计算
        print("📈 步骤 7: 计算控制限...")
        control_limits = calculate_control_limits(corrected)

        print(f"   X-bar 图控制限:")
        print(f"     UCL: {control_limits['x_bar']['ucl']:.4f}")
        print(f"     CL:  {control_limits['x_bar']['cl']:.4f}")
        print(f"     LCL: {control_limits['x_bar']['lcl']:.4f}")
        print(f"   R 图控制限:")
        print(f"     UCL: {control_limits['r']['ucl']:.4f}")
        print(f"     CL:  {control_limits['r']['cl']:.4f}")
        if control_limits['r']['lcl'] > 0:
            print(f"     LCL: {control_limits['r']['lcl']:.4f}")
        print()

        # 9. 总结
        print("=" * 60)
        print("📋 分析报告摘要")
        print("=" * 60)
        print(f"批次: {data['header']['batch_id']}")
        print(f"参数: {data['header']['dimension_name']}")
        print(f"样本量: {len(corrected)}")
        print(f"Cpk: {stats['cpk']:.4f} ({stats['cpk_status']})")
        print(f"正态性: {'符合' if normality_result['is_normal'] else '不符合'}")
        print()
        print("✅ 分析完成！")
        print()
        print("💡 下一步操作:")
        print("   1. 启动 Streamlit Dashboard 查看完整 6 SPC 图表")
        print("   2. 运行命令: python3 -m streamlit run src/verify_ui.py")
        print()

    except FileNotFoundError:
        print("❌ 错误: 找不到 sample_scan.pdf")
        print("   请确保示例文件存在于项目根目录")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
