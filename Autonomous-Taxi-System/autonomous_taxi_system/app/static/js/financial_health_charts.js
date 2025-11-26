/**
 * 财务健康页面图表JS文件 - 实现财务健康页面的可视化图表
 */

document.addEventListener('DOMContentLoaded', function() {
    // 一旦DOM加载完成，初始化所有图表
    initFinanceBalanceGauge();
    initCostStructureSankey();
    initFinancialMetricsForecast();
    initCityFinancialRadar();
    initCreditIncomeChart();
    initVehicleRoiBoxplot();
    initCouponPackageSunburst();
    
    // 稍后可以添加其他图表初始化
});

/**
 * 初始化实时收支动态平衡仪表盘
 */
function initFinanceBalanceGauge() {
    // 获取当前URL中的日期参数
    const urlParams = new URLSearchParams(window.location.search);
    let startDate = urlParams.get('start_date') || '';
    let endDate = urlParams.get('end_date') || '';
    
    // 构建API请求URL，包含日期参数
    let apiUrl = '/analytics/api/finance_balance_data';
    if (startDate && endDate) {
        apiUrl += `?start_date=${startDate}&end_date=${endDate}`;
    }
    
    // 从后端获取收入支出数据
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            const chartDom = document.getElementById('finance-balance-gauge');
            if (!chartDom) return;
            
            const myChart = echarts.init(chartDom);
            const option = createFinanceBalanceGaugeOption(data);
            myChart.setOption(option);
            
            // 响应窗口调整大小
            window.addEventListener('resize', function() {
                myChart.resize();
            });
        })
        .catch(error => {
            console.error('获取收支平衡数据失败:', error);
            // 使用模拟数据进行展示
            const chartDom = document.getElementById('finance-balance-gauge');
            if (!chartDom) return;
            
            const myChart = echarts.init(chartDom);
            const mockData = {
                totalIncome: 1250000,
                totalExpense: 980000,
                balance: 270000,
                profitMargin: 21.6,
                incomeBreakdown: {
                    '车费收入': 1150000,
                    '充值卡收入': 50000,
                    '会员费': 30000,
                    '其他收入': 20000
                },
                expenseBreakdown: {
                    '车辆支出': 450000,
                    '充电站支出': 320000,
                    '其他支出': 210000
                }
            };
            
            const option = createFinanceBalanceGaugeOption(mockData);
            myChart.setOption(option);
            
            // 响应窗口调整大小
            window.addEventListener('resize', function() {
                myChart.resize();
            });
        });
}

/**
 * 创建收支动态平衡仪表盘的配置选项
 */
function createFinanceBalanceGaugeOption(data) {
    // 计算数值显示格式
    const formatNumber = num => {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(2) + '百万';
        } else if (num >= 10000) {
            return (num / 10000).toFixed(2) + '万';
        } else {
            return num.toFixed(2);
        }
    };
    
    // 提取和计算所需数据
    const totalIncome = data.totalIncome;
    const totalExpense = data.totalExpense;
    const balance = data.balance;
    const profitMargin = data.profitMargin;
    
    // 收入明细数据
    const incomeData = [];
    for (const [key, value] of Object.entries(data.incomeBreakdown)) {
        incomeData.push({
            name: key,
            value: value
        });
    }
    
    // 支出明细数据
    const expenseData = [];
    for (const [key, value] of Object.entries(data.expenseBreakdown)) {
        expenseData.push({
            name: key,
            value: value
        });
    }
    
    // 设置仪表盘最大值为总收入和支出的较大者的1.2倍
    const maxValue = Math.max(totalIncome, totalExpense) * 1.2;
    
    return {
        title: {
            text: '实时收支动态平衡状态',
            left: 'center',
            top: 10,
            textStyle: {
                fontSize: 18,
                color: '#333'
            }
        },
        tooltip: {
            formatter: '{a} <br/>{b} : {c}元'
        },
        grid: {
            top: 100,
            bottom: 150
        },
        series: [
            {
                name: '实时收支平衡',
                type: 'gauge',
                radius: '75%',
                center: ['50%', '60%'],
                min: 0,
                max: maxValue,
                splitNumber: 10,
                axisLine: {
                    lineStyle: {
                        width: 30,
                        color: [
                            [0.5, '#ff6e76'],  // 支出区域：红色
                            [0.8, '#fddd60'],  // 收支平衡区域：黄色
                            [1, '#7cffb2']     // 盈利区域：绿色
                        ]
                    }
                },
                pointer: {
                    itemStyle: {
                        color: 'auto'
                    }
                },
                axisTick: {
                    distance: -30,
                    length: 8,
                    lineStyle: {
                        color: '#fff',
                        width: 2
                    }
                },
                splitLine: {
                    distance: -30,
                    length: 30,
                    lineStyle: {
                        color: '#fff',
                        width: 4
                    }
                },
                axisLabel: {
                    color: 'auto',
                    distance: 40,
                    fontSize: 12,
                    formatter: function(value) {
                        return formatNumber(value) + '元';
                    }
                },
                detail: {
                    valueAnimation: true,
                    formatter: function(value) {
                        return '总收入: ' + formatNumber(totalIncome) + '元' + 
                               '\n总支出: ' + formatNumber(totalExpense) + '元' + 
                               '\n净利润: ' + formatNumber(balance) + '元' + 
                               '\n利润率: ' + profitMargin.toFixed(1) + '%';
                    },
                    color: 'auto',
                    fontSize: 16,
                    offsetCenter: [0, '70%'],
                    rich: {
                        valueStyle: {
                            fontSize: 36,
                            lineHeight: 40
                        }
                    }
                },
                data: [
                    {
                        value: totalIncome,
                        name: '总收入'
                    }
                ]
            },
            // 小图表：收入构成
            {
                name: '收入构成',
                type: 'pie',
                radius: ['15%', '25%'],
                center: ['25%', '25%'],
                itemStyle: {
                    borderRadius: 5
                },
                label: {
                    show: false
                },
                emphasis: {
                    label: {
                        show: true,
                        formatter: '{b}: {c}元 ({d}%)',
                        position: 'outside'
                    }
                },
                data: incomeData
            },
            // 小图表：支出构成
            {
                name: '支出构成',
                type: 'pie',
                radius: ['15%', '25%'],
                center: ['75%', '25%'],
                itemStyle: {
                    borderRadius: 5
                },
                label: {
                    show: false
                },
                emphasis: {
                    label: {
                        show: true,
                        formatter: '{b}: {c}元 ({d}%)',
                        position: 'outside'
                    }
                },
                data: expenseData
            }
        ]
    };
}

/**
 * 初始化成本结构桑基图
 */
function initCostStructureSankey() {
    // 获取当前URL中的日期参数
    const urlParams = new URLSearchParams(window.location.search);
    let startDate = urlParams.get('start_date') || '';
    let endDate = urlParams.get('end_date') || '';
    
    // 构建API请求URL，包含日期参数
    let apiUrl = '/analytics/api/cost_structure_data';
    if (startDate && endDate) {
        apiUrl += `?start_date=${startDate}&end_date=${endDate}`;
    }
    
    // 从后端获取成本结构数据
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            const chartDom = document.getElementById('cost-structure-sankey');
            if (!chartDom) return;
            
            const myChart = echarts.init(chartDom);
            const option = createCostStructureSankeyOption(data);
            myChart.setOption(option);
            
            // 响应窗口调整大小
            window.addEventListener('resize', function() {
                myChart.resize();
            });
        })
        .catch(error => {
            console.error('获取成本结构数据失败:', error);
            // 如果数据获取失败，可以使用模拟数据展示
            // 此处省略模拟数据展示代码
        });
}

/**
 * 创建成本结构桑基图的配置选项
 */
function createCostStructureSankeyOption(data) {
    return {
        title: {
            text: '成本结构分析',
            left: 'center',
            top: 10
        },
        tooltip: {
            trigger: 'item',
            triggerOn: 'mousemove',
            formatter: function(params) {
                let value = params.value;
                // 将数值格式化为更易读的形式
                if (value >= 1000000) {
                    value = (value / 1000000).toFixed(2) + '百万元';
                } else if (value >= 10000) {
                    value = (value / 10000).toFixed(2) + '万元';
                } else {
                    value = value.toFixed(2) + '元';
                }
                
                // 为不同级别的节点显示不同的提示格式
                let result = '';
                if (params.dataType === 'edge') {
                    result = params.data.source + ' → ' + params.data.target + ': ' + value;
                } else {
                    result = params.name + ': ' + value;
                }
                return result;
            }
        },
        series: [
            {
                type: 'sankey',
                layout: 'none',
                emphasis: {
                    focus: 'adjacency'
                },
                data: data.nodes,
                links: data.links,
                lineStyle: {
                    color: 'gradient',
                    curveness: 0.5
                },
                itemStyle: {
                    borderWidth: 1,
                    borderColor: '#aaa'
                },
                label: {
                    fontSize: 12,
                    position: 'right'
                },
                levels: [
                    {
                        depth: 0,
                        itemStyle: {
                            color: '#e06343'
                        },
                        lineStyle: {
                            color: 'source',
                            opacity: 0.6
                        }
                    },
                    {
                        depth: 1,
                        itemStyle: {
                            color: function(params) {
                                // 使用不同颜色区分不同类型的支出
                                if (params.name === '车辆支出') {
                                    return '#5470c6';
                                } else if (params.name === '充电站支出') {
                                    return '#91cc75';
                                } else {
                                    return '#fac858';
                                }
                            }
                        },
                        lineStyle: {
                            color: 'source',
                            opacity: 0.6
                        }
                    },
                    {
                        depth: 2,
                        itemStyle: {
                            color: function(params) {
                                // 根据父节点类型决定颜色
                                if (params.name.includes('车辆')) {
                                    return '#5470c6';
                                } else if (params.name.includes('充电')) {
                                    return '#91cc75';
                                } else {
                                    return '#fac858';
                                }
                            }
                        }
                    }
                ]
            }
        ]
    };
}

/**
 * 初始化关键财务指标预测趋势图
 */
function initFinancialMetricsForecast() {
    // 获取当前URL中的日期参数
    const urlParams = new URLSearchParams(window.location.search);
    let startDate = urlParams.get('start_date') || '';
    let endDate = urlParams.get('end_date') || '';
    
    // 构建API请求URL，包含日期参数
    let apiUrl = '/analytics/api/financial_metrics_forecast';
    if (startDate && endDate) {
        apiUrl += `?start_date=${startDate}&end_date=${endDate}`;
    }
    
    // 从后端获取财务指标预测数据
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('获取财务指标预测数据失败，HTTP状态: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            const chartDom = document.getElementById('financial-metrics-forecast');
            if (!chartDom) return;
            
            const myChart = echarts.init(chartDom);
            const option = createFinancialMetricsForecastOption(data);
            myChart.setOption(option);
            
            // 响应窗口调整大小
            window.addEventListener('resize', function() {
                myChart.resize();
            });
        })
        .catch(error => {
            console.error('获取财务指标预测数据失败:', error);
            // 显示错误信息在图表容器中
            const chartDom = document.getElementById('financial-metrics-forecast');
            if (chartDom) {
                chartDom.innerHTML = `
                    <div style="height:100%;display:flex;align-items:center;justify-content:center;flex-direction:column;color:#f56c6c;">
                        <i class="bi bi-exclamation-triangle" style="font-size:3rem;margin-bottom:1rem;"></i>
                        <p>数据加载失败</p>
                        <p style="font-size:0.9rem;color:#999;">${error.message}</p>
                    </div>
                `;
            }
        });
}

/**
 * 创建关键财务指标预测趋势图的配置选项
 */
function createFinancialMetricsForecastOption(data) {
    // 格式化日期数据，确保X轴显示正确
    const formatDate = date => {
        const d = new Date(date);
        return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`;
    };
    
    return {
        title: {
            text: '关键财务指标预测趋势',
            left: 'center',
            top: 10
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross',
                label: {
                    backgroundColor: '#6a7985'
                }
            },
            formatter: function(params) {
                let res = params[0].axisValue + '<br/>';
                
                params.forEach((param) => {
                    const value = param.value;
                    const formattedValue = value >= 10000 
                        ? (value / 10000).toFixed(2) + '万元' 
                        : value.toFixed(2) + '元';
                    
                    res += `<span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${param.color};"></span>`;
                    res += `${param.seriesName}: ${formattedValue}<br/>`;
                });
                
                return res;
            }
        },
        legend: {
            data: ['总收入', '总支出', '净利润', '收入预测', '支出预测', '利润预测'],
            top: 40
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            top: '25%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: data.dates.map(formatDate),
            axisLabel: {
                rotate: 45,
                formatter: function(value) {
                    return value.substring(5); // 只显示月-日
                }
            }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                formatter: function(value) {
                    return value >= 10000 
                        ? (value / 10000).toFixed(1) + '万' 
                        : value;
                }
            }
        },
        series: [
            {
                name: '总收入',
                type: 'line',
                stack: 'Total',
                emphasis: {
                    focus: 'series'
                },
                showSymbol: false,
                lineStyle: {
                    width: 3,
                    color: '#5470c6'
                },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0,
                        y: 0,
                        x2: 0,
                        y2: 1,
                        colorStops: [{
                            offset: 0,
                            color: 'rgba(84, 112, 198, 0.5)' 
                        }, {
                            offset: 1,
                            color: 'rgba(84, 112, 198, 0.1)'
                        }]
                    }
                },
                data: data.incomeData
            },
            {
                name: '总支出',
                type: 'line',
                stack: 'Total',
                emphasis: {
                    focus: 'series'
                },
                showSymbol: false,
                lineStyle: {
                    width: 3,
                    color: '#ee6666'
                },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0,
                        y: 0,
                        x2: 0,
                        y2: 1,
                        colorStops: [{
                            offset: 0,
                            color: 'rgba(238, 102, 102, 0.5)'
                        }, {
                            offset: 1,
                            color: 'rgba(238, 102, 102, 0.1)'
                        }]
                    }
                },
                data: data.expenseData
            },
            {
                name: '净利润',
                type: 'line',
                stack: 'Total',
                emphasis: {
                    focus: 'series'
                },
                showSymbol: false,
                lineStyle: {
                    width: 3,
                    color: '#91cc75'
                },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0,
                        y: 0,
                        x2: 0,
                        y2: 1,
                        colorStops: [{
                            offset: 0,
                            color: 'rgba(145, 204, 117, 0.5)'
                        }, {
                            offset: 1,
                            color: 'rgba(145, 204, 117, 0.1)'
                        }]
                    }
                },
                data: data.profitData
            },
            {
                name: '收入预测',
                type: 'line',
                emphasis: {
                    focus: 'series'
                },
                showSymbol: false,
                lineStyle: {
                    width: 2,
                    type: 'dashed',
                    color: '#5470c6'
                },
                data: data.incomeDataForecast
            },
            {
                name: '支出预测',
                type: 'line',
                emphasis: {
                    focus: 'series'
                },
                showSymbol: false,
                lineStyle: {
                    width: 2,
                    type: 'dashed',
                    color: '#ee6666'
                },
                data: data.expenseDataForecast
            },
            {
                name: '利润预测',
                type: 'line',
                emphasis: {
                    focus: 'series'
                },
                showSymbol: false,
                lineStyle: {
                    width: 2,
                    type: 'dashed',
                    color: '#91cc75'
                },
                data: data.profitDataForecast
            }
        ]
    };
}

/**
 * 初始化城市收入雷达图
 */
function initCityFinancialRadar() {
    // 获取当前URL中的日期参数
    const urlParams = new URLSearchParams(window.location.search);
    let startDate = urlParams.get('start_date') || '';
    let endDate = urlParams.get('end_date') || '';
    
    // 构建API请求URL，包含日期参数
    let apiUrl = '/analytics/api/city_financial_data';
    if (startDate && endDate) {
        apiUrl += `?start_date=${startDate}&end_date=${endDate}`;
    }
    
    // 从后端获取城市财务数据
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('获取城市财务数据失败，HTTP状态: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            const chartDom = document.getElementById('city-financial-radar');
            if (!chartDom) return;
            
            const myChart = echarts.init(chartDom);
            const option = createCityFinancialRadarOption(data);
            myChart.setOption(option);
            
            // 响应窗口调整大小
            window.addEventListener('resize', function() {
                myChart.resize();
            });
        })
        .catch(error => {
            console.error('获取城市财务数据失败:', error);
            // 显示错误信息在图表容器中
            const chartDom = document.getElementById('city-financial-radar');
            if (chartDom) {
                chartDom.innerHTML = `
                    <div style="height:100%;display:flex;align-items:center;justify-content:center;flex-direction:column;color:#f56c6c;">
                        <i class="bi bi-exclamation-triangle" style="font-size:3rem;margin-bottom:1rem;"></i>
                        <p>数据加载失败</p>
                        <p style="font-size:0.9rem;color:#999;">${error.message}</p>
                    </div>
                `;
            }
        });
}

/**
 * 创建城市收入雷达图的配置选项
 */
function createCityFinancialRadarOption(data) {
    // 处理指标数据
    const indicators = data.indicators;
    const seriesData = data.cities;

    // 雷达图配置
    return {
        title: {
            text: '城市财务表现对比',
            left: 'center',
            top: 10
        },
        tooltip: {
            trigger: 'item'
        },
        legend: {
            type: 'scroll',
            bottom: 10,
            data: seriesData.map(item => item.name)
        },
        radar: {
            // 雷达图的指示器，用来指定雷达图中的多个变量
            indicator: indicators,
            // 雷达图的中心（圆心）坐标，数组的第一项是横坐标，第二项是纵坐标
            center: ['50%', '55%'],
            // 雷达图的半径，数组的第一项是内半径，第二项是外半径
            radius: '65%',
            // 指示器轴的分割段数
            splitNumber: 5,
            // 坐标轴线的样式
            axisLine: {
                lineStyle: {
                    color: 'rgba(0, 0, 0, 0.2)'
                }
            },
            // 分割线的样式
            splitLine: {
                lineStyle: {
                    color: 'rgba(0, 0, 0, 0.2)'
                }
            },
            // 分割区域的样式
            splitArea: {
                show: true,
                areaStyle: {
                    color: ['rgba(250,250,250,0.3)', 'rgba(200,200,200,0.2)']
                }
            },
            // 坐标轴的名字
            name: {
                textStyle: {
                    color: '#333',
                    fontSize: 12
                }
            }
        },
        series: [
            {
                type: 'radar',
                data: seriesData,
                areaStyle: {
                    opacity: 0.3
                },
                lineStyle: {
                    width: 2
                }
            }
        ]
    };
}

/**
 * 初始化用户信用分vs.人均贡献收入气泡图
 */
function initCreditIncomeChart() {
    // 从后端获取用户信用-收入数据
    fetch('/analytics/api/credit_income_data')
        .then(response => {
            if (!response.ok) {
                throw new Error('获取用户信用-收入数据失败，HTTP状态: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            const chartDom = document.getElementById('credit-income-bubble');
            if (!chartDom) return;
            
            const myChart = echarts.init(chartDom);
            const option = createCreditIncomeBubbleOption(data);
            myChart.setOption(option);
            
            // 响应窗口调整大小
            window.addEventListener('resize', function() {
                myChart.resize();
            });
        })
        .catch(error => {
            console.error('获取用户信用-收入数据失败:', error);
            // 显示错误信息在图表容器中
            const chartDom = document.getElementById('credit-income-bubble');
            if (chartDom) {
                chartDom.innerHTML = `
                    <div style="height:100%;display:flex;align-items:center;justify-content:center;flex-direction:column;color:#f56c6c;">
                        <i class="bi bi-exclamation-triangle" style="font-size:3rem;margin-bottom:1rem;"></i>
                        <p>数据加载失败</p>
                        <p style="font-size:0.9rem;color:#999;">${error.message}</p>
                    </div>
                `;
            }
        });
}

/**
 * 创建用户信用分vs.人均贡献收入气泡图的配置选项
 */
function createCreditIncomeBubbleOption(data) {
    return {
        title: {
            text: '用户信用分与人均贡献收入关系',
            left: 'center',
            top: 10
        },
        tooltip: {
            trigger: 'item',
            formatter: function (params) {
                return `信用分: ${params.value[0]}<br />人均收入: ${params.value[1].toFixed(2)}元<br />用户数量: ${params.value[2]}`;
            }
        },
        grid: {
            left: '10%',
            right: '10%',
            top: '15%',
            bottom: '10%'
        },
        xAxis: {
            type: 'value',
            name: '用户信用分',
            nameLocation: 'middle',
            nameGap: 30,
            nameTextStyle: {
                fontSize: 14
            },
            min: 0,
            max: 100,
            splitLine: {
                show: true,
                lineStyle: {
                    type: 'dashed'
                }
            }
        },
        yAxis: {
            type: 'value',
            name: '人均贡献收入(元)',
            nameLocation: 'middle',
            nameGap: 30,
            nameTextStyle: {
                fontSize: 14
            },
            splitLine: {
                show: true,
                lineStyle: {
                    type: 'dashed'
                }
            },
            axisLabel: {
                formatter: function(value) {
                    return value.toFixed(0);
                }
            }
        },
        visualMap: [
            {
                show: false,
                dimension: 0, // 第一个维度（X轴：信用分）映射到颜色
                min: 0,
                max: 100,
                inRange: {
                    color: ['#51689b', '#ce5c5c', '#fac858', '#ee6666', '#91cc75', '#5470c6']
                }
            },
            {
                show: false,
                dimension: 2, // 第三个维度（用户数量）映射到大小
                min: 1,
                max: data.maxUserCount,
                inRange: {
                    symbolSize: [10, 50]
                }
            }
        ],
        series: [
            {
                name: '用户信用分vs收入',
                type: 'scatter',
                data: data.bubbleData,
                emphasis: {
                    focus: 'self',
                    label: {
                        show: true,
                        formatter: function (param) {
                            return param.value[0];
                        },
                        position: 'top'
                    }
                },
                itemStyle: {
                    opacity: 0.8,
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowOffsetY: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        ]
    };
}

/**
 * 初始化车辆资产回报箱线图
 */
function initVehicleRoiBoxplot() {
    // 获取当前URL中的日期参数
    const urlParams = new URLSearchParams(window.location.search);
    let startDate = urlParams.get('start_date') || '';
    let endDate = urlParams.get('end_date') || '';
    
    // 构建API请求URL，包含日期参数
    let apiUrl = '/analytics/api/vehicle_roi_data';
    if (startDate && endDate) {
        apiUrl += `?start_date=${startDate}&end_date=${endDate}`;
    }
    
    // 从后端获取车辆资产回报数据
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('获取车辆资产回报数据失败，HTTP状态: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            const chartDom = document.getElementById('vehicle-roi-boxplot');
            if (!chartDom) return;
            
            const myChart = echarts.init(chartDom);
            const option = createVehicleRoiBoxplotOption(data);
            myChart.setOption(option);
            
            // 响应窗口调整大小
            window.addEventListener('resize', function() {
                myChart.resize();
            });
        })
        .catch(error => {
            console.error('获取车辆资产回报数据失败:', error);
            // 显示错误信息在图表容器中
            const chartDom = document.getElementById('vehicle-roi-boxplot');
            if (chartDom) {
                chartDom.innerHTML = `
                    <div style="height:100%;display:flex;align-items:center;justify-content:center;flex-direction:column;color:#f56c6c;">
                        <i class="bi bi-exclamation-triangle" style="font-size:3rem;margin-bottom:1rem;"></i>
                        <p>数据加载失败</p>
                        <p style="font-size:0.9rem;color:#999;">${error.message}</p>
                    </div>
                `;
            }
        });
}

/**
 * 创建车辆资产回报箱线图的配置选项
 */
function createVehicleRoiBoxplotOption(data) {
    if (!data || data.length === 0) {
        return {
            title: {
                text: '车辆资产回报箱线图 - 暂无数据',
                left: 'center'
            }
        };
    }
    
    // 提取数据
    const models = data.map(item => item.model);
    const boxData = data.map(item => item.boxplot);
    const avgPrices = data.map(item => item.avgPurchasePrice);
    const vehicleCounts = data.map(item => item.vehicleCount);
    
    return {
        title: {
            text: '车辆资产回报分析',
            left: 'center',
            top: 10
        },
        tooltip: {
            trigger: 'item',
            axisPointer: {
                type: 'shadow'
            },
            formatter: function(params) {
                if (params.seriesType === 'boxplot') {
                    // 箱线图数据提示
                    const dataIndex = params.dataIndex;
                    const model = models[dataIndex];
                    const vehicleCount = vehicleCounts[dataIndex];
                    const avgPrice = avgPrices[dataIndex].toLocaleString('zh-CN', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });
                    const boxValues = params.data.slice(1, 6); // 提取boxplot数据
                    
                    return `
                        <div style="font-weight:bold;margin-bottom:10px;">${model}</div>
                        <div>车辆数量: ${vehicleCount}辆</div>
                        <div>平均购置成本: ${avgPrice}元</div>
                        <div style="margin-top:8px;font-weight:bold;">回报率(每日):</div>
                        <div>最小值: ${boxValues[0].toFixed(4)}%</div>
                        <div>下四分位: ${boxValues[1].toFixed(4)}%</div>
                        <div>中位数: ${boxValues[2].toFixed(4)}%</div>
                        <div>上四分位: ${boxValues[3].toFixed(4)}%</div>
                        <div>最大值: ${boxValues[4].toFixed(4)}%</div>
                    `;
                } else {
                    // 平均购置成本数据提示
                    return `${params.name}<br/>平均购置成本: ${params.value.toLocaleString('zh-CN', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })}元`;
                }
            }
        },
        legend: {
            data: ['日均回报率', '平均购置成本'],
            top: 40
        },
        grid: {
            left: '3%',
            right: '3%',
            bottom: '15%',
            top: '25%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: models,
            boundaryGap: true,
            nameGap: 30,
            axisLabel: {
                rotate: 45
            },
            splitArea: {
                show: false
            }
        },
        yAxis: [
            {
                type: 'value',
                name: '日均回报率(%)',
                splitArea: {
                    show: true
                },
                axisLabel: {
                    formatter: function(value) {
                        return value.toFixed(3) + '%';
                    }
                }
            },
            {
                type: 'value',
                name: '平均购置成本(元)',
                splitLine: {
                    show: false
                },
                axisLabel: {
                    formatter: function(value) {
                        return (value / 10000).toFixed(0) + '万';
                    }
                }
            }
        ],
        series: [
            {
                name: '日均回报率',
                type: 'boxplot',
                data: boxData.map(item => {
                    return {
                        value: [0, ...item], // 添加一个虚拟最小值0，以便ECharts箱线图正确显示
                        itemStyle: {
                            borderColor: '#5470c6',
                            borderWidth: 2
                        }
                    };
                }),
                tooltip: {
                    formatter: function(param) {
                        return [
                            param.name + ': ',
                            '上限: ' + param.data[5].toFixed(4) + '%',
                            'Q3: ' + param.data[4].toFixed(4) + '%',
                            '中位数: ' + param.data[3].toFixed(4) + '%',
                            'Q1: ' + param.data[2].toFixed(4) + '%',
                            '下限: ' + param.data[1].toFixed(4) + '%'
                        ].join('<br/>');
                    }
                }
            },
            {
                name: '平均购置成本',
                type: 'bar',
                yAxisIndex: 1,
                data: avgPrices,
                itemStyle: {
                    color: '#91cc75',
                    opacity: 0.7
                },
                barWidth: '40%',
                barGap: '30%',
                z: -1
            }
        ]
    };
}

/**
 * 初始化优惠券套餐销售贡献旭日图
 */
function initCouponPackageSunburst() {
    // 获取当前URL中的日期参数
    const urlParams = new URLSearchParams(window.location.search);
    let startDate = urlParams.get('start_date') || '';
    let endDate = urlParams.get('end_date') || '';
    
    // 构建API请求URL，包含日期参数
    let apiUrl = '/analytics/api/coupon_package_data';
    if (startDate && endDate) {
        apiUrl += `?start_date=${startDate}&end_date=${endDate}`;
    }
    
    // 从后端获取优惠券套餐销售贡献数据
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('获取优惠券套餐销售贡献数据失败，HTTP状态: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            const chartDom = document.getElementById('coupon-package-sunburst');
            if (!chartDom) return;
            
            const myChart = echarts.init(chartDom);
            const option = createCouponPackageSunburstOption(data);
            myChart.setOption(option);
            
            // 响应窗口调整大小
            window.addEventListener('resize', function() {
                myChart.resize();
            });
        })
        .catch(error => {
            console.error('获取优惠券套餐销售贡献数据失败:', error);
            // 显示错误信息在图表容器中
            const chartDom = document.getElementById('coupon-package-sunburst');
            if (chartDom) {
                chartDom.innerHTML = `
                    <div style="height:100%;display:flex;align-items:center;justify-content:center;flex-direction:column;color:#f56c6c;">
                        <i class="bi bi-exclamation-triangle" style="font-size:3rem;margin-bottom:1rem;"></i>
                        <p>数据加载失败</p>
                        <p style="font-size:0.9rem;color:#999;">${error.message}</p>
                    </div>
                `;
            }
        });
}

/**
 * 创建优惠券套餐销售贡献旭日图的配置选项
 */
function createCouponPackageSunburstOption(data) {
    if (!data || data.length === 0) {
        return {
            title: {
                text: '优惠券套餐销售贡献旭日图 - 暂无数据',
                left: 'center'
            }
        };
    }
    
    return {
        title: {
            text: '优惠券套餐销售贡献分析',
            left: 'center',
            top: 10
        },
        tooltip: {
            trigger: 'item',
            formatter: function(params) {
                const value = params.value;
                let valueText;
                
                if (value >= 10000) {
                    valueText = (value / 10000).toFixed(2) + '万元';
                } else {
                    valueText = value.toFixed(2) + '元';
                }
                
                // 计算所占百分比，相对于父节点的比例
                let percentage = '';
                if (params.name !== '优惠券套餐总销售') {
                    if (params.treePathInfo.length > 1) {
                        const parentValue = params.treePathInfo[params.treePathInfo.length - 2].value;
                        if (parentValue > 0) {
                            percentage = '(' + (value / parentValue * 100).toFixed(1) + '%)';
                        }
                    }
                }
                
                return `${params.name}<br/>销售价值: ${valueText} ${percentage}`;
            }
        },
        series: [
            {
                type: 'sunburst',
                data: data,
                radius: ['20%', '90%'],
                center: ['50%', '55%'],
                sort: null, // 保持原始顺序
                emphasis: {
                    focus: 'ancestor',
                    itemStyle: {
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                },
                levels: [
                    {}, // 空对象表示使用系统默认值
                    {
                        r0: '20%',
                        r: '45%',
                        itemStyle: {
                            borderWidth: 2
                        },
                        label: {
                            fontSize: 14,
                            align: 'center'
                        }
                    },
                    {
                        r0: '45%',
                        r: '90%',
                        label: {
                            align: 'right'
                        },
                        itemStyle: {
                            borderWidth: 1
                        }
                    }
                ],
                label: {
                    formatter: function(params) {
                        const name = params.name;
                        const value = params.value;
                        
                        if (params.depth === 0) {
                            if (value >= 10000) {
                                return name + '\n' + (value / 10000).toFixed(2) + '万元';
                            }
                            return name + '\n' + value.toFixed(2) + '元';
                        } else if (name.length > 10) {
                            return name.slice(0, 9) + '...';
                        }
                        return name;
                    }
                }
            }
        ]
    };
}

/**
 * 图表实例存储对象 - 用于刷新和下载功能
 */
const chartInstances = {};

/**
 * 图表ID与对应初始化函数的映射
 */
const chartInitFunctions = {
    'finance-balance-gauge': initFinanceBalanceGauge,
    'cost-structure-sankey': initCostStructureSankey,
    'financial-metrics-forecast': initFinancialMetricsForecast,
    'financial-health-risk': null, // 假设这个图表的初始化函数尚未实现
    'city-financial-radar': initCityFinancialRadar,
    'credit-income-bubble': initCreditIncomeChart,
    'vehicle-roi-boxplot': initVehicleRoiBoxplot,
    'coupon-package-sunburst': initCouponPackageSunburst
};

/**
 * 在DOM加载完成后绑定按钮事件
 */
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(el => new bootstrap.Tooltip(el));
    }
    
    // 绑定图表刷新按钮事件
    bindRefreshButtons();
    
    // 绑定图表下载按钮事件
    bindDownloadButtons();
    
    // 监听窗口调整大小事件，调整所有图表大小
            window.addEventListener('resize', function() {
        for (const chartId in chartInstances) {
            if (chartInstances[chartId]) {
                chartInstances[chartId].resize();
            }
        }
    });
});

/**
 * 绑定所有刷新按钮的点击事件
 */
function bindRefreshButtons() {
    document.querySelectorAll('.refresh-chart').forEach(button => {
        button.addEventListener('click', function() {
            const chartId = this.getAttribute('data-chart');
            refreshChart(chartId);
            });
        });
}

/**
 * 刷新指定图表
 * @param {string} chartId - 图表的DOM ID
 */
function refreshChart(chartId) {
    // 显示加载中效果
    const loadingId = chartId + 'Loading';
    const loadingEl = document.getElementById(loadingId);
    if (loadingEl) {
        loadingEl.style.display = 'flex';
    }
    
    // 调用对应的初始化函数刷新图表
    const initFunc = chartInitFunctions[chartId];
    if (typeof initFunc === 'function') {
        // 设置短暂延时，确保加载效果能够显示
        setTimeout(() => {
            initFunc();
            // 300ms后隐藏加载效果
            setTimeout(() => {
                if (loadingEl) {
                    loadingEl.style.display = 'none';
                }
            }, 300);
        }, 100);
    } else {
        console.warn(`没有找到图表 ${chartId} 的初始化函数`);
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
    }
}

/**
 * 绑定所有下载按钮的点击事件
 */
function bindDownloadButtons() {
    document.querySelectorAll('.download-chart').forEach(button => {
        button.addEventListener('click', function() {
            const chartId = this.getAttribute('data-chart');
            downloadChart(chartId);
        });
    });
}

/**
 * 下载指定图表为PNG图片
 * @param {string} chartId - 图表的DOM ID
 */
function downloadChart(chartId) {
    try {
        const chartInstance = chartInstances[chartId];
        if (!chartInstance) {
            console.error(`找不到图表实例: ${chartId}`);
            return;
        }
        
        // 获取图表容器和标题
        const chartContainer = document.getElementById(chartId);
        const chartTitle = chartContainer.closest('.card').querySelector('.card-title').textContent.trim();
        const fileName = chartTitle.replace(/\s+/g, '_') + '.png';
        
        // 获取图表的画布元素
        const canvas = chartInstance.getRenderedCanvas({
            pixelRatio: 3, // 3倍分辨率提高图片质量
            backgroundColor: '#fff'
        });
        
        // 创建下载链接
        const link = document.createElement('a');
        link.download = fileName;
        link.href = canvas.toDataURL('image/png');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
    } catch (err) {
        console.error('下载图表失败:', err);
        alert('下载图表失败，请重试。错误详情: ' + err.message);
    }
}

/**
 * 修改原有的echarts初始化函数，保存图表实例到全局对象中
 * 以便支持刷新和下载功能
 */
const originalEChartsInit = echarts.init;
echarts.init = function(dom, theme, opts) {
    const chart = originalEChartsInit.call(this, dom, theme, opts);
    // 保存图表实例到全局映射中
    if (dom && dom.id) {
        chartInstances[dom.id] = chart;
    }
    return chart;
}; 