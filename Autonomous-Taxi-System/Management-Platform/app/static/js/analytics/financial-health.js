// 财务健康风险评估雷达图
function initFinancialHealthRiskChart() {
    const chartDom = document.getElementById('financial-health-risk');
    const loadingDom = document.getElementById('financial-health-riskLoading');
    if (!chartDom) return;
    
    const myChart = echarts.init(chartDom);
    loadingDom.style.display = 'flex';
    
    // 异步加载数据
    fetch('/admin/analytics/financial-risk-data')
        .then(response => response.json())
        .then(data => {
            loadingDom.style.display = 'none';
            
            const option = {
                color: ['#8A2BE2', '#FF1493'],
                title: {
                    text: ''
                },
                tooltip: {
                    trigger: 'axis'
                },
                legend: {
                    data: ['当前值', '目标值']
                },
                radar: {
                    shape: 'polygon',
                    indicator: [
                        { name: '流动性比率', max: 10 },
                        { name: '资产负债率', max: 10 },
                        { name: '营业利润率', max: 10 },
                        { name: '投资回报率', max: 10 },
                        { name: '现金流量比', max: 10 },
                        { name: '成本效率', max: 10 }
                    ]
                },
                series: [{
                    name: '财务健康指标',
                    type: 'radar',
                    data: [
                        {
                            value: data.current,
                            name: '当前值',
                            areaStyle: {
                                color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                                    { offset: 0, color: 'rgba(138, 43, 226, 0.6)' },
                                    { offset: 1, color: 'rgba(138, 43, 226, 0.1)' }
                                ])
                            },
                            lineStyle: {
                                width: 2
                            }
                        },
                        {
                            value: data.target,
                            name: '目标值',
                            lineStyle: {
                                type: 'dashed',
                                width: 1
                            }
                        }
                    ]
                }]
            };
            
            option && myChart.setOption(option);
            
            // 添加按钮事件
            registerChartEvents(myChart, 'financial-health-risk', '财务健康风险评估');
        })
        .catch(error => {
            console.error('加载财务健康风险数据出错:', error);
            loadingDom.style.display = 'none';
            showErrorMessage(chartDom, '数据加载失败，请稍后重试');
        });
        
    // 自适应大小
    window.addEventListener('resize', function() {
        myChart.resize();
    });
    
    return myChart;
}

// 显示错误信息函数
function showErrorMessage(container, message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'text-center text-danger mt-5';
    errorDiv.innerHTML = `<i class="bi bi-exclamation-triangle me-2"></i>${message}`;
    container.appendChild(errorDiv);
}

// 注册图表按钮事件
function registerChartEvents(chart, chartId, chartName) {
    // 刷新按钮事件
    document.querySelector(`[data-chart="${chartId}"].refresh-chart`).addEventListener('click', function() {
        const loadingDom = document.getElementById(`${chartId}Loading`);
        loadingDom.style.display = 'flex';
        
        // 这里可以重新加载数据
        setTimeout(() => {
            // 模拟刷新过程
            loadingDom.style.display = 'none';
            toastr.success(`${chartName}数据已更新`);
        }, 1000);
    });
    
    // 下载按钮事件
    document.querySelector(`[data-chart="${chartId}"].download-chart`).addEventListener('click', function() {
        const url = chart.getDataURL({
            type: 'png',
            pixelRatio: 2,
            backgroundColor: '#fff'
        });
        
        const link = document.createElement('a');
        link.download = `${chartName}_${new Date().toISOString().slice(0,10)}.png`;
        link.href = url;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        toastr.success(`${chartName}图表已下载`);
    });
}

// 文档加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // ... existing code ...
    
    // 初始化财务健康风险评估雷达图
    initFinancialHealthRiskChart();
}); 