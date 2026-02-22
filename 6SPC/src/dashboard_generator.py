"""
Professional HTML Dashboard Generator for 6SPC Pro Max
Generates ISO 13485 compliant tabbed interface with all analysis
"""

import os
import time
from datetime import datetime
from typing import List, Dict, Any
import plotly.graph_objects as go
import plotly.subplots as sp
import numpy as np
from scipy import stats

# Import analysis engine
try:
    from src.analysis_engine import PlasticInjectionAnalyzer
except ImportError:
    from analysis_engine import PlasticInjectionAnalyzer


def _create_individual_plot(measurements: List[float], usl: float, lsl: float) -> str:
    """Create individual values plot - Professional styling with enhanced visibility"""
    fig = go.Figure()

    # Add measurements with enhanced styling and better visibility
    fig.add_trace(go.Scatter(
        y=measurements,
        mode='lines+markers',
        name='测量值 Measured Values',
        line=dict(color='#0891B2', width=2.5),
        marker=dict(
            size=8,
            color='#0891B2',
            line=dict(width=1.5, color='white'),
            symbol='circle',
            opacity=0.85
        ),
        hovertemplate='<b>Sample %{x}</b><br>Value: %{y:.4f}<extra></extra>'
    ))

    # Add specification limits with enhanced styling
    fig.add_hline(
        y=usl,
        line_dash="dash",
        line_color="#DC2626",
        line_width=3,
        annotation_text=f"<b>USL</b>: {usl}",
        annotation_font_size=12,
        annotation_font_color="#DC2626",
        annotation_font_weight="bold"
    )
    fig.add_hline(
        y=lsl,
        line_dash="dash",
        line_color="#DC2626",
        line_width=3,
        annotation_text=f"<b>LSL</b>: {lsl}",
        annotation_font_size=12,
        annotation_font_color="#DC2626",
        annotation_font_weight="bold"
    )

    # Add target line (nominal)
    target = (usl + lsl) / 2
    fig.add_hline(
        y=target,
        line_dash="dot",
        line_color="#22C55E",
        line_width=2,
        annotation_text=f"<b>Target</b>: {target:.4f}",
        annotation_font_size=11,
        annotation_font_color="#22C55E",
        annotation_opacity=0.7
    )

    fig.update_layout(
        title=dict(
            text="1. Individual Values Plot (单值图)",
            font=dict(size=16, color='#1F2937', family='Arial, sans-serif', weight='bold')
        ),
        yaxis=dict(
            title=dict(text="测量值 Measured Value", font=dict(size=13, weight='bold')),
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1,
            zeroline=True,
            zerolinecolor='gray',
            zerolinewidth=1.5
        ),
        xaxis=dict(
            title=dict(text="序号 Sequence", font=dict(size=13, weight='bold')),
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1
        ),
        hovermode='x unified',
        height=450,
        plot_bgcolor='rgba(255, 255, 255, 0.98)',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif', color='#374151', size=11),
        margin=dict(l=60, r=30, t=50, b=60),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11)
        )
    )

    return fig.to_html(full_html=False, include_plotlyjs='cdn')


def _create_xbar_chart(subgroups: Dict, stats: Dict) -> str:
    """Create X-bar control chart - Professional styling with enhanced visibility"""
    x_bar = subgroups['x_bar']
    r = subgroups['r']

    # Calculate control limits (constants for n=5: A2=0.577)
    r_bar = np.mean(r) if len(r) > 0 else 0
    x_double_bar = np.mean(x_bar) if len(x_bar) > 0 else 0
    A2 = 0.577

    ucl = x_double_bar + A2 * r_bar
    lcl = x_double_bar - A2 * r_bar
    cl = x_double_bar

    fig = go.Figure()

    # Add X-bar values with enhanced visibility
    fig.add_trace(go.Scatter(
        y=x_bar,
        mode='lines+markers',
        name='X-bar',
        line=dict(color='#0891B2', width=3),
        marker=dict(
            size=10,
            color='#0891B2',
            line=dict(width=2, color='white'),
            symbol='circle',
            opacity=0.9
        ),
        hovertemplate='<b>Subgroup %{x}</b><br>X-bar: %{y:.4f}<extra></extra>'
    ))

    # Add control limits with enhanced styling
    fig.add_hline(
        y=ucl,
        line_dash="dash",
        line_color="#DC2626",
        line_width=3,
        annotation_text=f"<b>UCL</b>: {ucl:.4f}",
        annotation_font_size=12,
        annotation_font_color="#DC2626",
        annotation_font_weight="bold"
    )
    fig.add_hline(
        y=cl,
        line_dash="solid",
        line_color="#16A34A",
        line_width=2.5,
        annotation_text=f"<b>CL</b>: {cl:.4f}",
        annotation_font_size=12,
        annotation_font_color="#16A34A",
        annotation_font_weight="bold"
    )
    fig.add_hline(
        y=lcl,
        line_dash="dash",
        line_color="#DC2626",
        line_width=3,
        annotation_text=f"<b>LCL</b>: {lcl:.4f}",
        annotation_font_size=12,
        annotation_font_color="#DC2626",
        annotation_font_weight="bold"
    )

    fig.update_layout(
        title=dict(
            text="2. X-bar Control Chart (均值控制图)",
            font=dict(size=16, color='#1F2937', family='Arial, sans-serif', weight='bold')
        ),
        yaxis=dict(
            title=dict(text="子组均值 Subgroup Mean (X-bar)", font=dict(size=13, weight='bold')),
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1,
            zeroline=True,
            zerolinecolor='gray',
            zerolinewidth=1.5
        ),
        xaxis=dict(
            title=dict(text="子组序号 Subgroup Number", font=dict(size=13, weight='bold')),
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1
        ),
        hovermode='x unified',
        height=450,
        plot_bgcolor='rgba(255, 255, 255, 0.98)',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif', color='#374151', size=11),
        margin=dict(l=60, r=30, t=50, b=60),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11)
        )
    )

    return fig.to_html(full_html=False, include_plotlyjs='cdn')


def _create_r_chart(subgroups: Dict, stats: Dict) -> str:
    """Create R control chart - Professional styling with enhanced visibility and better UI"""
    r_values = subgroups['r']

    # Calculate control limits (constants for n=5: D3=0, D4=2.114)
    r_bar = np.mean(r_values) if len(r_values) > 0 else 0
    D3 = 0
    D4 = 2.114

    ucl = D4 * r_bar
    lcl = D3 * r_bar
    cl = r_bar

    fig = go.Figure()

    # Identify out-of-control points for highlighting
    ooc_colors = ['#DC2626' if (r > ucl or (lcl > 0 and r < lcl)) else '#0891B2' for r in r_values]
    ooc_sizes = [12 if (r > ucl or (lcl > 0 and r < lcl)) else 10 for r in r_values]

    # Add R values with enhanced styling and out-of-control highlighting
    for i, (r, color, size) in enumerate(zip(r_values, ooc_colors, ooc_sizes)):
        fig.add_trace(go.Scatter(
            x=[i+1],
            y=[r],
            mode='markers',
            name='<b>超差 Out of Control</b>' if color == '#DC2626' else '<b>受控 In Control</b>',
            marker=dict(
                size=size,
                color=color,
                line=dict(width=2.5, color='white'),
                symbol='diamond',
                opacity=0.95
            ),
            hovertemplate=f'<b>Subgroup {i+1}</b><br>Range: {r:.4f}<extra></extra>',
            showlegend=True if i == 0 or (i == len(r_values)-1 and color == '#DC2626') else False
        ))

    # Connect points with line
    fig.add_trace(go.Scatter(
        x=list(range(1, len(r_values)+1)),
        y=r_values,
        mode='lines',
        name='Trend Line',
        line=dict(color='#0891B2', width=2.5),
        hoverinfo='skip',
        showlegend=False
    ))

    # Add control limits with ENHANCED styling
    fig.add_hline(
        y=ucl,
        line_dash="dash",
        line_color="#DC2626",
        line_width=4,
        annotation_text=f"<b>上限 UCL</b>: {ucl:.4f}",
        annotation_font_size=13,
        annotation_font_color="#DC2626",
        annotation_font_weight="bold"
    )
    fig.add_hline(
        y=cl,
        line_dash="solid",
        line_color="#16A34A",
        line_width=3,
        annotation_text=f"<b>中心线 CL</b>: {cl:.4f}",
        annotation_font_size=12,
        annotation_font_color="#16A34A",
        annotation_font_weight="bold"
    )
    if lcl > 0:
        fig.add_hline(
            y=lcl,
            line_dash="dash",
            line_color="#DC2626",
            line_width=4,
            annotation_text=f"<b>下限 LCL</b>: {lcl:.4f}",
            annotation_font_size=13,
            annotation_font_color="#DC2626",
            annotation_font_weight="bold"
        )

    # Add statistics annotation box
    ooc_count = sum(1 for r in r_values if r > ucl or (lcl > 0 and r < lcl))
    stats_text = (
        f"<b>极差统计 Range Statistics</b><br>"
        f"══════════════════<br>"
        f"R-bar: <b>{r_bar:.4f}</b><br>"
        f"UCL: <b>{ucl:.4f}</b><br>"
        f"LCL: <b>{lcl:.4f}</b><br>"
        f"超差点 OOC: <b>{ooc_count}</b>/{len(r_values)}"
    )

    fig.add_annotation(
        x=0.98, y=0.98,
        xref='paper', yref='paper',
        text=stats_text,
        showarrow=False,
        bgcolor='rgba(255, 255, 255, 0.98)',
        bordercolor='#0891B2',
        borderwidth=2,
        borderpad=10,
        yanchor='top',
        xanchor='right',
        font=dict(size=11, color='#1F2937')
    )

    fig.update_layout(
        title=dict(
            text="3. R Control Chart (极差控制图)",
            font=dict(size=16, color='#1F2937', family='Arial, sans-serif', weight='bold')
        ),
        yaxis=dict(
            title=dict(text="子组极差 Subgroup Range (R)", font=dict(size=13, weight='bold')),
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1,
            zeroline=True,
            zerolinecolor='gray',
            zerolinewidth=1.5
        ),
        xaxis=dict(
            title=dict(text="子组序号 Subgroup Number", font=dict(size=13, weight='bold')),
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1
        ),
        hovermode='x unified',
        height=450,
        plot_bgcolor='rgba(255, 255, 255, 0.98)',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif', color='#374151', size=11),
        margin=dict(l=60, r=60, t=50, b=60),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11)
        )
    )

    return fig.to_html(full_html=False, include_plotlyjs='cdn')


def _create_histogram(measurements: List[float], usl: float, lsl: float) -> str:
    """Create histogram with normal distribution fit - Enhanced with data points and better UI"""
    measurements_arr = np.array(measurements)
    mu, std = np.mean(measurements_arr), np.std(measurements_arr, ddof=1)

    fig = go.Figure()

    # Add histogram with improved colors and styling
    fig.add_trace(go.Histogram(
        x=measurements,
        nbinsx=20,
        name='实测数据 Measured Data',
        marker_color='#0891B2',
        opacity=0.7,
        marker_line=dict(color='white', width=1.5)
    ))

    # Add normal distribution curve
    x = np.linspace(measurements_arr.min(), measurements_arr.max(), 100)
    y = ((1 / (std * np.sqrt(2 * np.pi))) *
         np.exp(-0.5 * ((x - mu) / std) ** 2))

    # Scale the normal curve to match histogram
    bin_width = (measurements_arr.max() - measurements_arr.min()) / 20
    y_scaled = y * len(measurements) * bin_width

    fig.add_trace(go.Scatter(
        x=x,
        y=y_scaled,
        mode='lines',
        name='正态分布拟合 Normal Fit',
        line=dict(color='#DC2626', width=4)
    ))

    # Add individual data points as rug plot at bottom
    fig.add_trace(go.Scatter(
        x=measurements,
        y=[-0.5] * len(measurements),
        mode='markers',
        name='数据点 Data Points',
        marker=dict(
            size=8,
            color='#0891B2',
            symbol='line-ns',
            line=dict(width=1, color='white'),
            opacity=0.6
        ),
        hovertemplate='<b>Value</b>: %{x:.4f}<extra></extra>',
        showlegend=True
    ))

    # Add specification limits with ENHANCED styling
    # Highlight out-of-spec regions with colored bars
    oos_above = sum(1 for m in measurements if m > usl)
    oos_below = sum(1 for m in measurements if m < lsl)

    fig.add_vline(
        x=usl,
        line_dash="dash",
        line_color="#DC2626",
        line_width=4,
        annotation_text=f"<b>上限 USL</b>: {usl}",
        annotation_position="top right",
        annotation_font_size=13,
        annotation_font_color="#DC2626",
        annotation_font_weight="bold"
    )
    fig.add_vline(
        x=lsl,
        line_dash="dash",
        line_color="#DC2626",
        line_width=4,
        annotation_text=f"<b>下限 LSL</b>: {lsl}",
        annotation_position="top left",
        annotation_font_size=13,
        annotation_font_color="#DC2626",
        annotation_font_weight="bold"
    )

    # Add mean line
    fig.add_vline(
        x=mu,
        line_dash="dot",
        line_color="#16A34A",
        line_width=2.5,
        annotation_text=f"<b>均值 Mean</b>: {mu:.4f}",
        annotation_position="bottom",
        annotation_font_size=11,
        annotation_font_color="#16A34A",
        annotation_font_weight="bold"
    )

    # Add statistics annotation box
    stats_text = (
        f"<b>分布统计 Distribution Stats</b><br>"
        f"══════════════════════<br>"
        f"均值 Mean: <b>{mu:.4f}</b><br>"
        f"标准差 Std: <b>{std:.4f}</b><br>"
        f"样本数 n: <b>{len(measurements)}</b><br>"
        f"<br>"
        f"<b>超差统计 OOS Count</b><br>"
        f"══════════════════════<br>"
        f">USL: <b>{oos_above}</b>   "
        f"<LSL: <b>{oos_below}</b><br>"
        f"总计 Total: <b>{oos_above + oos_below}</b>"
    )

    fig.add_annotation(
        x=0.98, y=0.98,
        xref='paper', yref='paper',
        text=stats_text,
        showarrow=False,
        bgcolor='rgba(255, 255, 255, 0.98)',
        bordercolor='#0891B2',
        borderwidth=2,
        borderpad=10,
        yanchor='top',
        xanchor='right',
        font=dict(size=11, color='#1F2937')
    )

    fig.update_layout(
        title=dict(
            text="4. Histogram with Normal Fit (直方图+正态拟合)",
            font=dict(size=16, color='#1F2937', family='Arial, sans-serif', weight='bold')
        ),
        xaxis=dict(
            title=dict(text="测量值 Measured Value", font=dict(size=13, weight='bold')),
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1
        ),
        yaxis=dict(
            title=dict(text="频数 Frequency", font=dict(size=13, weight='bold')),
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1
        ),
        barmode='overlay',
        height=450,
        plot_bgcolor='rgba(255, 255, 255, 0.98)',
        paper_bgcolor='white',
        margin=dict(l=60, r=60, t=50, b=60),
        font=dict(family='Arial, sans-serif', color='#374151', size=11),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10)
        )
    )

    return fig.to_html(full_html=False, include_plotlyjs='cdn')


def _create_qq_plot(measurements: List[float]) -> str:
    """Create Q-Q plot for normality assessment - Professional styling"""
    measurements_arr = np.array(measurements)

    # Calculate theoretical quantiles
    theoretical_quantiles = np.percentile(
        np.random.normal(0, 1, 10000),
        np.linspace(1, 99, len(measurements_arr))
    )
    sample_quantiles = np.sort(measurements_arr)

    # Normalize sample quantiles
    sample_mean = np.mean(measurements_arr)
    sample_std = np.std(measurements_arr, ddof=1)
    sample_quantiles_normalized = (sample_quantiles - sample_mean) / sample_std

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=theoretical_quantiles,
        y=sample_quantiles_normalized,
        mode='markers',
        name='样本分位数 Sample Quantiles',
        marker=dict(color='#0891B2', size=9, line=dict(width=1, color='white'))
    ))

    # Add reference line (y = x)
    fig.add_trace(go.Scatter(
        x=[-3, 3],
        y=[-3, 3],
        mode='lines',
        name='参考线 Reference (y=x)',
        line=dict(color='#DC2626', dash='dash', width=2.5)
    ))

    fig.update_layout(
        title=dict(
            text="5. Q-Q Plot (正态性检验)",
            font=dict(size=15, color='#1F2937', family='Arial, sans-serif')
        ),
        xaxis=dict(
            title=dict(text="理论分位数 Theoretical Quantile (标准正态)", font=dict(size=12)),
            showgrid=True, gridcolor='rgba(0,0,0,0.05)',
            zeroline=True, zerolinecolor='gray', zerolinewidth=1
        ),
        yaxis=dict(
            title=dict(text="样本分位数 Sample Quantile (标准化)", font=dict(size=12)),
            showgrid=True, gridcolor='rgba(0,0,0,0.05)',
            zeroline=True, zerolinecolor='gray', zerolinewidth=1
        ),
        height=420,
        plot_bgcolor='rgba(255, 255, 255, 0.98)',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif', color='#374151')
    )

    return fig.to_html(full_html=False, include_plotlyjs='cdn')


def _create_capability_plot(measurements: List[float], usl: float, lsl: float, stats: Dict) -> str:
    """Create capability plot with distribution and limits - Enhanced with prominent LSL/USL labels"""
    measurements_arr = np.array(measurements)
    mu, std = np.mean(measurements_arr), np.std(measurements_arr, ddof=1)

    fig = go.Figure()

    # Generate distribution curve
    x = np.linspace(measurements_arr.min() - 0.5, measurements_arr.max() + 0.5, 200)
    y = ((1 / (std * np.sqrt(2 * np.pi))) *
         np.exp(-0.5 * ((x - mu) / std) ** 2))

    # Add distribution curve with gradient fill
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='lines',
        name='概率密度分布 Probability Density',
        line=dict(color='#0891B2', width=3),
        fill='tozeroy',
        fillcolor='rgba(8, 145, 178, 0.15)'
    ))

    # Add shaded regions for out-of-specification areas
    # Above USL
    x_usl = np.linspace(usl, measurements_arr.max() + 0.5, 50)
    y_usl = ((1 / (std * np.sqrt(2 * np.pi))) *
             np.exp(-0.5 * ((x_usl - mu) / std) ** 2))
    fig.add_trace(go.Scatter(
        x=x_usl,
        y=y_usl,
        mode='lines',
        name='超差区 >USL',
        line=dict(color='#DC2626', width=0),
        fill='tozeroy',
        fillcolor='rgba(220, 38, 38, 0.25)',
        showlegend=True
    ))

    # Below LSL
    x_lsl = np.linspace(measurements_arr.min() - 0.5, lsl, 50)
    y_lsl = ((1 / (std * np.sqrt(2 * np.pi))) *
             np.exp(-0.5 * ((x_lsl - mu) / std) ** 2))
    fig.add_trace(go.Scatter(
        x=x_lsl,
        y=y_lsl,
        mode='lines',
        name='超差区 <LSL',
        line=dict(color='#DC2626', width=0),
        fill='tozeroy',
        fillcolor='rgba(220, 38, 38, 0.25)',
        showlegend=True
    ))

    # Calculate y values at specification limits for reference
    y_at_usl = ((1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((usl - mu) / std) ** 2))
    y_at_lsl = ((1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((lsl - mu) / std) ** 2))

    # Add specification limits with ENHANCED styling - both vertical and point markers
    fig.add_vline(
        x=usl,
        line_dash="dash",
        line_color="#DC2626",
        line_width=5,
        annotation_text=f"<b>上限 USL</b>: {usl}",
        annotation_position="top right",
        annotation_font_size=14,
        annotation_font_color="#DC2626",
        annotation_font_weight="bold",
        annotation_textangle=0
    )
    fig.add_vline(
        x=lsl,
        line_dash="dash",
        line_color="#DC2626",
        line_width=5,
        annotation_text=f"<b>下限 LSL</b>: {lsl}",
        annotation_position="top left",
        annotation_font_size=14,
        annotation_font_color="#DC2626",
        annotation_font_weight="bold",
        annotation_textangle=0
    )

    # Add point markers on the curve at LSL and USL positions for y-axis visibility
    fig.add_trace(go.Scatter(
        x=[usl],
        y=[y_at_usl],
        mode='markers+text',
        name='<b>USL位置</b>',
        marker=dict(size=15, color='#DC2626', symbol='diamond', line=dict(width=2, color='white')),
        text=['<b>USL</b>'],
        textposition='top center',
        textfont=dict(size=11, color='#DC2626', family='Arial, sans-serif'),
        showlegend=True,
        hovertemplate=f'<b>USL</b>: {usl}<br>Y: {y_at_usl:.4f}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=[lsl],
        y=[y_at_lsl],
        mode='markers+text',
        name='<b>LSL位置</b>',
        marker=dict(size=15, color='#DC2626', symbol='diamond', line=dict(width=2, color='white')),
        text=['<b>LSL</b>'],
        textposition='top center',
        textfont=dict(size=11, color='#DC2626', family='Arial, sans-serif'),
        showlegend=True,
        hovertemplate=f'<b>LSL</b>: {lsl}<br>Y: {y_at_lsl:.4f}<extra></extra>'
    ))

    # Add target/nominal line (center of specification)
    target = (usl + lsl) / 2
    y_at_target = ((1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((target - mu) / std) ** 2))

    fig.add_vline(
        x=target,
        line_dash="dot",
        line_color="#22C55E",
        line_width=2.5,
        annotation_text=f"<b>目标 Target</b>: {target:.4f}",
        annotation_position="top",
        annotation_font_size=12,
        annotation_font_color="#22C55E",
        annotation_font_weight="bold"
    )

    # Add mean line
    y_at_mean = ((1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((mu - mu) / std) ** 2))

    fig.add_vline(
        x=mu,
        line_dash="solid",
        line_color="#16A34A",
        line_width=2.5,
        annotation_text=f"<b>均值 Mean</b>: {mu:.4f}",
        annotation_position="bottom",
        annotation_font_size=12,
        annotation_font_color="#16A34A",
        annotation_font_weight="bold"
    )

    # Add mean marker on curve
    fig.add_trace(go.Scatter(
        x=[mu],
        y=[y_at_mean],
        mode='markers',
        name='<b>均值峰值</b>',
        marker=dict(size=12, color='#16A34A', symbol='circle', line=dict(width=2, color='white')),
        showlegend=True,
        hovertemplate=f'<b>Mean Peak</b><br>X: {mu:.4f}<br>Y: {y_at_mean:.4f}<extra></extra>'
    ))

    # Calculate PPM
    ppm_above = ((measurements_arr > usl).sum() / len(measurements_arr)) * 1e6
    ppm_below = ((measurements_arr < lsl).sum() / len(measurements_arr)) * 1e6
    ppm_total = ppm_above + ppm_below

    # Calculate specification width and process centering
    spec_width = usl - lsl
    centering = ((mu - target) / (spec_width / 2)) * 100 if spec_width > 0 else 0

    # Professional annotation box - Chinese + English bilingual
    annotation_text = (
        f"<b>能力指数 Capability Indices</b><br>"
        f"══════════════════<br>"
        f"Cp:  <b>{stats['cp']:.3f}</b>   "
        f"Cpk: <b>{stats['cpk']:.3f}</b><br>"
        f"Pp:  <b>{stats['pp']:.3f}</b>   "
        f"Ppk: <b>{stats['ppk']:.3f}</b><br>"
        f"<br>"
        f"<b>百万分率 PPM (Defect Rate)</b><br>"
        f"══════════════════════════<br>"
        f"总计 Total: <b>{ppm_total:.0f}</b><br>"
        f">USL: <b>{ppm_above:.0f}</b>   "
        f"<LSL: <b>{ppm_below:.0f}</b><br>"
        f"<br>"
        f"<b>规格中心ing: {centering:+.1f}%</b><br>"
        f"<br>"
        f"<b>规格限值 Spec Limits</b><br>"
        f"══════════════════════<br>"
        f"USL: <b>{usl:.4f}</b><br>"
        f"LSL: <b>{lsl:.4f}</b>"
    )

    fig.add_annotation(
        x=0.98, y=0.98,
        xref='paper', yref='paper',
        text=annotation_text,
        showarrow=False,
        bgcolor='rgba(255, 255, 255, 0.98)',
        bordercolor='#0891B2',
        borderwidth=3,
        borderpad=12,
        yanchor='top',
        xanchor='right',
        font=dict(size=11, color='#1F2937')
    )

    # Focus x-axis on data range (add 15% padding)
    x_min = measurements_arr.min()
    x_max = measurements_arr.max()
    x_padding = (x_max - x_min) * 0.15

    fig.update_layout(
        title=dict(
            text="6. Capability Plot (过程能力分析图)",
            font=dict(size=16, color='#1F2937', family='Arial, sans-serif', weight='bold')
        ),
        xaxis=dict(
            title=dict(text="测量值 Measurement Value", font=dict(size=13, weight='bold')),
            range=[x_min - x_padding, x_max + x_padding],
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1,
            zeroline=False
        ),
        yaxis=dict(
            title=dict(text="概率密度 Probability Density", font=dict(size=13, weight='bold')),
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1
        ),
        height=480,
        plot_bgcolor='rgba(255, 255, 255, 0.98)',
        paper_bgcolor='white',
        margin=dict(l=60, r=60, t=60, b=60),
        font=dict(family='Arial, sans-serif', color='#374151', size=11),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=10)
        )
    )

    return fig.to_html(full_html=False, include_plotlyjs='cdn')


def generate_professional_dashboard(dim_data: List[Dict], stats_list: List[Dict], layout: str = "tabbed") -> str:
    """
    Generate professional HTML dashboard with tabbed interface.

    Args:
        dim_data: List of dimension sets from OCR
        stats_list: List of SPC statistics (one per dimension)
        layout: "tabbed" or "scrollable"

    Returns:
        HTML file path
    """
    if not dim_data or not stats_list:
        raise ValueError("dim_data and stats_list cannot be empty")

    # Create reports directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)

    # Generate executive summary HTML
    summary_html = _generate_executive_summary(dim_data, stats_list)

    # Generate dimension tabs and content
    dimension_tabs_html = ""
    dimension_content_html = ""

    for i, (dim, stats) in enumerate(zip(dim_data, stats_list)):
        tab_id = f"dim_{i}"
        dim_name = dim['header']['dimension_name']

        # Tab button
        active_class = "active" if i == 0 else ""
        dimension_tabs_html += f'<div class="tab {active_class}" onclick="showTab(\'{tab_id}\')">{dim_name}</div>\n'

        # Tab content
        display_style = "" if i == 0 else "display: none;"
        dimension_content_html += f'<div id="{tab_id}" class="tab-content" style="{display_style}">\n'
        dimension_content_html += _generate_dimension_content(dim, stats, i)
        dimension_content_html += '</div>\n'

    # Full HTML template
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>6SPC Pro Max - Quality Analysis Report</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        /* Medical-grade professional styling */
        :root {{
            --primary: #0891B2;
            --primary-dark: #0E7490;
            --success: #22C55E;
            --danger: #EF4444;
            --warning: #F59E0B;
            --bg: #F8FAFC;
            --surface: #FFFFFF;
            --text: #1E293B;
            --text-light: #64748B;
            --border: #E2E8F0;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* Header */
        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 40px;
            border-radius: 16px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(8, 145, 178, 0.2);
        }}

        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}

        .header p {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}

        /* Tab Navigation */
        .tab-container {{
            background: var(--surface);
            border-radius: 12px;
            padding: 0;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            overflow: hidden;
        }}

        .tabs {{
            display: flex;
            border-bottom: 2px solid var(--border);
            overflow-x: auto;
        }}

        .tab {{
            padding: 16px 24px;
            cursor: pointer;
            background: var(--surface);
            border: none;
            font-size: 1rem;
            font-weight: 500;
            color: var(--text-light);
            transition: all 0.3s ease;
            white-space: nowrap;
            border-bottom: 3px solid transparent;
        }}

        .tab:hover {{
            background: var(--bg);
            color: var(--primary);
        }}

        .tab.active {{
            color: var(--primary);
            border-bottom-color: var(--primary);
            background: var(--bg);
        }}

        /* Tab Content */
        .tab-content {{
            background: var(--surface);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            min-height: 600px;
        }}

        /* Status badges */
        .status-pass {{
            display: inline-block;
            padding: 6px 16px;
            background: #DCFCE7;
            color: #166534;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
        }}

        .status-fail {{
            display: inline-block;
            padding: 6px 16px;
            background: #FEE2E2;
            color: #991B1B;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: var(--surface);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        th {{
            background: var(--primary);
            color: white;
            padding: 16px;
            text-align: left;
            font-weight: 600;
        }}

        td {{
            padding: 14px 16px;
            border-bottom: 1px solid var(--border);
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        tr:hover {{
            background: var(--bg);
        }}

        /* Info cards */
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}

        .info-card {{
            background: var(--bg);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid var(--primary);
        }}

        .info-card h4 {{
            color: var(--text-light);
            font-size: 0.9rem;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .info-card .value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text);
        }}

        /* Chart containers */
        .chart {{
            margin: 30px 0;
            padding: 20px;
            background: var(--bg);
            border-radius: 8px;
        }}

        .chart h3 {{
            margin-bottom: 15px;
            color: var(--primary-dark);
        }}

        /* Print styles */
        @media print {{
            .tab-container, .tabs {{
                display: none;
            }}
            .tab-content {{
                display: block !important;
                page-break-before: always;
            }}
            body {{
                background: white;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🛡️ 6SPC Pro Max 质量分析报告</h1>
            <p>ISO 13485 Compliant | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <!-- Tab Navigation -->
        <div class="tab-container">
            <div class="tabs">
                <div class="tab active" onclick="showTab('summary')">📊 Executive Summary</div>
                {dimension_tabs_html}
            </div>
        </div>

        <!-- Executive Summary Tab -->
        <div id="summary" class="tab-content">
            {summary_html}
        </div>

        <!-- Dimension Tabs Content -->
        {dimension_content_html}
    </div>

    <script>
        function showTab(tabId) {{
            // Hide all tabs
            var contents = document.querySelectorAll('.tab-content');
            contents.forEach(function(content) {{
                content.style.display = 'none';
                content.classList.remove('active');
            }});

            // Remove active class from all tabs
            var tabs = document.querySelectorAll('.tab');
            tabs.forEach(function(tab) {{
                tab.classList.remove('active');
            }});

            // Show selected tab
            document.getElementById(tabId).style.display = 'block';
            document.getElementById(tabId).classList.add('active');

            // Set active tab styling
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>"""

    # Write to file
    timestamp = int(time.time())
    filename = f"6spc_report_{timestamp}.html"
    filepath = os.path.join("reports", filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_template)

    print(f"✅ Dashboard generated: {filepath}")
    return filepath


def _generate_executive_summary(dim_data: List[Dict], stats_list: List[Dict]) -> str:
    """Generate executive summary with pass/fail matrix and AI analysis"""

    analyzer = PlasticInjectionAnalyzer()

    # Generate analyses for all dimensions
    analyses = []
    for dim, stats in zip(dim_data, stats_list):
        analysis = analyzer.analyze_dimension(dim, stats)
        analyses.append(analysis)

    # Generate executive summary
    exec_summary = analyzer.generate_executive_summary(analyses)

    # Summary table with risk indicators
    rows = ""
    for i, (dim, stats, analysis) in enumerate(zip(dim_data, stats_list, analyses)):
        header = dim['header']
        status_class = "status-pass" if stats['cpk_status'] == "PASS" else "status-fail"
        status_text = stats['cpk_status']

        # Risk indicator
        risk_colors = {
            'LOW': '#22C55E',
            'MEDIUM': '#F59E0B',
            'HIGH': '#F97316',
            'CRITICAL': '#DC2626'
        }
        risk_color = risk_colors.get(analysis['risk_level'], '#6B7280')

        rows += f"""
        <tr>
            <td><strong>{header['dimension_name']}</strong></td>
            <td>{header['batch_id']}</td>
            <td>{stats['mean']:.4f}</td>
            <td>{stats['cpk']:.3f}</td>
            <td>{stats['ppk']:.3f}</td>
            <td><span class="{status_class}">{status_text}</span></td>
            <td><span style="color: {risk_color}; font-weight: bold;">{analysis['status_emoji']} {analysis['risk_level']}</span></td>
        </tr>
        """

    # Status distribution
    status_dist = exec_summary['status_distribution']

    return f"""
    <h2>📊 Executive Summary | 执行摘要</h2>

    <div class="info-grid">
        <div class="info-card">
            <h4>Total Dimensions</h4>
            <div class="value">{exec_summary['total_dimensions']}</div>
        </div>
        <div class="info-card">
            <h4>Pass Rate</h4>
            <div class="value">{exec_summary['pass_rate']:.1f}%</div>
        </div>
        <div class="info-card">
            <h4>Compliance</h4>
            <div class="value">ISO 13485</div>
        </div>
        <div class="info-card">
            <h4>Overall Status</h4>
            <div class="value" style="font-size: 1.2rem;">
                {'✅ EXCELLENT' if exec_summary['pass_rate'] >= 90 else '⚠️ ACCEPTABLE' if exec_summary['pass_rate'] >= 70 else '🔧 NEEDS WORK'}
            </div>
        </div>
    </div>

    <div style="margin: 30px 0; padding: 25px; background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%); border-radius: 12px; border-left: 5px solid #3B82F6; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h3 style="color: #1E40AF; margin-top: 0;">🤖 AI 整体评估 Overall Process Assessment</h3>
        <p style="color: #1E3A8A; line-height: 1.8; font-size: 15px;">
            {exec_summary['overall_recommendation'].replace('**', '<strong>').replace('**', '</strong>')}
        </p>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 20px;">
            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 24px;">🏆</div>
                <div style="font-size: 20px; font-weight: bold; color: #22C55E;">{status_dist['excellent']}</div>
                <div style="font-size: 12px; color: #6B7280;">Excellent</div>
            </div>
            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 24px;">✅</div>
                <div style="font-size: 20px; font-weight: bold; color: #3B82F6;">{status_dist['good']}</div>
                <div style="font-size: 12px; color: #6B7280;">Good</div>
            </div>
            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 24px;">⚠️</div>
                <div style="font-size: 20px; font-weight: bold; color: #F59E0B;">{status_dist['acceptable']}</div>
                <div style="font-size: 12px; color: #6B7280;">Acceptable</div>
            </div>
            <div style="background: white; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 24px;">🚨</div>
                <div style="font-size: 20px; font-weight: bold; color: #DC2626;">{status_dist['needs_work']}</div>
                <div style="font-size: 12px; color: #6B7280;">Critical</div>
            </div>
        </div>
    </div>

    <h3>Pass/Fail Matrix | 通过/失败矩阵</h3>
    <table>
        <thead>
            <tr>
                <th>Dimension 尺寸</th>
                <th>Batch ID 批次</th>
                <th>Mean 均值</th>
                <th>Cpk</th>
                <th>Ppk</th>
                <th>Status 状态</th>
                <th>Risk 风险</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>

    <div style="margin-top: 30px; padding: 20px; background: #F0FDF4; border-radius: 8px; border-left: 4px solid #22C55E;">
        <h4 style="color: #166534; margin-bottom: 10px;">📋 Analysis Criteria | 分析标准</h4>
        <ul style="color: #166534; margin-left: 20px; line-height: 1.8;">
            <li><strong>Cpk ≥ 1.67:</strong> 6-Sigma 卓越水平 (Excellent)</li>
            <li><strong>Cpk ≥ 1.33:</strong> 4-Sigma 充足能力 (Capable - PASS)</li>
            <li><strong>Cpk ≥ 1.00:</strong> 3-Sigma 基本能力 (Acceptable - 需监控)</li>
            <li><strong>Cpk < 1.00:</strong> 能力不足 (Needs Improvement - 需改善)</li>
            <li>所有尺寸均采用 6 SPC 方法论分析 (All dimensions analyzed with 6 SPC methodology)</li>
        </ul>
    </div>
    """


def _generate_dimension_content(dim: Dict, stats: Dict, index: int) -> str:
    """Generate content for one dimension tab"""

    header = dim['header']
    measurements = dim['measurements']

    # Header info
    info_html = f"""
    <div class="info-grid">
        <div class="info-card">
            <h4>Dimension</h4>
            <div class="value">{header['dimension_name']}</div>
        </div>
        <div class="info-card">
            <h4>Batch ID</h4>
            <div class="value">{header['batch_id']}</div>
        </div>
        <div class="info-card">
            <h4>USL</h4>
            <div class="value">{header['usl']}</div>
        </div>
        <div class="info-card">
            <h4>LSL</h4>
            <div class="value">{header['lsl']}</div>
        </div>
    </div>
    """

    # Statistics table
    stats_html = f"""
    <h3>📈 Statistics Summary</h3>
    <table>
        <thead>
            <tr>
                <th>Metric</th>
                <th>Value</th>
                <th>Metric</th>
                <th>Value</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Mean</strong></td>
                <td>{stats['mean']:.4f}</td>
                <td><strong>Std Dev (Overall)</strong></td>
                <td>{stats['std_overall']:.4f}</td>
            </tr>
            <tr>
                <td><strong>Cp</strong></td>
                <td>{stats['cp']:.3f}</td>
                <td><strong>Cpk</strong></td>
                <td>{stats['cpk']:.3f}</td>
            </tr>
            <tr>
                <td><strong>Pp</strong></td>
                <td>{stats['pp']:.3f}</td>
                <td><strong>Ppk</strong></td>
                <td>{stats['ppk']:.3f}</td>
            </tr>
            <tr>
                <td><strong>Min</strong></td>
                <td>{stats['min']:.4f}</td>
                <td><strong>Max</strong></td>
                <td>{stats['max']:.4f}</td>
            </tr>
            <tr>
                <td><strong>Count</strong></td>
                <td>{stats['count']}</td>
                <td><strong>Status</strong></td>
                <td><span class="{'status-pass' if stats['cpk_status'] == 'PASS' else 'status-fail'}">{stats['cpk_status']}</span></td>
            </tr>
        </tbody>
    </table>
    """

    # Generate all 6 SPC charts with Plotly HTML
    charts_html = """
    <h3>📊 SPC Charts</h3>
    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
        <div class="chart">
            <h4>1. Individual Values Plot</h4>
            """ + _create_individual_plot(measurements, header['usl'], header['lsl']) + """
        </div>
        <div class="chart">
            <h4>2. X-bar Control Chart</h4>
            """ + _create_xbar_chart(stats.get('subgroups', {}), stats) + """
        </div>
        <div class="chart">
            <h4>3. R Control Chart</h4>
            """ + _create_r_chart(stats.get('subgroups', {}), stats) + """
        </div>
        <div class="chart">
            <h4>4. Histogram with Normal Fit</h4>
            """ + _create_histogram(measurements, header['usl'], header['lsl']) + """
        </div>
        <div class="chart" style="grid-column: span 2;">
            <h4>5. Q-Q Plot</h4>
            """ + _create_qq_plot(measurements) + """
        </div>
        <div class="chart" style="grid-column: span 2;">
            <h4>6. Capability Plot</h4>
            """ + _create_capability_plot(measurements, header['usl'], header['lsl'], stats) + """
        </div>
    </div>
    """

    # AI-Powered Analysis Section
    analyzer = PlasticInjectionAnalyzer()
    analysis = analyzer.analyze_dimension(dim, stats)

    # Convert markdown-like formatting to HTML
    def format_analysis_text(text: str) -> str:
        """Convert markdown formatting to HTML"""
        text = text.replace('**', '<strong>').replace('**', '</strong>')
        text = text.replace('\n', '<br>')
        return text

    analysis_html = f"""
    <div style="margin-top: 30px; padding: 25px; background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); border-radius: 12px; border-left: 5px solid #F59E0B; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h3 style="color: #92400E; margin-top: 0; display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 24px;">{analysis['status_emoji']}</span>
            <span>AI 工艺分析 - Plastic Injection Process Analysis</span>
            <span style="margin-left: auto; padding: 5px 15px; background: white; border-radius: 20px; font-size: 12px; font-weight: bold;">
                {analysis['status']} | RISK: {analysis['risk_level']}
            </span>
        </h3>

        <div style="background: white; padding: 20px; border-radius: 8px; margin-top: 15px;">
            <h4 style="color: #1F2937; margin-top: 0;">📊 总体评估 Overall Assessment</h4>
            <p style="color: #374151; line-height: 1.8; margin-bottom: 20px;">
                {format_analysis_text(analysis['overall_assessment'])}
            </p>

            <h4 style="color: #1F2937; margin-top: 20px;">🎯 能力分析 Capability Analysis</h4>
            <p style="color: #374151; line-height: 1.8; margin-bottom: 20px;">
                {format_analysis_text(analysis['capability_analysis'])}
            </p>

            <h4 style="color: #1F2937; margin-top: 20px;">📈 稳定性分析 Stability Analysis</h4>
            <p style="color: #374151; line-height: 1.8; margin-bottom: 20px;">
                {format_analysis_text(analysis['stability_analysis'])}
            </p>

            <h4 style="color: #1F2937; margin-top: 20px;">🔧 改善建议 Improvement Actions</h4>
            <div style="margin-top: 10px;">
    """

    # Add improvement actions
    for action in analysis['improvement_actions']:
        analysis_html += f"""
                <div style="background: #EFF6FF; padding: 15px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #3B82F6;">
                    <p style="margin: 0; color: #1F2937; line-height: 1.6;">{format_analysis_text(action)}</p>
                </div>
        """

    # Add hot runner tips
    analysis_html += """
            </div>

            <h4 style="color: #1F2937; margin-top: 20px;">🌡️ 热流道系统建议 Hot Runner Tips</h4>
            <div style="margin-top: 10px;">
    """

    for tip in analysis['hot_runner_tips']:
        analysis_html += f"""
                <div style="background: #ECFDF5; padding: 15px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #10B981;">
                    <p style="margin: 0; color: #1F2937; line-height: 1.6;">{format_analysis_text(tip)}</p>
                </div>
        """

    analysis_html += """
            </div>
        </div>
    </div>
    """

    # Data table
    data_rows = ""
    for j, val in enumerate(measurements, 1):
        data_rows += f"<tr><td>{j}</td><td>{val:.4f}</td></tr>\n"

    data_html = f"""
    <h3>📋 Measurement Data</h3>
    <table>
        <thead>
            <tr>
                <th>序号</th>
                <th>测量值</th>
            </tr>
        </thead>
        <tbody>
            {data_rows}
        </tbody>
    </table>
    """

    return info_html + stats_html + analysis_html + charts_html + data_html
