#!/usr/bin/env python3
"""
Manual data entry for 20260122_111541.pdf
Use this when OCR fails to extract data correctly.
"""

from src.ocr_service import OCRService

# Based on the scanned image data
manual_specs = [
    {
        'location': '1',
        'usl': 27.9,
        'lsl': 27.8,
        'name': '位置1',
        'measurements': [
            27.85, 27.84, 27.81, 27.82, 27.85,
            27.84, 27.82, 27.85, 27.81, 27.84
        ]
    },
    {
        'location': '11',
        'usl': 6.1,
        'lsl': 5.9,
        'name': 'Φ位置11',
        'measurements': [
            6.02, 6.02, 6.01, 6.01, 6.06,
            6.02, 6.04, 6.02, 6.03, 6.03
        ]
    },
    {
        'location': '13',
        'usl': 73.2,
        'lsl': 73.05,
        'name': '位置13',
        'measurements': [
            73.14, 73.12, 73.15, 73.12, 73.10,
            73.15, 73.19, 73.19, 73.15, 73.13
        ]
    }
]

# Create the data structure
ocr = OCRService()
correct_data = ocr.create_manual_entry(manual_specs)

# Print the data structure
print("=" * 80)
print("✅ 正确的数据结构已生成")
print("=" * 80)

for i, dim in enumerate(correct_data, 1):
    header = dim['header']
    measurements = dim['measurements']

    print(f"\n参数 {i}: {header['dimension_name']}")
    print(f"  批次ID: {header['batch_id']}")
    print(f"  USL: {header['usl']}, LSL: {header['lsl']}")
    print(f"  测量数据 ({len(measurements)} 个):")
    print(f"    {measurements}")
    print(f"  均值: {sum(measurements)/len(measurements):.4f}")

# Now calculate SPC stats
from src.spc_engine import SPCEngine

print("\n" + "=" * 80)
print("📊 6SPC 统计分析结果")
print("=" * 80)

for i, dim in enumerate(correct_data, 1):
    header = dim['header']
    measurements = dim['measurements']

    engine = SPCEngine(usl=header['usl'], lsl=header['lsl'])
    stats = engine.calculate_stats(measurements)

    print(f"\n参数 {i}: {header['dimension_name']}")
    print(f"  均值: {stats['mean']:.4f}")
    print(f"  标准差(overall): {stats['std_overall']:.4f}")
    print(f"  标准差(within): {stats['std_within']:.4f}")
    print(f"  Cp: {stats['cp']:.3f}, Cpk: {stats['cpk']:.3f} [{stats['cpk_status']}]")
    print(f"  Pp: {stats['pp']:.3f}, Ppk: {stats['ppk']:.3f}")
    print(f"  最小值: {stats['min']:.2f}, 最大值: {stats['max']:.2f}")

print("\n" + "=" * 80)
print("💡 现在可以在Streamlit应用中使用这个数据")
print("=" * 80)
