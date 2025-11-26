// 优惠券领取-使用转化桑基图
$(document).ready(function() {
    // 初始化桑基图
    const sankeyChart = echarts.init(document.getElementById('coupon-sankey-diagram'));
    
    // 加载动画
    sankeyChart.showLoading({
        text: '数据加载中...',
        color: '#f39c12',
        textColor: '#000',
        maskColor: 'rgba(255, 255, 255, 0.8)',
        zlevel: 0
    });
    
    // 获取当前URL中的日期参数
    const urlParams = new URLSearchParams(window.location.search);
    const startDate = urlParams.get('start_date') || '';
    const endDate = urlParams.get('end_date') || '';
    const dateRange = urlParams.get('date_range') || 'last_30_days';
    
    // 从后端API获取数据
    $.ajax({
        url: '/admin/user_marketing/sankey_data',
        type: 'GET',
        data: {
            start_date: startDate,
            end_date: endDate,
            date_range: dateRange
        },
        success: function(response) {
            // 隐藏加载动画
            sankeyChart.hideLoading();
            
            // 渲染桑基图
            renderSankeyChart(sankeyChart, response);
            
            // 添加汇总信息
            addSummaryCards(response.summary);
        },
        error: function(xhr, status, error) {
            // 隐藏加载动画，显示错误信息
            sankeyChart.hideLoading();
            console.error('获取桑基图数据失败:', error);
            
            // 显示错误消息
            $('#coupon-sankey-diagram').html(`
                <div class="text-center text-danger">
                    <i class="bi bi-exclamation-triangle-fill fs-1"></i>
                    <p>数据加载失败，请稍后再试</p>
                </div>
            `);
        }
    });
    
    // 窗口调整大小时，重新调整图表尺寸
    $(window).resize(function() {
        sankeyChart.resize();
    });
});

// 渲染桑基图
function renderSankeyChart(chart, data) {
    const nodes = data.nodes;
    const links = data.links;
    
    // 确保数据有效
    if (!nodes || !links || nodes.length === 0 || links.length === 0) {
        $('#coupon-sankey-diagram').html(`
            <div class="text-center text-warning py-5">
                <i class="bi bi-exclamation-circle fs-1"></i>
                <p>没有足够的数据来生成桑基图</p>
                <small>请选择不同的时间范围或等待更多数据收集</small>
            </div>
        `);
        return;
    }
    
    // 增强链接的视觉效果
    links.forEach(link => {
        // 使用渐变效果
        const sourceNode = nodes[link.source];
        const targetNode = nodes[link.target];
        
        if (sourceNode && targetNode) {
            link.lineStyle = {
                color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                    {offset: 0, color: sourceNode.itemStyle ? sourceNode.itemStyle.color : 'rgba(255, 165, 45, 0.8)'},
                    {offset: 1, color: targetNode.itemStyle ? targetNode.itemStyle.color : 'rgba(255, 125, 45, 0.8)'}
                ]),
                opacity: 0.7,
                shadowColor: 'rgba(0, 0, 0, 0.2)',
                shadowBlur: 5,
                shadowOffsetX: 2,
                shadowOffsetY: 2,
                curveness: 0.5
            };
        }
    });
    
    // 配置选项
    const option = {
        title: {
            text: `优惠券流转分析 (${data.summary.period})`,
            subtext: `总计${data.summary.total_coupons}张优惠券，使用率${data.summary.usage_rate}%`,
            left: 'center',
            top: 0,
            textStyle: {
                fontSize: 16,
                color: '#333'
            },
            subtextStyle: {
                fontSize: 12,
                color: '#999'
            }
        },
        tooltip: {
            trigger: 'item',
            triggerOn: 'mousemove',
            formatter: function(params) {
                if (params.dataType === 'edge') {
                    // 链接的提示框
                    return `<div style="padding: 8px">
                        <div style="font-weight: bold; margin-bottom: 5px;">${nodes[params.data.source].name} → ${nodes[params.data.target].name}</div>
                        <div>流量: <span style="color:#ff9f43; font-weight: bold">${params.data.value.toLocaleString()}</span> 张优惠券</div>
                        <div>占比: <span style="color:#2ecc71">${(params.data.value / data.summary.total_coupons * 100).toFixed(1)}%</span></div>
                    </div>`;
                } else {
                    // 节点的提示框
                    return `<div style="padding: 8px">
                        <div style="font-weight: bold; margin-bottom: 5px;">${params.data.name}</div>
                        <div>数量: <span style="color:#3498db; font-weight: bold">${params.value.toLocaleString()}</span> 张优惠券</div>
                    </div>`;
                }
            },
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: 'rgba(255,200,100,0.3)',
            borderWidth: 1,
            textStyle: {
                color: '#666'
            },
            extraCssText: 'box-shadow: 0 4px 14px rgba(0,0,0,0.1); border-radius: 8px;'
        },
        series: [{
            type: 'sankey',
            layoutIterations: 64,
            nodeWidth: 24,
            nodePadding: 16,
            focusNodeAdjacency: true,
            nodeAlign: 'justify',
            orient: 'horizontal',
            label: {
                show: true,
                position: 'right',
                fontSize: 12,
                color: '#666',
                fontWeight: 'bold'
            },
            lineStyle: {
                color: 'source',
                opacity: 0.6,
                curveness: 0.5
            },
            itemStyle: {
                borderWidth: 1,
                borderColor: '#fff',
                shadowColor: 'rgba(0, 0, 0, 0.2)',
                shadowBlur: 5
            },
            emphasis: {
                label: {
                    fontSize: 14,
                    color: '#333',
                    fontWeight: 'bold',
                    textShadowBlur: 3,
                    textShadowColor: 'rgba(255, 255, 255, 0.7)'
                },
                lineStyle: {
                    opacity: 0.9,
                    width: 2,
                    shadowBlur: 20,
                    shadowColor: 'rgba(0, 0, 0, 0.4)'
                },
                itemStyle: {
                    shadowBlur: 20,
                    shadowColor: 'rgba(0, 0, 0, 0.4)'
                }
            },
            data: nodes,
            links: links,
            levels: [
                { depth: 0, itemStyle: { color: '#59a6ff' } },
                { depth: 1, itemStyle: { color: '#f5bd25' } },
                { depth: 2, itemStyle: { color: '#fc7c43' } }
            ],
            // 动画效果
            animation: true,
            animationDuration: 1500,
            animationEasing: 'elasticOut',
            animationDelay: function(idx) {
                return idx * 100;
            }
        }]
    };
    
    // 渲染图表
    chart.setOption(option);
    
    // 添加点击事件
    chart.on('click', function(params) {
        if (params.dataType === 'node') {
            console.log(`点击了节点: ${params.name}`);
        } else {
            console.log(`点击了链接: ${nodes[params.data.source].name} -> ${nodes[params.data.target].name}`);
        }
    });
}

// 添加汇总卡片
function addSummaryCards(summary) {
    // 检查是否已存在卡片容器，如果不存在则创建
    let summaryCardContainer = $('#sankey-summary-container');
    if (summaryCardContainer.length === 0) {
        // 在桑基图下方创建卡片容器
        $('#coupon-sankey-diagram').after('<div id="sankey-summary-container" class="mt-4"></div>');
        summaryCardContainer = $('#sankey-summary-container');
    } else {
        // 如果已存在则清空内容
        summaryCardContainer.empty();
    }
    
    // 创建来源分布饼图卡片
    const sourceCardHtml = `
        <div class="card mb-3 summary-card" style="border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid rgba(255,150,0,0.1); overflow: hidden;">
            <div class="card-header d-flex justify-content-between align-items-center" style="background: linear-gradient(135deg, rgba(125,85,25,0.1), rgba(255,165,45,0.05)); border-bottom: none;">
                <h5 class="card-title mb-0" style="font-size: 1rem; color: #e67e22;">
                    <i class="bi bi-diagram-3 me-2"></i>优惠券来源分布
                </h5>
                <span class="badge bg-warning" style="font-size: 0.8rem;">${summary.total_coupons}张</span>
            </div>
            <div class="card-body">
                <div id="source-pie-chart" style="height: 200px;"></div>
            </div>
        </div>
    `;
    
    // 创建状态分布饼图卡片
    const statusCardHtml = `
        <div class="card mb-3 summary-card" style="border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid rgba(255,150,0,0.1); overflow: hidden;">
            <div class="card-header d-flex justify-content-between align-items-center" style="background: linear-gradient(135deg, rgba(125,85,25,0.1), rgba(255,165,45,0.05)); border-bottom: none;">
                <h5 class="card-title mb-0" style="font-size: 1rem; color: #e67e22;">
                    <i class="bi bi-pie-chart-fill me-2"></i>优惠券状态分布
                </h5>
                <span class="badge bg-info" style="font-size: 0.8rem;">使用率${summary.usage_rate}%</span>
            </div>
            <div class="card-body">
                <div id="status-pie-chart" style="height: 200px;"></div>
            </div>
        </div>
    `;
    
    // 创建行布局包装两个饼图
    summaryCardContainer.html(`
        <div class="row">
            <div class="col-md-6">${sourceCardHtml}</div>
            <div class="col-md-6">${statusCardHtml}</div>
        </div>
    `);
    
    // 渲染来源分布饼图
    renderSourcePieChart(summary.source_data);
    
    // 渲染状态分布饼图
    renderStatusPieChart(summary.status_data);
    
    // 添加CSS动画
    if (!$('#sankey-summary-style').length) {
        $('head').append(`
            <style id="sankey-summary-style">
                .summary-card {
                    transition: all 0.3s ease;
                    animation: fadeInUp 0.5s ease backwards;
                }
                
                .summary-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 8px 20px rgba(0,0,0,0.1) !important;
                }
                
                @keyframes fadeInUp {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
            </style>
        `);
    }
}

// 渲染来源分布饼图
function renderSourcePieChart(sourceData) {
    // 检查数据
    if (!sourceData || sourceData.length === 0) {
        $('#source-pie-chart').html('<div class="text-center text-muted py-5">暂无来源数据</div>');
        return;
    }
    
    // 初始化饼图
    const sourcePieChart = echarts.init(document.getElementById('source-pie-chart'));
    
    // 定义颜色
    const colors = [
        '#59a6ff', '#50bfda', '#47d8b8', '#3ef097', '#52f078', '#93f267', '#d4f355', '#f5d042', '#f5a142', '#f56f42'
    ];
    
    // 配置选项
    const option = {
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)',
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            borderColor: 'rgba(255,200,100,0.3)',
            borderWidth: 1,
            textStyle: {
                color: '#666'
            },
            extraCssText: 'box-shadow: 0 4px 14px rgba(0,0,0,0.1); border-radius: 8px;'
        },
        legend: {
            orient: 'vertical',
            right: 0,
            top: 'center',
            itemWidth: 10,
            itemHeight: 10,
            icon: 'circle',
            formatter: function(name) {
                const item = sourceData.find(item => item.name === name);
                if (item) {
                    return name + ' ' + Math.round(item.value / sourceData.reduce((sum, i) => sum + i.value, 0) * 100) + '%';
                }
                return name;
            },
            textStyle: {
                fontSize: 10,
                color: '#666'
            }
        },
        series: [
            {
                name: '优惠券来源',
                type: 'pie',
                radius: ['35%', '70%'],
                center: ['30%', '50%'],
                avoidLabelOverlap: true,
                itemStyle: {
                    borderRadius: 10,
                    borderColor: 'rgba(255, 255, 255, 0.6)',
                    borderWidth: 2,
                    shadowColor: 'rgba(0, 0, 0, 0.2)',
                    shadowBlur: 10
                },
                label: {
                    show: false
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: 12,
                        fontWeight: 'bold'
                    },
                    itemStyle: {
                        shadowBlur: 20,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                },
                labelLine: {
                    show: false
                },
                data: sourceData.map((item, index) => ({
                    value: item.value,
                    name: item.name,
                    itemStyle: {
                        color: colors[index % colors.length]
                    }
                })),
                // 动画效果
                animationType: 'scale',
                animationEasing: 'elasticOut',
                animationDelay: function(idx) {
                    return idx * 100 + 300;
                }
            }
        ]
    };
    
    // 渲染图表
    sourcePieChart.setOption(option);
    
    // 监听窗口调整大小事件
    $(window).resize(function() {
        sourcePieChart.resize();
    });
}

// 渲染状态分布饼图
function renderStatusPieChart(statusData) {
    // 检查数据
    if (!statusData || statusData.length === 0) {
        $('#status-pie-chart').html('<div class="text-center text-muted py-5">暂无状态数据</div>');
        return;
    }
    
    // 初始化饼图
    const statusPieChart = echarts.init(document.getElementById('status-pie-chart'));
    
    // 定义颜色
    const statusColors = {
        '未使用': '#f0c419',
        '已使用': '#4cd964',
        '已过期': '#ff3b30'
    };
    
    // 计算总数
    const total = statusData.reduce((sum, item) => sum + item.value, 0);
    
    // 配置选项
    const option = {
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)',
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            borderColor: 'rgba(255,200,100,0.3)',
            borderWidth: 1,
            textStyle: {
                color: '#666'
            },
            extraCssText: 'box-shadow: 0 4px 14px rgba(0,0,0,0.1); border-radius: 8px;'
        },
        legend: {
            orient: 'vertical',
            right: 0,
            top: 'center',
            itemWidth: 10,
            itemHeight: 10,
            icon: 'circle',
            formatter: function(name) {
                const item = statusData.find(item => item.name === name);
                if (item) {
                    return name + ' ' + Math.round(item.value / total * 100) + '%';
                }
                return name;
            },
            textStyle: {
                fontSize: 10,
                color: '#666'
            }
        },
        series: [
            {
                name: '优惠券状态',
                type: 'pie',
                radius: ['35%', '70%'],
                center: ['30%', '50%'],
                avoidLabelOverlap: true,
                itemStyle: {
                    borderRadius: 10,
                    borderColor: 'rgba(255, 255, 255, 0.6)',
                    borderWidth: 2,
                    shadowColor: 'rgba(0, 0, 0, 0.2)',
                    shadowBlur: 10
                },
                label: {
                    show: false
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: 12,
                        fontWeight: 'bold'
                    },
                    itemStyle: {
                        shadowBlur: 20,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                },
                labelLine: {
                    show: false
                },
                data: statusData.map(item => ({
                    value: item.value,
                    name: item.name,
                    itemStyle: {
                        color: statusColors[item.name] || getRandomColor(item.name),
                        // 根据状态添加发光效果
                        shadowBlur: item.name === '已使用' ? 15 : 0,
                        shadowColor: item.name === '已使用' ? 'rgba(76, 217, 100, 0.5)' : 'rgba(0, 0, 0, 0)'
                    }
                })),
                // 动画效果
                animationType: 'scale',
                animationEasing: 'elasticOut',
                animationDelay: function(idx) {
                    return idx * 100 + 400;
                }
            }
        ]
    };
    
    // 渲染图表
    statusPieChart.setOption(option);
    
    // 监听窗口调整大小事件
    $(window).resize(function() {
        statusPieChart.resize();
    });
}

// 获取随机颜色
function getRandomColor(seed) {
    // 使用字符串生成一个确定性的颜色
    let hash = 0;
    for (let i = 0; i < seed.length; i++) {
        hash = seed.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    let color = '#';
    for (let i = 0; i < 3; i++) {
        const value = (hash >> (i * 8)) & 0xFF;
        // 确保颜色不会太暗
        const adjustedValue = Math.max(value, 100);
        color += ('00' + adjustedValue.toString(16)).substr(-2);
    }
    
    return color;
} 