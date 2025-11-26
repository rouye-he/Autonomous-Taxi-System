/**
 * 车辆表格组件
 * 基于通用DataTable组件，为车辆管理模块提供特定功能
 */

class VehicleTable extends DataTable {
    /**
     * 创建车辆表格组件
     * @param {Object} options - 配置选项，可覆盖默认配置
     */
    constructor(options) {
        // 默认配置
        const defaultOptions = {
            tableContainer: '.vehicles-table-container',
            baseUrl: '/vehicles',
            statsElements: {
                total: 'totalVehicleCount',
                online: 'onlineVehicleCount',
                busy: 'busyVehicleCount',
                charging: 'chargingVehicleCount',
                maintenance: 'maintenanceVehicleCount'
            },
            initRowEvents: function() {
                // 初始化行事件在这里实现
                this.initVehicleRowEvents();
            }
        };
        
        // 调用父类构造函数，合并默认配置和用户配置
        super(Object.assign({}, defaultOptions, options));
        
        // 绑定方法到实例
        this.initVehicleRowEvents = this.initVehicleRowEvents.bind(this);
        
        // 确保只绑定一次全局事件
        if (!window.vehicleButtonsEventInitialized) {
            this.initGlobalButtonEvents();
            window.vehicleButtonsEventInitialized = true;
        }
    }
    
    /**
     * 全局事件委托初始化 - 只执行一次
     */
    initGlobalButtonEvents() {
        // 使用事件委托模式为所有车辆按钮绑定事件
        document.addEventListener('click', (e) => {
            // 查找最近的button元素
            const button = e.target.closest('button');
            if (!button) return;
            
            // 获取车辆ID
            const vehicleId = button.getAttribute('data-vehicle-id');
            if (!vehicleId) return;
            
            // 查看详情按钮
            if (button.classList.contains('view-vehicle-btn') || 
                (button.classList.contains('btn-info') && button.closest('td') && 
                 button.querySelector('.bi-info-circle, .bi-info-circle'))) {
                e.preventDefault();
                if (typeof window.showVehicleDetails === 'function') {
                    window.showVehicleDetails(vehicleId);
                } else {
                    console.error('showVehicleDetails函数未定义');
                }
            }
            // 编辑按钮
            else if (button.classList.contains('edit-vehicle-btn') || 
                     (button.classList.contains('btn-warning') && button.closest('td') && 
                      button.querySelector('.bi-pencil'))) {
                e.preventDefault();
                if (typeof window.editVehicle === 'function') {
                    window.editVehicle(vehicleId);
                } else {
                    console.error('editVehicle函数未定义');
                }
            }
            // 删除按钮
            else if (button.classList.contains('delete-vehicle-btn') || 
                     (button.classList.contains('btn-danger') && button.closest('td') && 
                      button.querySelector('.bi-trash'))) {
                e.preventDefault();
                if (typeof window.confirmDeleteVehicle === 'function') {
                    window.confirmDeleteVehicle(vehicleId);
                } else {
                    console.error('confirmDeleteVehicle函数未定义');
                }
            }
            // 救援按钮
            else if (button.classList.contains('rescue-vehicle-btn') || 
                     (button.classList.contains('btn-primary') && button.closest('td') && 
                      button.querySelector('.bi-lightning-charge'))) {
                e.preventDefault();
                if (typeof window.rescueVehicle === 'function') {
                    window.rescueVehicle(vehicleId);
                } else {
                    console.error('rescueVehicle函数未定义');
                }
            }
            // 开始维护按钮
            else if (button.classList.contains('start-maintenance-btn') || 
                     (button.classList.contains('btn-secondary') && button.closest('td') && 
                      button.querySelector('.bi-wrench'))) {
                e.preventDefault();
                if (typeof window.startVehicleMaintenance === 'function') {
                    window.startVehicleMaintenance(vehicleId);
                } else {
                    console.error('startVehicleMaintenance函数未定义');
                }
            }
            // 结束维护按钮
            else if (button.classList.contains('end-maintenance-btn') || 
                     (button.classList.contains('btn-secondary') && button.closest('td') && 
                      button.querySelector('.bi-wrench-adjustable'))) {
                e.preventDefault();
                if (typeof window.endVehicleMaintenance === 'function') {
                    window.endVehicleMaintenance(vehicleId);
                } else {
                    console.error('endVehicleMaintenance函数未定义');
                }
            }
        });
        
        console.log('车辆按钮全局事件初始化完成');
    }
    
    /**
     * 初始化车辆行事件（现在只是占位符，实际逻辑已移至全局事件委托）
     */
    initVehicleRowEvents() {
        // 实际逻辑已经移到initGlobalButtonEvents方法中
        console.log('车辆行事件初始化');
    }
    
    /**
     * 切换视图模式（表格/卡片）
     * @param {string} mode - 视图模式，'table' 或 'card'
     */
    switchViewMode(mode) {
        // 实现视图切换逻辑
        // 可以在这里发送AJAX请求或直接操作DOM
        
        // 保存用户偏好
        localStorage.setItem('vehicleViewMode', mode);
        
        // 刷新表格
        this.reloadTable();
    }
    
    /**
     * 根据状态筛选车辆
     * @param {string} status - 车辆状态
     */
    filterByStatus(status) {
        let url = new URL(window.location.href);
        url.searchParams.set('status', status);
        
        // 重置到第一页
        url.searchParams.set('page', '1');
        
        window.location.href = url.toString();
    }
}

// 导出给其他模块使用
window.VehicleTable = VehicleTable; 