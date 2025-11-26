// 初始化echarts实例
let tagHeatmapChart = null;
let creditPathChart = null;
let firstOrderTimeChart = null; 
let userLTVChart = null;
let couponPreferenceChart = null;
let channelActivityChart = null;
let repurchaseIntervalChart = null;

// 页面加载完成后初始化图表
document.addEventListener('DOMContentLoaded', function() {
    // 初始化标签热力图
    initTagHeatmap();
    
    // 初始化信用分路径图
    initCreditScorePath();
    
    // 初始化首次下单时间分布图
    initFirstOrderTimeChart();
    
    // 初始化用户生命周期价值分布图
    initUserLTVChart();
    
    // 初始化优惠券使用偏好雷达图
    initCouponPreferenceRadar();
    
    // 初始化不同注册渠道用户活跃时段对比图
    initChannelActivityComparison();
    
    // 初始化用户复购间隔时间分布图
    initRepurchaseIntervalChart();
});

// 初始化用户标签共现关系热力图
function initTagHeatmap() {
    const heatmapContainer = document.getElementById('user-tag-heatmap');
    if (!heatmapContainer) return;
    
    tagHeatmapChart = echarts.init(heatmapContainer);
    
    // 显示加载动画
    tagHeatmapChart.showLoading({
        text: '数据加载中...',
        color: '#f56c6c',
        textColor: '#fff',
        maskColor: 'rgba(0, 0, 0, 0.2)',
        zlevel: 0
    });
    
    // 从API获取数据
    fetch('/user_marketing/tags_heatmap_data')
        .then(response => response.json())
        .then(data => {
            tagHeatmapChart.hideLoading();
            renderTagHeatmap(data);
            
            // 添加动态效果
            addHeatmapAnimation();
        })
        .catch(error => {
            console.error('获取标签热力图数据失败:', error);
            tagHeatmapChart.hideLoading();
            tagHeatmapChart.setOption({
                title: {
                    text: '数据加载失败',
                    textStyle: {
                        color: '#f56c6c'
                    },
                    left: 'center',
                    top: 'center'
                }
            });
        });
}

// 渲染用户标签共现关系热力图
function renderTagHeatmap(data) {
    const tags = data.tags;
    const heatmapData = data.data;
    const maxValue = data.max_value;
    
    // 热力图配置
    const option = {
        tooltip: {
            position: 'top',
            formatter: function(params) {
                const tagX = tags[params.value[0]];
                const tagY = tags[params.value[1]];
                return `<div style="padding: 8px 12px; background: rgba(0,0,0,0.8); border-radius: 4px;">
                        <span style="color:#FFD700;font-weight:bold">${tagY}</span> 和 
                        <span style="color:#FFD700;font-weight:bold">${tagX}</span><br/>
                        共同出现次数: <span style="color:#FF6B6B;font-weight:bold">${params.value[2]}</span>
                        </div>`;
            },
            backgroundColor: 'rgba(50,50,50,0.9)',
            borderColor: 'rgba(255,255,255,0.3)',
            borderWidth: 1,
            textStyle: {
                color: '#fff'
            },
            extraCssText: 'box-shadow: 0 4px 20px rgba(0,0,0,0.4); backdrop-filter: blur(4px);'
        },
        animation: true,
        animationDuration: 1000,
        animationEasing: 'bounceOut',
        grid: {
            top: '10%',
            left: '3%',
            right: '6%',
            bottom: '12%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: tags,
            axisLabel: {
                interval: 0,
                rotate: 45,
                color: 'rgba(255,255,255,0.8)',
                fontSize: 11,
                fontWeight: 'bold'
            },
            splitArea: {
                show: true,
                areaStyle: {
                    color: ['rgba(250,250,250,0.05)', 'rgba(200,200,200,0.05)']
                }
            },
            axisLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,0.2)'
                }
            },
            splitLine: {
                show: false
            }
        },
        yAxis: {
            type: 'category',
            data: tags,
            axisLabel: {
                color: 'rgba(255,255,255,0.8)',
                fontSize: 11,
                fontWeight: 'bold'
            },
            splitArea: {
                show: true,
                areaStyle: {
                    color: ['rgba(250,250,250,0.05)', 'rgba(200,200,200,0.05)']
                }
            },
            axisLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,0.2)'
                }
            },
            splitLine: {
                show: false
            }
        },
        visualMap: {
            min: 0,
            max: maxValue,
            calculable: true,
            orient: 'horizontal',
            left: 'center',
            bottom: '0%',
            precision: 0,
            text: ['高频共现', '低频共现'],
            textStyle: {
                color: '#fff',
                shadowColor: 'rgba(0,0,0,0.3)',
                shadowBlur: 2
            },
            inRange: {
                color: [
                    'rgba(30, 144, 255, 0.2)',
                    'rgba(65, 182, 255, 0.5)',
                    'rgba(116, 220, 220, 0.6)',
                    'rgba(177, 250, 175, 0.7)',
                    'rgba(238, 255, 144, 0.8)',
                    'rgba(254, 225, 133, 0.9)',
                    'rgba(255, 181, 120, 0.95)',
                    'rgba(255, 120, 120, 1)'
                ]
            }
        },
        series: [{
            name: '标签共现关系',
            type: 'heatmap',
            data: heatmapData,
            label: {
                show: false
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 15,
                    shadowColor: 'rgba(255,255,255,0.2)'
                }
            }
        }]
    };
    
    // 应用配置
    tagHeatmapChart.setOption(option);
    
    // 窗口大小改变时重置图表大小
    window.addEventListener('resize', function() {
        tagHeatmapChart.resize();
    });
}

// 添加热力图动态效果
function addHeatmapAnimation() {
    // 定时器ID，用于清除
    let heatmapAnimationTimer = null;
    
    // 获取当前配置
    const currentOption = tagHeatmapChart.getOption();
    const originalData = currentOption.series[0].data;
    
    // 随机选择一些数据点进行动态突出显示
    function animateHeatmap() {
        // 随机选择1-3个数据点
        const numPoints = Math.floor(Math.random() * 3) + 1;
        let updatedData = JSON.parse(JSON.stringify(originalData));
        
        // 为随机数据点添加强调效果
        for (let i = 0; i < numPoints; i++) {
            if (updatedData.length > 0) {
                const randomIndex = Math.floor(Math.random() * updatedData.length);
                const point = updatedData[randomIndex];
                
                // 添加闪烁效果
                const originalColor = point.itemStyle ? point.itemStyle.color : null;
                
                point.itemStyle = {
                    ...point.itemStyle,
                    shadowBlur: 25,
                    shadowColor: 'rgba(255,255,255,0.8)',
                    borderWidth: 2,
                    borderColor: '#fff'
                };
            }
        }
        
        // 更新图表
        tagHeatmapChart.setOption({
            series: [{
                data: updatedData
            }]
        });
        
        // 2秒后恢复原样
        setTimeout(() => {
            tagHeatmapChart.setOption({
                series: [{
                    data: originalData
                }]
            });
        }, 2000);
    }
    
    // 开始动画循环
    heatmapAnimationTimer = setInterval(animateHeatmap, 4000);
    
    // 页面离开时清除定时器
    window.addEventListener('beforeunload', function() {
        if (heatmapAnimationTimer) {
            clearInterval(heatmapAnimationTimer);
        }
    });
}

// 初始化用户信用分变化路径图
function initCreditScorePath() {
    const pathContainer = document.getElementById('credit-score-path-chart');
    if (!pathContainer) return;
    
    creditPathChart = echarts.init(pathContainer);
    
    // 显示加载动画
    creditPathChart.showLoading({
        text: '生成用户信用分变化轨迹...',
        color: '#ff69b4',
        textColor: '#fff',
        maskColor: 'rgba(0, 0, 0, 0.2)',
        zlevel: 0
    });
    
    // 从API获取数据
    fetch('/user_marketing/credit_score_path_data')
        .then(response => response.json())
        .then(data => {
            creditPathChart.hideLoading();
            renderCreditScorePath(data);
            
            // 添加动态效果和交互
            addCreditPathAnimation();
        })
        .catch(error => {
            console.error('获取信用分变化路径图数据失败:', error);
            creditPathChart.hideLoading();
            creditPathChart.setOption({
                title: {
                    text: '数据加载失败',
                    textStyle: {
                        color: '#f56c6c'
                    },
                    left: 'center',
                    top: 'center'
                }
            });
        });
}

// 渲染用户信用分变化路径图
function renderCreditScorePath(data) {
    const seriesData = data.series;
    
    // 路径图配置
    const option = {
        tooltip: {
            trigger: 'item',
            formatter: function(params) {
                const data = params.data;
                if (data.value) {
                    const [index, score, date, reason, type] = data.value;
                    let color = '#fff';
                    
                    // 根据类型设置颜色
                    if (type === '订单完成' || type === '系统奖励' || type === '定期恢复') {
                        color = '#52c41a'; // 绿色
                    } else if (type === '违规行为') {
                        color = '#f5222d'; // 红色
                    } else if (type === '人工修改') {
                        color = '#fadb14'; // 黄色
                    }
                    
                    return `<div style="padding: 8px 12px; background: rgba(0,0,0,0.8); border-radius: 6px; box-shadow: 0 4px 10px rgba(0,0,0,0.5);">
                            <div style="font-size: 14px; font-weight: bold; margin-bottom: 5px; color: #fff;">
                                ${params.seriesName}
                            </div>
                            <div style="font-size: 20px; margin-bottom: 5px;">
                                信用分: <span style="color:#ff85c0;font-weight:bold">${score}</span>
                            </div>
                            <div style="font-size: 12px; color: #aaa; margin-bottom: 5px;">
                                ${date || '未知日期'}
                            </div>
                            <div style="font-size: 13px; margin-bottom: 3px;">
                                <span style="color:${color};font-weight:bold">${type}</span>
                            </div>
                            <div style="font-size: 12px; color: #ddd;">
                                ${reason}
                            </div>
                            </div>`;
                }
                return '';
            },
            backgroundColor: 'rgba(50,50,50,0.9)',
            borderColor: 'rgba(255,255,255,0.3)',
            borderWidth: 1,
            padding: 0,
            extraCssText: 'box-shadow: 0 4px 20px rgba(0,0,0,0.4); backdrop-filter: blur(4px);'
        },
        legend: {
            data: seriesData.map(item => item.name),
            top: 10,
            textStyle: {
                color: '#fff'
            },
            icon: 'roundRect',
            itemWidth: 14,
            itemHeight: 8,
            itemGap: 15
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            top: '15%',
            containLabel: true
        },
        xAxis: {
            type: 'value',
            show: false,
            min: 0,
            max: 'dataMax'
        },
        yAxis: {
            type: 'value',
            name: '信用分',
            nameTextStyle: {
                color: 'rgba(255,255,255,0.8)',
                padding: [0, 30, 0, 0]
            },
            min: 0,
            max: 110,
            interval: 20,
            axisLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,0.2)'
                }
            },
            axisLabel: {
                color: 'rgba(255,255,255,0.7)'
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,0.1)',
                    type: 'dashed'
                }
            }
        },
        series: seriesData
    };
    
    // 应用配置
    creditPathChart.setOption(option);
    
    // 窗口大小改变时重置图表大小
    window.addEventListener('resize', function() {
        creditPathChart.resize();
    });
}

// 添加路径图动画效果
function addCreditPathAnimation() {
    // 定时器ID，用于清除
    let pathAnimationTimer = null;
    
    // 获取当前配置和系列数据
    const currentOption = creditPathChart.getOption();
    const seriesData = currentOption.series;
    
    let highlightedSeries = null;
    
    // 随机高亮某个用户
    function animatePath() {
        // 如果有之前的高亮，先清除
        if (highlightedSeries !== null) {
            // 重置之前的高亮
            creditPathChart.dispatchAction({
                type: 'downplay',
                seriesIndex: highlightedSeries
            });
        }
        
        // 随机选择用户路径
        highlightedSeries = Math.floor(Math.random() * seriesData.length);
        
        // 高亮选中路径
        creditPathChart.dispatchAction({
            type: 'highlight',
            seriesIndex: highlightedSeries
        });
        
        // 显示选中路径的提示
        const dataLength = seriesData[highlightedSeries].data.length;
        const randomIndex = Math.floor(Math.random() * dataLength);
        
        creditPathChart.dispatchAction({
            type: 'showTip',
            seriesIndex: highlightedSeries,
            dataIndex: randomIndex
        });
    }
    
    // 开始动画循环
    pathAnimationTimer = setInterval(animatePath, 5000);
    
    // 用户交互时暂停动画
    creditPathChart.on('mouseover', function() {
        if (pathAnimationTimer) {
            clearInterval(pathAnimationTimer);
            pathAnimationTimer = null;
        }
    });
    
    // 用户停止交互后恢复动画
    creditPathChart.on('mouseout', function() {
        if (!pathAnimationTimer) {
            pathAnimationTimer = setInterval(animatePath, 5000);
        }
    });
    
    // 页面离开时清除定时器
    window.addEventListener('beforeunload', function() {
        if (pathAnimationTimer) {
            clearInterval(pathAnimationTimer);
        }
    });
    
    // 立即触发一次动画
    setTimeout(animatePath, 1000);
}

function initCreditScorePathChart() {
    const dom = document.getElementById('credit-score-path-chart');
    const creditScoreChart = echarts.init(dom);
    const app = {};
    
    const option = {
        title: {
            text: '用户信用分变化趋势',
            left: 'center',
            top: 0,
            textStyle: {
                color: '#eee',
                fontSize: 16,
                fontWeight: 'normal'
            }
        },
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(15, 21, 77, 0.8)',
            borderColor: 'rgba(83, 122, 255, 0.6)',
            borderWidth: 1,
            padding: [8, 12],
            textStyle: {
                color: '#fff'
            },
            formatter: function(params) {
                const param = params[0];
                const month = param.value[2];
                const type = param.value[4];
                let result = `<div style="font-size:12px;font-weight:bold;margin-bottom:5px;color:#80dfff">${month} - ${type}</div>`;
                
                params.forEach(param => {
                    const color = param.color.colorStops 
                        ? `linear-gradient(${param.color.colorStops[0].color}, ${param.color.colorStops[1].color})` 
                        : param.color;
                    
                    const label = param.value[3];
                    const value = param.value[1].toFixed(1);
                    
                    result += `
                    <div style="display:flex;align-items:center;margin:5px 0;">
                        <div style="width:10px;height:10px;background:${color};border-radius:50%;margin-right:6px"></div>
                        <span style="margin-right:10px">${label}:</span>
                        <span style="color:#fffa9d;font-weight:bold">${value}</span>
                    </div>`;
                });
                
                return result;
            }
        },
        legend: {
            show: false
        },
        toolbox: {
            feature: {
                saveAsImage: {
                    title: '保存为图片',
                    name: '用户信用分变化趋势',
                    backgroundColor: '#0f204b',
                    iconStyle: {
                        color: '#fff',
                        borderColor: '#80dfff'
                    }
                }
            },
            right: 20,
            top: 15,
            iconStyle: {
                color: '#80dfff',
                borderColor: '#80dfff'
            }
        },
        grid: {
            top: 70,
            left: 10,
            right: 10,
            bottom: 45,
            containLabel: true
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: [],
            axisLine: {
                lineStyle: {
                    color: 'rgba(255, 255, 255, 0.2)'
                }
            },
            axisLabel: {
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: 11
            },
            axisTick: {
                show: false
            }
        },
        yAxis: {
            type: 'value',
            name: '信用分',
            nameTextStyle: {
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: 12,
                padding: [0, 0, 0, 20]
            },
            min: 50,
            max: 100,
            interval: 10,
            axisLine: {
                show: false
            },
            axisLabel: {
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: 11
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(255, 255, 255, 0.1)'
                }
            }
        },
        dataZoom: [{
            type: 'inside',
            start: 0,
            end: 100
        }],
        series: []
    };
    
    // 类别切换选项
    const categorySelector = document.createElement('div');
    categorySelector.className = 'category-selector';
    categorySelector.innerHTML = `
        <span class="category-btn active" data-category="gender">按性别</span>
        <span class="category-btn" data-category="city">按城市</span>
        <style>
            .category-selector {
                position: absolute;
                top: 35px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(15, 32, 75, 0.7);
                border-radius: 20px;
                padding: 3px;
                display: flex;
                z-index: 100;
                border: 1px solid rgba(128, 223, 255, 0.4);
            }
            .category-btn {
                padding: 4px 12px;
                cursor: pointer;
                border-radius: 16px;
                margin: 0 2px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 12px;
                transition: all 0.3s;
            }
            .category-btn.active {
                background: rgba(128, 223, 255, 0.3);
                color: #fff;
                box-shadow: 0 0 10px rgba(128, 223, 255, 0.4);
            }
            .category-btn:hover:not(.active) {
                background: rgba(128, 223, 255, 0.1);
                color: rgba(255, 255, 255, 0.9);
            }
        </style>
    `;
    dom.parentNode.style.position = 'relative';
    dom.parentNode.appendChild(categorySelector);
    
    // 当前显示的分类
    let currentCategory = 'gender';
    
    // 加载数据并绘制图表
    function loadChartData() {
        fetch('/user_marketing/credit_score_path_data')
            .then(response => response.json())
            .then(data => {
                if (!data.months || data.months.length === 0) {
                    console.error('No month data available');
                    return;
                }
                
                // 更新x轴数据
                option.xAxis.data = data.months;
                
                // 设置当前显示的系列
                const seriesData = currentCategory === 'gender' ? data.gender_series : data.city_series;
                
                // 使用空数组先清空系列
                option.series = [];
                
                // 延迟添加系列实现动画效果
                creditScoreChart.setOption(option);
                
                // 为每个系列设置延迟动画
                seriesData.forEach((series, index) => {
                    setTimeout(() => {
                        const newOption = {
                            series: [series]
                        };
                        
                        // 合并选项而不是替换
                        creditScoreChart.setOption(newOption, true);
                        
                        // 触发闪光动画效果
                        if (index === seriesData.length - 1) {
                            setTimeout(() => {
                                addGlowingEffect(creditScoreChart);
                            }, 300);
                        }
                    }, index * 200);
                });
            })
            .catch(error => {
                console.error('Error fetching credit score path data:', error);
                option.series = [];
                creditScoreChart.setOption(option);
            });
    }
    
    // 初始加载
    loadChartData();
    
    // 添加类别切换事件
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            if (this.classList.contains('active')) return;
            
            document.querySelector('.category-btn.active').classList.remove('active');
            this.classList.add('active');
            
            currentCategory = this.dataset.category;
            
            // 清空当前系列并重新加载
            option.series = [];
            creditScoreChart.clear();
            creditScoreChart.setOption(option);
            
            // 加载新分类数据
            loadChartData();
        });
    });
    
    // 添加闪光动画效果
    function addGlowingEffect(chart) {
        const seriesCount = chart.getOption().series.length;
        let currentIndex = 0;
        
        // 轮流为每个系列创建闪光效果
        function pulseNextSeries() {
            if (!chart.getOption().series || chart.getOption().series.length === 0) return;
            
            const allSeries = [...chart.getOption().series];
            const targetSeries = allSeries[currentIndex % seriesCount];
            
            // 创建临时增强效果
            const enhancedSeries = {
                ...targetSeries,
                lineStyle: {
                    ...targetSeries.lineStyle,
                    width: 5,
                    shadowBlur: 15,
                    shadowColor: 'rgba(255, 255, 255, 0.8)'
                },
                itemStyle: {
                    ...targetSeries.itemStyle,
                    shadowBlur: 15,
                    shadowColor: 'rgba(255, 255, 255, 0.8)'
                },
                symbolSize: 12,
                z: 10
            };
            
            // 替换目标系列
            allSeries[currentIndex % seriesCount] = enhancedSeries;
            chart.setOption({series: allSeries}, true);
            
            // 恢复正常效果
            setTimeout(() => {
                allSeries[currentIndex % seriesCount] = targetSeries;
                chart.setOption({series: allSeries}, true);
                
                // 移动到下一个系列
                currentIndex = (currentIndex + 1) % seriesCount;
                
                // 随机时间后触发下一个脉冲
                setTimeout(pulseNextSeries, 2000 + Math.random() * 3000);
            }, 800);
        }
        
        // 开始脉冲效果
        setTimeout(pulseNextSeries, 500);
    }
    
    // 窗口大小改变时调整图表大小
    window.addEventListener('resize', function() {
        creditScoreChart.resize();
    });
    
    // 添加缩放动画效果
    addZoomAnimationEffect(creditScoreChart);
    
    return {
        chart: creditScoreChart,
        update: loadChartData
    };
}

// 初始化首次下单时间分布图
function initFirstOrderTimeChart() {
    const chartContainer = document.getElementById('first-order-time-distribution');
    if (!chartContainer) return;
    
    firstOrderTimeChart = echarts.init(chartContainer);
    
    // 显示加载动画
    firstOrderTimeChart.showLoading({
        text: '数据加载中...',
        color: '#ff7b46',
        textColor: '#fff',
        maskColor: 'rgba(255, 123, 70, 0.1)',
        zlevel: 0
    });
    
    // 从API获取数据
    fetch('/user_marketing/first_order_time_data')
        .then(response => response.json())
        .then(data => {
            firstOrderTimeChart.hideLoading();
            renderSimpleFirstOrderTimeChart(data);
        })
        .catch(error => {
            console.error('获取首次下单时间分布数据失败:', error);
            firstOrderTimeChart.hideLoading();
            firstOrderTimeChart.setOption({
                title: {
                    text: '数据加载失败',
                    textStyle: {
                        color: '#f56c6c'
                    },
                    left: 'center',
                    top: 'center'
                }
            });
        });
}

// 简化版首次下单时间分布图
function renderSimpleFirstOrderTimeChart(data) {
    const categories = data.categories || [];
    const counts = data.counts || [];
    const totalUsers = data.total_users || 0;
    
    // 计算百分比
    const percentages = counts.map(count => {
        return ((count / totalUsers) * 100).toFixed(1);
    });
    
    // 简化的配置选项
    const option = {
        backgroundColor: 'rgba(40, 40, 40, 0.8)',
        title: {
            text: '首次下单时间分布',
            textStyle: {
                color: '#fff',
                fontSize: 14
            },
            left: 'center'
        },
        tooltip: {
            trigger: 'axis',
            formatter: function(params) {
                const index = params[0].dataIndex;
                return `${categories[index]}: ${counts[index]}人 (${percentages[index]}%)`;
            }
        },
        grid: {
            left: '5%',
            right: '5%',
            bottom: '15%',
            top: '15%',
            containLabel: true,
            show: true,
            borderColor: 'rgba(255,255,255,0.2)',
            backgroundColor: 'rgba(50, 50, 50, 0.3)'
        },
        xAxis: {
            type: 'category',
            data: categories,
            axisLine: {
                show: true,
                lineStyle: {
                    color: 'rgba(255,255,255,0.8)',
                    width: 2
                }
            },
            axisTick: {
                show: true,
                alignWithLabel: true,
                length: 5,
                lineStyle: {
                    color: 'rgba(255,255,255,0.7)',
                    width: 1
                }
            },
            axisLabel: {
                show: true,
                color: '#ffa64d',
                rotate: 45,
                fontSize: 12,
                margin: 15,
                fontWeight: 'bold'
            },
            splitLine: {
                show: true,
                lineStyle: {
                    color: 'rgba(255,255,255,0.2)',
                    type: 'dashed'
                }
            }
        },
        yAxis: {
            type: 'value',
            name: '用户数',
            nameLocation: 'middle',
            nameGap: 50,
            nameTextStyle: {
                color: '#ff9900',
                fontSize: 16,
                fontWeight: 'bold'
            },
            axisLine: {
                show: true,
                lineStyle: {
                    color: 'rgba(255,255,255,0.8)',
                    width: 2
                }
            },
            axisTick: {
                show: true,
                length: 5,
                lineStyle: {
                    color: 'rgba(255,255,255,0.7)',
                    width: 1
                }
            },
            axisLabel: {
                show: true,
                color: '#ffa64d',
                fontSize: 12,
                fontWeight: 'bold'
            },
            splitLine: {
                show: true,
                lineStyle: {
                    color: 'rgba(255,255,255,0.2)',
                    type: 'dashed',
                    width: 1
                }
            }
        },
        series: [{
            name: '用户数量',
            type: 'bar',
            data: counts,
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    {offset: 0, color: '#ff6e76'},
                    {offset: 1, color: '#ff9f7f'}
                ]),
                borderRadius: [4, 4, 0, 0]
            },
            barWidth: '50%',
            label: {
                show: true,
                position: 'top',
                formatter: '{c}',
                color: '#fff',
                fontSize: 12,
                fontWeight: 'bold'
            }
        }]
    };
    
    // 先清除原有内容
    firstOrderTimeChart.clear();
    // 应用新配置
    firstOrderTimeChart.setOption(option, true);
    
    // 强制更新图表
    setTimeout(() => {
        firstOrderTimeChart.resize();
    }, 100);
    
    // 窗口调整大小时，重新调整图表尺寸
    window.addEventListener('resize', function() {
        firstOrderTimeChart.resize();
    });
}

// 初始化用户生命周期价值分布图
function initUserLTVChart() {
    const chartContainer = document.getElementById('user-ltv-distribution');
    if (!chartContainer) return;
    
    userLTVChart = echarts.init(chartContainer);
    
    // 显示加载动画
    userLTVChart.showLoading({
        text: '数据加载中...',
        color: '#36c77d',
        textColor: '#fff',
        maskColor: 'rgba(54, 199, 125, 0.1)',
        zlevel: 0
    });
    
    // 从API获取数据
    fetch('/user_marketing/user_ltv_data')
        .then(response => response.json())
        .then(data => {
            userLTVChart.hideLoading();
            renderSimpleUserLTVChart(data);
        })
        .catch(error => {
            console.error('获取用户LTV分布数据失败:', error);
            userLTVChart.hideLoading();
            userLTVChart.setOption({
                title: {
                    text: '数据加载失败',
                    textStyle: {
                        color: '#f56c6c'
                    },
                    left: 'center',
                    top: 'center'
                }
            });
        });
}

// 简化版用户生命周期价值分布图
function renderSimpleUserLTVChart(data) {
    const summary = data.summary || {};
    
    // 格式化金额
    const formatMoney = (value) => {
        return '￥' + parseFloat(value).toFixed(2);
    };
    
    // 构建简单的箱线图数据
    const boxData = [];
    
    if (summary.count > 0) {
        boxData.push([
            summary.min,     // 最小值
            summary.q1,      // 下四分位数
            summary.median,  // 中位数
            summary.q3,      // 上四分位数
            summary.max      // 最大值
        ]);
    } else {
        boxData.push([0, 0, 0, 0, 0]);
    }
    
    // 从用户数据中提取前5个高价值用户
    const topUsers = (data.summary && data.summary.top_users) || [];
    const scatterData = topUsers.slice(0, 5).map(user => {
        return [0, user.total_spend];
    });
    
    // 简化的配置选项
    const option = {
        backgroundColor: 'rgba(40, 40, 40, 0.8)',
        title: {
            text: '用户价值(LTV)分布',
            textStyle: {
                color: '#fff',
                fontSize: 14
            },
            left: 'center'
        },
        tooltip: {
            trigger: 'item',
            formatter: function(params) {
                if (params.seriesName === '价值分布') {
                    return `
                        <div>最大值: ${formatMoney(summary.max)}</div>
                        <div>上四分位: ${formatMoney(summary.q3)}</div>
                        <div>中位数: ${formatMoney(summary.median)}</div>
                        <div>下四分位: ${formatMoney(summary.q1)}</div>
                        <div>最小值: ${formatMoney(summary.min)}</div>
                        <div>平均值: ${formatMoney(summary.mean)}</div>
                    `;
                } else if (params.seriesName === '高价值用户') {
                    const userIndex = params.dataIndex;
                    if (userIndex < topUsers.length) {
                        const user = topUsers[userIndex];
                        return `
                            <div>${user.username}</div>
                            <div>消费总额: ${formatMoney(user.total_spend)}</div>
                            <div>订单数: ${user.order_count}</div>
                        `;
                    }
                }
                return '';
            }
        },
        grid: {
            left: '15%',
            right: '15%',
            bottom: '15%',
            top: '15%',
            show: true,
            borderColor: 'rgba(255,255,255,0.2)',
            backgroundColor: 'rgba(50, 50, 50, 0.3)'
        },
        xAxis: {
            type: 'category',
            data: ['用户消费总额'],
            axisLine: {
                show: true,
                onZero: false,
                lineStyle: {
                    color: 'rgba(255,255,255,0.8)',
                    width: 2
                }
            },
            axisTick: {
                show: true,
                length: 5,
                lineStyle: {
                    color: 'rgba(255,255,255,0.7)',
                    width: 1
                }
            },
            axisLabel: {
                show: true,
                color: '#4dffaa',
                fontSize: 12,
                fontWeight: 'bold'
            },
            splitLine: {
                show: true,
                lineStyle: {
                    color: 'rgba(255,255,255,0.2)',
                    type: 'dashed'
                }
            }
        },
        yAxis: {
            type: 'value',
            name: '金额(元)',
            nameLocation: 'middle',
            nameGap: 50,
            nameTextStyle: {
                color: '#00cc66',
                fontSize: 16,
                padding: [0, 0, 10, 0],
                fontWeight: 'bold'
            },
            axisLine: {
                show: true,
                onZero: false,
                lineStyle: {
                    color: 'rgba(255,255,255,0.8)',
                    width: 2
                }
            },
            axisTick: {
                show: true,
                length: 5,
                lineStyle: {
                    color: 'rgba(255,255,255,0.7)',
                    width: 1
                }
            },
            axisLabel: {
                show: true,
                color: '#4dffaa',
                fontSize: 12,
                formatter: '{value} ¥',
                fontWeight: 'bold'
            },
            splitLine: {
                show: true,
                lineStyle: {
                    color: 'rgba(255,255,255,0.2)',
                    type: 'dashed',
                    width: 1
                }
            }
        },
        series: [
            {
                name: '价值分布',
                type: 'boxplot',
                data: boxData,
                itemStyle: {
                    color: '#36c77d',
                    borderColor: '#fff',
                    borderWidth: 2
                },
                tooltip: {
                    formatter: function(param) {
                        return [
                            '用户消费价值统计:',
                            '最大值: ' + param.data[4].toFixed(2) + ' ¥',
                            '上四分位数: ' + param.data[3].toFixed(2) + ' ¥',
                            '中位数: ' + param.data[2].toFixed(2) + ' ¥',
                            '下四分位数: ' + param.data[1].toFixed(2) + ' ¥',
                            '最小值: ' + param.data[0].toFixed(2) + ' ¥'
                        ].join('<br/>');
                    }
                }
            },
            {
                name: '高价值用户',
                type: 'scatter',
                data: scatterData,
                symbolSize: 12,
                itemStyle: {
                    color: '#ff9f43',
                    borderColor: '#fff',
                    borderWidth: 1,
                    shadowBlur: 5,
                    shadowColor: 'rgba(0,0,0,0.3)'
                }
            }
        ]
    };
    
    // 先清除原有内容
    userLTVChart.clear();
    // 应用新配置
    userLTVChart.setOption(option, true);
    
    // 强制更新图表
    setTimeout(() => {
        userLTVChart.resize();
    }, 100);
    
    // 窗口调整大小时，重新调整图表尺寸
    window.addEventListener('resize', function() {
        userLTVChart.resize();
    });
}

// 初始化优惠券使用偏好雷达图
function initCouponPreferenceRadar() {
    const radarContainer = document.getElementById('coupon-preference-radar');
    if (!radarContainer) return;
    
    couponPreferenceChart = echarts.init(radarContainer);
    
    // 显示加载动画
    couponPreferenceChart.showLoading({
        text: '数据加载中...',
        color: '#a855f7',
        textColor: '#fff',
        maskColor: 'rgba(0, 0, 0, 0.2)',
        zlevel: 0
    });
    
    // 从API获取数据
    fetch('/user_marketing/coupon_preference_radar')
        .then(response => response.json())
        .then(data => {
            couponPreferenceChart.hideLoading();
            renderCouponPreferenceRadar(data);
        })
        .catch(error => {
            console.error('获取优惠券使用偏好数据失败:', error);
            couponPreferenceChart.hideLoading();
            couponPreferenceChart.setOption({
                title: {
                    text: '数据加载失败',
                    textStyle: {
                        color: '#f56c6c'
                    },
                    left: 'center',
                    top: 'center'
                }
            });
        });
}

// 渲染优惠券使用偏好雷达图
function renderCouponPreferenceRadar(data) {
    const indicators = data.indicators || [];
    const seriesData = data.series_data || [];
    const categories = data.categories || [];
    
    const colors = ['#9955ff', '#ff55a4', '#5593ff', '#55deff', '#55ffaa'];
    
    // 雷达图配置
    const option = {
        backgroundColor: 'rgba(25, 25, 35, 0.9)',
        color: colors,
        tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(50,50,50,0.9)',
            borderColor: 'rgba(255,255,255,0.3)',
            borderWidth: 1,
            textStyle: {
                color: '#fff'
            },
            formatter: function(params) {
                return `<div style="padding: 8px 12px;">
                        <strong style="color:#FFD700">${params.name}</strong><br/>
                        ${params.marker} ${params.value.join(' / ')}
                        </div>`;
            }
        },
        legend: {
            data: categories,
            bottom: 0,
            textStyle: {
                color: 'rgba(255,255,255,0.8)'
            },
            selectedMode: 'single'
        },
        radar: {
            indicator: indicators,
            shape: 'circle',
            splitNumber: 5,
            radius: '70%',
            axisName: {
                color: 'rgba(255,255,255,0.8)',
                fontSize: 11,
                padding: [3, 5]
            },
            splitLine: {
                lineStyle: {
                    color: ['rgba(255,255,255,0.3)']
                }
            },
            splitArea: {
                show: true,
                areaStyle: {
                    color: ['rgba(255,255,255,0.05)', 'rgba(255,255,255,0.03)']
                }
            },
            axisLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,0.3)'
                }
            }
        },
        series: seriesData.map((item, index) => ({
            name: item.name,
            type: 'radar',
            data: [{
                value: item.value,
                name: item.name,
                areaStyle: {
                    opacity: 0.5,
                    color: {
                        type: 'radial',
                        x: 0.5,
                        y: 0.5,
                        r: 0.5,
                        colorStops: [{
                            offset: 0,
                            color: colors[index % colors.length] // 渐变色起始
                        }, {
                            offset: 1,
                            color: colors[index % colors.length].replace(')', ', 0.2)').replace('rgb', 'rgba') // 渐变色结束
                        }]
                    }
                },
                lineStyle: {
                    width: 2
                },
                emphasis: {
                    lineStyle: {
                        width: 4
                    }
                }
            }]
        }))
    };
    
    // 应用配置
    couponPreferenceChart.setOption(option);
    
    // 窗口大小改变时重置图表大小
    window.addEventListener('resize', function() {
        couponPreferenceChart.resize();
    });
}

// 初始化不同注册渠道用户活跃时段对比图
function initChannelActivityComparison() {
    const chartContainer = document.getElementById('channel-activity-comparison');
    if (!chartContainer) return;
    
    channelActivityChart = echarts.init(chartContainer);
    
    // 显示加载动画
    channelActivityChart.showLoading({
        text: '数据加载中...',
        color: '#4ade80',
        textColor: '#fff',
        maskColor: 'rgba(0, 0, 0, 0.2)',
        zlevel: 0
    });
    
    // 从API获取数据
    fetch('/user_marketing/channel_activity_comparison')
        .then(response => response.json())
        .then(data => {
            channelActivityChart.hideLoading();
            renderChannelActivityComparison(data);
        })
        .catch(error => {
            console.error('获取渠道活跃时段数据失败:', error);
            channelActivityChart.hideLoading();
            channelActivityChart.setOption({
                title: {
                    text: '数据加载失败',
                    textStyle: {
                        color: '#f56c6c'
                    },
                    left: 'center',
                    top: 'center'
                }
            });
        });
}

// 渲染不同注册渠道用户活跃时段对比图
function renderChannelActivityComparison(data) {
    const channels = data.channels || [];
    const hours = data.hours || Array.from({length: 24}, (_, i) => i);
    const series = data.series || [];
    const peakHours = data.peak_hours || [];
    
    // 生成小时标签
    const hourLabels = hours.map(hour => `${hour}:00`);
    
    // 找出峰值时段标注
    const markPoints = channels.map((channel, index) => {
        return {
            data: peakHours.filter(peak => peak.channel === channel).map(peak => ({
                name: `${peak.hour}点峰值`,
                value: peak.count,
                xAxis: peak.hour,
                yAxis: peak.count,
                itemStyle: {
                    color: series[index]?.itemStyle?.color || '#fff'
                }
            }))
        };
    });
    
    // 图表配置
    const option = {
        backgroundColor: 'rgba(25, 25, 35, 0.9)',
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            },
            formatter: function(params) {
                let result = `<div style="padding: 8px 12px;"><strong>${params[0].axisValue}</strong><br/>`;
                params.forEach(param => {
                    result += `${param.marker} ${param.seriesName}: ${param.value}<br/>`;
                });
                result += '</div>';
                return result;
            }
        },
        legend: {
            data: channels,
            bottom: 10,
            textStyle: {
                color: 'rgba(255,255,255,0.8)'
            },
            selectedMode: 'multiple'
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            top: '15%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: hourLabels,
            axisLabel: {
                color: 'rgba(255,255,255,0.8)',
                formatter: '{value}'
            },
            axisLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,0.4)'
                }
            },
            axisTick: {
                alignWithLabel: true,
                lineStyle: {
                    color: 'rgba(255,255,255,0.4)'
                }
            }
        },
        yAxis: {
            type: 'value',
            name: '订单数量',
            nameTextStyle: {
                color: 'rgba(255,255,255,0.8)'
            },
            axisLabel: {
                color: 'rgba(255,255,255,0.8)'
            },
            axisLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,0.4)'
                }
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,0.2)'
                }
            }
        },
        series: series.map((item, index) => ({
            ...item,
            markPoint: markPoints[index],
            barWidth: '50%',
            barGap: '10%',
            emphasis: {
                focus: 'series'
            },
            animationDelay: function(idx) {
                return idx * 80;
            }
        }))
    };
    
    // 应用配置
    channelActivityChart.setOption(option);
    
    // 窗口大小改变时重置图表大小
    window.addEventListener('resize', function() {
        channelActivityChart.resize();
    });
}

// 初始化用户复购间隔时间分布图
function initRepurchaseIntervalChart() {
    const chartContainer = document.getElementById('repurchase-interval-chart');
    if (!chartContainer) return;
    
    repurchaseIntervalChart = echarts.init(chartContainer);
    
    // 显示加载动画
    repurchaseIntervalChart.showLoading({
        text: '数据加载中...',
        color: '#3b82f6',
        textColor: '#fff',
        maskColor: 'rgba(0, 0, 0, 0.2)',
        zlevel: 0
    });
    
    // 从API获取数据
    fetch('/user_marketing/repurchase_interval_data')
        .then(response => response.json())
        .then(data => {
            repurchaseIntervalChart.hideLoading();
            renderRepurchaseIntervalChart(data);
        })
        .catch(error => {
            console.error('获取复购间隔数据失败:', error);
            repurchaseIntervalChart.hideLoading();
            repurchaseIntervalChart.setOption({
                title: {
                    text: '数据加载失败',
                    textStyle: {
                        color: '#f56c6c'
                    },
                    left: 'center',
                    top: 'center'
                }
            });
        });
}

// 渲染用户复购间隔时间分布图
function renderRepurchaseIntervalChart(data) {
    const intervals = data.intervals || [];
    const counts = data.counts || [];
    const kdeData = data.kde_data || [];
    const summary = data.summary || {};
    
    // 计算柱状图最大高度，以便于曲线适配
    const maxCount = Math.max(...counts, 1);
    
    // 转换KDE数据为曲线格式 - 确保x轴对齐并归一化y值
    const lineData = [];
    if (kdeData.length > 0) {
        // 确保KDE数据映射到正确的区间位置
        for (let i = 0; i < kdeData.length; i++) {
            const interval = kdeData[i][0];
            const density = kdeData[i][1];
            
            // 将连续值映射到离散区间索引
            let xIndex = 0;
            for (let j = 0; j < intervals.length; j++) {
                if (interval <= getBinUpperBound(j)) {
                    xIndex = j;
                    break;
                }
            }
            
            // 将密度值缩放到与柱状图高度一致
            const scaledDensity = density * maxCount;
            lineData.push([xIndex, scaledDensity]);
        }
        
        // 对lineData按x值排序
        lineData.sort((a, b) => a[0] - b[0]);
        
        // 确保曲线平滑，在各区间之间添加额外的点
        const smoothedLineData = [];
        for (let i = 0; i < intervals.length; i++) {
            // 寻找落在该区间的所有点，取平均值
            const pointsInBin = lineData.filter(point => Math.floor(point[0]) === i);
            if (pointsInBin.length > 0) {
                const avgY = pointsInBin.reduce((sum, p) => sum + p[1], 0) / pointsInBin.length;
                smoothedLineData.push([i, avgY]);
            } else {
                // 如果没有点落在该区间，插值计算
                smoothedLineData.push([i, 0]);
            }
        }
        
        // 使用平滑处理后的数据
        const finalLineData = [];
        for (let i = 0; i < smoothedLineData.length; i++) {
            finalLineData.push([smoothedLineData[i][0], smoothedLineData[i][1]]);
        }
        
        // 图表配置
        const option = {
            backgroundColor: 'rgba(25, 25, 35, 0.9)',
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross',
                    crossStyle: {
                        color: 'rgba(255,255,255,0.3)'
                    }
                },
                formatter: function(params) {
                    if (params.length > 0) {
                        const barData = params.find(param => param.seriesType === 'bar');
                        if (barData) {
                            return `<div style="padding: 8px 12px;">
                                    <strong>${barData.name}</strong><br/>
                                    ${barData.marker} 用户数: ${barData.value}<br/>
                                    ${summary.avg_interval_text ? `平均间隔: ${summary.avg_interval_text}<br/>` : ''}
                                    ${summary.median_interval_text ? `中位数间隔: ${summary.median_interval_text}` : ''}
                                    </div>`;
                        }
                    }
                    return '';
                }
            },
            title: {
                text: `复购用户: ${data.repurchase_users || 0}/${data.total_users || 0}`,
                textStyle: {
                    fontSize: 13,
                    color: 'rgba(255,255,255,0.9)',
                    fontWeight: 'normal'
                },
                padding: [5, 10],
                left: 10,
                top: 10
            },
            legend: {
                data: ['用户数量', '密度曲线'],
                bottom: 10,
                textStyle: {
                    color: 'rgba(255,255,255,0.8)'
                },
                selectedMode: 'multiple'
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                top: '20%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: intervals,
                axisPointer: {
                    type: 'shadow'
                },
                axisLabel: {
                    color: 'rgba(255,255,255,0.8)',
                    interval: 0,
                    rotate: 30
                },
                axisLine: {
                    lineStyle: {
                        color: 'rgba(255,255,255,0.4)'
                    }
                },
                axisTick: {
                    lineStyle: {
                        color: 'rgba(255,255,255,0.4)'
                    }
                }
            },
            yAxis: [
                {
                    type: 'value',
                    name: '用户数量',
                    nameTextStyle: {
                        color: 'rgba(255,255,255,0.8)'
                    },
                    position: 'left',
                    axisLabel: {
                        color: 'rgba(255,255,255,0.8)'
                    },
                    axisLine: {
                        lineStyle: {
                            color: 'rgba(255,255,255,0.4)'
                        }
                    },
                    splitLine: {
                        lineStyle: {
                            color: 'rgba(255,255,255,0.2)'
                        }
                    }
                }
            ],
            series: [
                {
                    name: '用户数量',
                    type: 'bar',
                    barWidth: '50%',
                    data: counts,
                    itemStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: 'rgba(59, 130, 246, 0.9)' },
                            { offset: 1, color: 'rgba(16, 185, 129, 0.5)' }
                        ])
                    },
                    emphasis: {
                        focus: 'series',
                        itemStyle: {
                            shadowBlur: 10,
                            shadowColor: 'rgba(0,0,0,0.3)'
                        }
                    }
                },
                {
                    name: '密度曲线',
                    type: 'line',
                    smooth: true,
                    symbol: 'none',
                    sampling: 'average',
                    data: finalLineData.length > 0 ? finalLineData : [],
                    lineStyle: {
                        width: 3,
                        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                            { offset: 0, color: 'rgba(131, 56, 236, 0.8)' },
                            { offset: 0.5, color: 'rgba(214, 51, 132, 0.8)' },
                            { offset: 1, color: 'rgba(251, 113, 133, 0.8)' }
                        ])
                    },
                    areaStyle: {
                        opacity: 0.3,
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: 'rgba(131, 56, 236, 0.6)' },
                            { offset: 1, color: 'rgba(131, 56, 236, 0)' }
                        ])
                    },
                    z: 10
                }
            ]
        };
        
        // 应用配置
        repurchaseIntervalChart.setOption(option);
    } else {
        // 没有KDE数据的情况，只显示柱状图
        const option = {
            backgroundColor: 'rgba(25, 25, 35, 0.9)',
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                },
                formatter: function(params) {
                    if (params.length > 0) {
                        return `<div style="padding: 8px 12px;">
                                <strong>${params[0].name}</strong><br/>
                                ${params[0].marker} 用户数: ${params[0].value}<br/>
                                ${summary.avg_interval_text ? `平均间隔: ${summary.avg_interval_text}` : ''}
                                </div>`;
                    }
                    return '';
                }
            },
            title: {
                text: `复购用户: ${data.repurchase_users || 0}/${data.total_users || 0}`,
                textStyle: {
                    fontSize: 13,
                    color: 'rgba(255,255,255,0.9)',
                    fontWeight: 'normal'
                },
                padding: [5, 10],
                left: 10,
                top: 10
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                top: '20%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: intervals,
                axisLabel: {
                    color: 'rgba(255,255,255,0.8)',
                    interval: 0,
                    rotate: 30
                },
                axisLine: {
                    lineStyle: {
                        color: 'rgba(255,255,255,0.4)'
                    }
                },
                axisTick: {
                    lineStyle: {
                        color: 'rgba(255,255,255,0.4)'
                    }
                }
            },
            yAxis: {
                type: 'value',
                name: '用户数量',
                nameTextStyle: {
                    color: 'rgba(255,255,255,0.8)'
                },
                axisLabel: {
                    color: 'rgba(255,255,255,0.8)'
                },
                axisLine: {
                    lineStyle: {
                        color: 'rgba(255,255,255,0.4)'
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: 'rgba(255,255,255,0.2)'
                    }
                }
            },
            series: [{
                data: counts,
                type: 'bar',
                barWidth: '50%',
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(59, 130, 246, 0.9)' },
                        { offset: 1, color: 'rgba(16, 185, 129, 0.5)' }
                    ])
                }
            }]
        };
        
        // 应用配置
        repurchaseIntervalChart.setOption(option);
    }
    
    // 窗口大小改变时重置图表大小
    window.addEventListener('resize', function() {
        repurchaseIntervalChart.resize();
    });
}

// 辅助函数：获取指定bin索引的上边界值
function getBinUpperBound(binIndex) {
    const boundaries = [6, 12, 24, 48, 72, 168, 336, 720];
    return boundaries[binIndex];
} 