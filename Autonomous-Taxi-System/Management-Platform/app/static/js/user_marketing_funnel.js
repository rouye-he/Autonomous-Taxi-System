// 用户活跃度转化漏斗图
$(document).ready(function() {
    // 初始化漏斗图
    const funnelChart = echarts.init(document.getElementById('user-funnel-chart'));
    
    // 加载动画
    funnelChart.showLoading({
        text: '数据加载中...',
        color: '#46a6ff',
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
        url: '/admin/user_marketing/funnel_data',
        type: 'GET',
        data: {
            start_date: startDate,
            end_date: endDate,
            date_range: dateRange
        },
        success: function(response) {
            // 隐藏加载动画
            funnelChart.hideLoading();
            
            // 处理数据和渲染图表
            renderFunnelChart(funnelChart, response);
            
            // 添加转化率指标卡
            addConversionCards(response.conversion_rates);
        },
        error: function(xhr, status, error) {
            // 隐藏加载动画，显示错误信息
            funnelChart.hideLoading();
            console.error('获取漏斗图数据失败:', error);
            
            // 显示错误消息
            $('#user-funnel-chart').html(`
                <div class="text-center text-danger">
                    <i class="bi bi-exclamation-triangle-fill fs-1"></i>
                    <p>数据加载失败，请稍后再试</p>
                </div>
            `);
        }
    });
    
    // 窗口调整大小时，重新调整图表尺寸
    $(window).resize(function() {
        funnelChart.resize();
    });
});

// 渲染漏斗图
function renderFunnelChart(chart, data) {
    // 实际数据值
    const funnelData = data.data;
    
    // 计算数值最大值，用于后续定制化
    const maxValue = Math.max(...funnelData.map(item => item.value));
    
    // 检查是否有零值并调整为最小值
    funnelData.forEach(item => {
        if (item.value === 0) {
            item.value = maxValue * 0.01; // 设置为最大值的1%
            item.itemStyle.opacity = 0.3; // 降低透明度
            item.label = {
                formatter: `{b}: 0`,
                position: 'inside'
            };
        }
    });
    
    // 定义渐变效果
    const gradients = [
        new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            {offset: 0, color: 'rgba(55, 165, 255, 0.8)'},
            {offset: 1, color: 'rgba(80, 141, 255, 0.8)'}
        ]),
        new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            {offset: 0, color: 'rgba(73, 190, 241, 0.8)'},
            {offset: 1, color: 'rgba(73, 190, 241, 0.8)'}
        ]),
        new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            {offset: 0, color: 'rgba(91, 218, 227, 0.85)'},
            {offset: 1, color: 'rgba(91, 218, 227, 0.85)'}
        ]),
        new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            {offset: 0, color: 'rgba(109, 245, 213, 0.9)'},
            {offset: 1, color: 'rgba(109, 245, 213, 0.9)'}
        ]),
        new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            {offset: 0, color: 'rgba(127, 255, 199, 0.95)'},
            {offset: 1, color: 'rgba(127, 255, 199, 0.95)'}
        ]),
        new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            {offset: 0, color: 'rgba(130, 255, 158, 1)'},
            {offset: 1, color: 'rgba(130, 255, 158, 1)'}
        ])
    ];
    
    // 为每个数据项应用渐变
    funnelData.forEach((item, index) => {
        if (index < gradients.length) {
            item.itemStyle = {
                ...item.itemStyle,
                color: gradients[index],
                shadowColor: 'rgba(0, 0, 0, 0.3)',
                shadowBlur: 10
            };
        }
    });
    
    // 配置选项
    const option = {
        title: {
            text: `用户活跃度转化分析(${data.period})`,
            subtext: '数据来源: users, orders 表',
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
            formatter: function(params) {
                // 计算与上一层级的百分比
                let percent = '';
                const currentValue = params.value;
                const currentIndex = params.dataIndex;
                
                if (currentIndex > 0) {
                    const prevValue = funnelData[currentIndex - 1].value;
                    if (prevValue && prevValue > 0) {
                        const ratio = (currentValue / prevValue * 100).toFixed(1);
                        percent = `<br />环比转化率: <span style="color:#ff9f43">${ratio}%</span>`;
                    }
                }
                
                return `<div style="padding: 8px">
                    <div style="margin-bottom: 5px; font-weight: bold;">${params.name}</div>
                    <div>数量: <span style="color:#3498db; font-weight: bold">${params.value.toLocaleString()}</span></div>
                    <div>占总注册数: <span style="color:#2ecc71">${(params.value / funnelData[0].value * 100).toFixed(1)}%</span></div>
                    ${percent}
                </div>`;
            },
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            borderColor: 'rgba(100,100,255,0.3)',
            borderWidth: 1,
            textStyle: {
                color: '#666'
            },
            extraCssText: 'box-shadow: 0 4px 14px rgba(0,0,0,0.1); border-radius: 8px;'
        },
        legend: {
            data: funnelData.map(item => item.name),
            bottom: 0,
            icon: 'roundRect',
            itemWidth: 12,
            itemHeight: 12,
            textStyle: {
                color: '#666'
            },
            selectedMode: false
        },
        series: [
            {
                name: '用户转化漏斗',
                type: 'funnel',
                left: '10%',
                right: '10%',
                top: 60,
                bottom: 60,
                width: '80%',
                min: 0,
                max: maxValue,
                minSize: '0%',
                maxSize: '100%',
                sort: 'descending',
                gap: 4,
                
                label: {
                    show: true,
                    position: 'inside',
                    formatter: (params) => {
                        return `${params.name}:\n${params.value.toLocaleString()}`;
                    },
                    fontSize: 14,
                    fontWeight: 'bold',
                    color: '#fff',
                    textShadowColor: 'rgba(0,0,0,0.3)',
                    textShadowBlur: 3,
                    textBorderWidth: 0
                },
                
                labelLine: {
                    length: 10,
                    lineStyle: {
                        width: 1,
                        type: 'solid'
                    }
                },
                
                emphasis: {
                    label: {
                        fontSize: 16,
                        fontWeight: 'bold',
                        textShadowBlur: 5
                    },
                    itemStyle: {
                        shadowBlur: 20,
                        shadowColor: 'rgba(0,0,0,0.5)'
                    }
                },
                
                data: funnelData,
                
                // 动画效果
                animationType: 'scale',
                animationEasing: 'elasticOut',
                animationDelay: function (idx) {
                    return Math.random() * 200 + 300 * idx;
                }
            }
        ]
    };
    
    // 渲染图表
    chart.setOption(option);
    
    // 添加点击事件
    chart.on('click', function(params) {
        const idx = params.dataIndex;
        // 根据点击的不同级别，可以添加不同的操作
        const levelNames = [
            '所有注册用户',
            '活跃用户分析',
            '订单用户分析',
            '近期订单用户',
            '重复购买用户',
            '新用户首单'
        ];
        
        if (idx < levelNames.length) {
            // 这里可以根据实际需求跳转到对应的分析页面
            console.log(`点击了${levelNames[idx]}层级`);
        }
    });
}

// 添加转化率卡片
function addConversionCards(conversionRates) {
    // 检查是否已存在卡片容器，如果不存在则创建
    let conversionCardContainer = $('#conversion-card-container');
    if (conversionCardContainer.length === 0) {
        // 在漏斗图下方创建卡片容器
        $('#user-funnel-chart').after('<div id="conversion-card-container" class="d-flex justify-content-between mt-3 flex-wrap"></div>');
        conversionCardContainer = $('#conversion-card-container');
    } else {
        // 如果已存在则清空内容
        conversionCardContainer.empty();
    }
    
    // 定义卡片数据
    const cards = [
        {
            label: '活跃率',
            value: conversionRates.active_rate,
            icon: 'bi-person-check',
            color: 'linear-gradient(135deg, #3498db, #5dade2)',
            description: '注册用户中的活跃用户比例'
        },
        {
            label: '下单转化率',
            value: conversionRates.order_rate,
            icon: 'bi-cart-check',
            color: 'linear-gradient(135deg, #2ecc71, #58d68d)',
            description: '活跃用户中的下单用户比例'
        },
        {
            label: '近期订单率',
            value: conversionRates.recent_order_rate,
            icon: 'bi-calendar-check',
            color: 'linear-gradient(135deg, #f39c12, #f5b041)',
            description: '所有下单用户中的近期下单用户比例'
        },
        {
            label: '重复购买率',
            value: conversionRates.repeat_rate,
            icon: 'bi-arrow-repeat',
            color: 'linear-gradient(135deg, #e74c3c, #ec7063)',
            description: '近期下单用户中的重复购买用户比例'
        },
        {
            label: '新用户转化率',
            value: conversionRates.new_conversion_rate,
            icon: 'bi-person-plus',
            color: 'linear-gradient(135deg, #9b59b6, #af7ac5)',
            description: '新注册用户中完成首单的比例'
        }
    ];
    
    // 创建卡片
    cards.forEach(card => {
        const cardHtml = `
            <div class="conversion-card p-2" style="flex: 1; min-width: 150px; margin: 5px; border-radius: 10px; box-shadow: 0 3px 10px rgba(0,0,0,0.1); overflow: hidden; position: relative;">
                <div class="card-content p-2" style="position: relative; z-index: 2;">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <div class="icon-container" style="width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: ${card.color}; box-shadow: 0 3px 8px rgba(0,0,0,0.2);">
                            <i class="bi ${card.icon} text-white"></i>
                        </div>
                        <h3 class="value mb-0" style="font-size: 1.6rem; font-weight: bold; color: #333;">${card.value}%</h3>
                    </div>
                    <div class="card-details">
                        <h5 class="card-title mb-1" style="font-size: 0.9rem; color: #666;">${card.label}</h5>
                        <p class="card-description mb-0" style="font-size: 0.75rem; color: #999; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${card.description}">${card.description}</p>
                    </div>
                </div>
                <div class="card-bg" style="position: absolute; top: 0; right: 0; bottom: 0; left: 0; background: ${card.color}; opacity: 0.05; z-index: 1;"></div>
            </div>
        `;
        
        conversionCardContainer.append(cardHtml);
    });
    
    // 添加卡片动画效果
    $('.conversion-card').each(function(index) {
        $(this).css('animation', `fadeIn 0.5s ease ${index * 0.1}s both`);
    });
    
    // 如果需要，添加CSS动画
    if (!$('#conversion-card-style').length) {
        $('head').append(`
            <style id="conversion-card-style">
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                
                .conversion-card {
                    transition: all 0.3s ease;
                }
                
                .conversion-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 5px 15px rgba(0,0,0,0.15);
                }
            </style>
        `);
    }
} 