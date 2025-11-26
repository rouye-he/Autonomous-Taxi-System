/**
 * 车辆日志表格组件
 * 扩展通用数据表格组件，处理日志特有的功能
 */

class LogTable extends DataTable {
    /**
     * 创建日志表格组件
     * @param {Object} options - 配置选项
     */
    constructor(options) {
        // 默认配置
        const defaultOptions = {
            tableContainer: '.log-table-container',
            baseUrl: '/vehicles/logs',
            statsElements: {
                total: 'totalLogCount',
                status_change: 'statusChangeCount',
                location_update: 'locationUpdateCount',
                battery_change: 'batteryChangeCount',
                maintenance: 'maintenanceCount'
            }
        };
        
        // 合并默认配置和用户配置
        super(Object.assign({}, defaultOptions, options));
        
        // 初始化日志特有事件
        this.initViewLogHandlers();
        this.initViewToggle();
    }
    
    /**
     * 初始化查看日志详情事件处理
     */
    initViewLogHandlers() {
        const self = this;
        
        // 为所有查看详情按钮添加事件监听（同时处理表格和卡片视图）
        document.querySelectorAll('.view-log-btn').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const logId = this.getAttribute('data-log-id');
                self.viewLogDetails(logId);
            });
        });
    }
    
    /**
     * 初始化视图切换功能
     */
    initViewToggle() {
        // 处理视图切换按钮点击事件
        document.querySelectorAll('.view-toggle-btn').forEach(button => {
            button.addEventListener('click', function() {
                const viewType = this.getAttribute('data-view');
                this.classList.add('active');
                
                if (viewType === 'table') {
                    document.getElementById('tableView').style.display = 'block';
                    document.getElementById('cardView').style.display = 'none';
                    document.querySelector('.view-toggle-btn[data-view="card"]').classList.remove('active');
                } else {
                    document.getElementById('tableView').style.display = 'none';
                    document.getElementById('cardView').style.display = 'block';
                    document.querySelector('.view-toggle-btn[data-view="table"]').classList.remove('active');
                }
                
                // 保存用户偏好到本地存储
                localStorage.setItem('logViewPreference', viewType);
            });
        });
        
        // 初始化时根据用户偏好设置视图
        const savedView = localStorage.getItem('logViewPreference');
        if (savedView) {
            document.querySelector(`.view-toggle-btn[data-view="${savedView}"]`).click();
        }
    }
    
    /**
     * 查看日志详情
     * @param {string} logId - 日志ID
     */
    viewLogDetails(logId) {
        if (!logId) return;
        
        // 获取日志信息，填充模态框
        fetch(`/vehicles/api/log_details/${logId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`请求失败: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    const log = data.data;
                    
                    // 填充模态框信息
                    document.getElementById('modal-vehicle-id').textContent = log.vehicle_id;
                    document.getElementById('modal-plate-number').textContent = log.plate_number;
                    document.getElementById('modal-log-type').textContent = log.log_type;
                    document.getElementById('modal-created-at').textContent = log.created_at;
                    document.getElementById('modal-log-content').textContent = log.log_content;
                    
                    // 显示模态框
                    const modal = new bootstrap.Modal(document.getElementById('logDetailModal'));
                    modal.show();
                } 
            })
            .catch(error => {
                console.error('获取日志详情出错:', error);
            });
    }
    
    /**
     * 重写initRowEvents方法，提供给DataTable使用
     */
    initRowEvents() {
        this.initViewLogHandlers();
    }
}

// 确保文档加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 创建日志表格实例并存储为全局变量
    window.logTable = new LogTable({
        initRowEvents: function() {
            window.logTable.initRowEvents();
        }
    });
}); 