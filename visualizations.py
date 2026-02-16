"""
可视化工具 - 情绪轨迹图
"""
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd

def create_emotion_timeline(records):
    """创建情绪时间线图（羽毛球场风格）"""
    if not records:
        # 返回空图
        fig = go.Figure()
        fig.update_layout(
            title="暂无数据",
            xaxis_title="时间",
            yaxis_title="心情指数"
        )
        return fig
    
    # 准备数据
    df = pd.DataFrame([
        {
            '时间': r.created_at,
            '心情': r.emotion_score,
            '发送者': '我' if r.sender == 'me' else '他',
            '内容': r.content[:15] + '...' if len(r.content) > 15 else r.content,
            '动作': r.action
        } for r in records
    ])
    
    # 按时间排序
    df = df.sort_values('时间')
    
    # 创建颜色映射
    colors = {'我': '#ff69b4', '他': '#4169e1'}
    
    # 创建图形
    fig = go.Figure()
    
    # 添加羽毛球轨迹线（用散点图连接）
    fig.add_trace(go.Scatter(
        x=df['时间'],
        y=df['心情'],
        mode='lines+markers',
        line=dict(color='rgba(255,255,255,0.3)', width=2, dash='dot'),
        marker=dict(size=8),
        name='心情轨迹',
        hoverinfo='none'
    ))
    
    # 添加发送者标记
    for sender in ['我', '他']:
        sender_df = df[df['发送者'] == sender]
        if not sender_df.empty:
            fig.add_trace(go.Scatter(
                x=sender_df['时间'],
                y=sender_df['心情'],
                mode='markers+text',
                marker=dict(
                    size=12,
                    color=colors[sender],
                    symbol='circle',
                    line=dict(color='white', width=2)
                ),
                text=sender_df['发送者'],
                textposition="top center",
                name=sender,
                hovertemplate=
                "<b>%{text}</b><br>" +
                "时间: %{x|%m-%d %H:%M}<br>" +
                "心情: %{y}/10<br>" +
                "内容: %{customdata}<br>" +
                "<extra></extra>",
                customdata=sender_df['内容']
            ))
    
    # 更新布局为球场风格
    fig.update_layout(
        title=dict(
            text="🏸 爱的球路轨迹",
            font=dict(size=20, color='white')
        ),
        plot_bgcolor='rgba(27, 77, 27, 0.3)',  # 球场绿半透明
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            title="时间",
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title="心情指数",
            gridcolor='rgba(255,255,255,0.1)',
            showgrid=True,
            range=[0, 11],
            tickmode='linear',
            tick0=1,
            dtick=1
        ),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # 添加羽毛球场氛围：半透明底色区域
    fig.add_hrect(
        y0=0, y1=11,
        line_width=0,
        fillcolor="rgba(255,255,255,0.05)",
        layer="below"
    )
    
    return fig

def create_emotion_heatmap(records, days=30):
    """创建情绪热力图（显示每个时间段的情绪）"""
    if not records:
        return go.Figure()
    
    # 准备数据
    df = pd.DataFrame([
        {
            '日期': r.created_at.date(),
            '小时': r.created_at.hour,
            '心情': r.emotion_score
        } for r in records
    ])
    
    # 创建透视表
    pivot = pd.pivot_table(
        df,
        values='心情',
        index='小时',
        columns='日期',
        aggfunc='mean',
        fill_value=0
    )
    
    # 创建热力图
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='Viridis',
        hovertemplate='日期: %{x}<br>时间: %{y}:00<br>平均心情: %{z:.1f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="📊 情绪时段分布",
        xaxis_title="日期",
        yaxis_title="小时",
        plot_bgcolor='rgba(27, 77, 27, 0.3)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    return fig