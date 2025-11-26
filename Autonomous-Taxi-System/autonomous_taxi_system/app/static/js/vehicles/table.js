/**
 * 车辆表格AJAX分页和操作处理
 */

// 初始化页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 绑定分页链接点击事件
    bindPaginationEvents();
    // 绑定页码跳转事件
    document.querySelector('#pageJumpInput')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            pageTableJump();
        }
    });
});

/**
 * 绑定分页链接的点击事件
 */
function bindPaginationEvents() {
    // 获取所有分页链接
    const paginationLinks = document.querySelectorAll('#vehicle-pagination .page-link');
    
    // 为每个分页链接添加点击事件
    paginationLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // 如果链接被禁用，不执行操作
            if (this.parentElement.classList.contains('disabled')) {
                e.preventDefault();
                return;
            }
            
            // 阻止默认行为
            e.preventDefault();
            
            // 获取链接地址
            const url = this.getAttribute('href');
            if (url && url !== '#') {
                // 使用AJAX加载新页面内容
                loadTableData(url);
            }
        });
    });
}

/**
 * 通过AJAX加载表格数据
 * @param {string} url - 请求URL
 */
function loadTableData(url) {
    // 添加AJAX标识
    const ajaxUrl = new URL(url, window.location.origin);
    ajaxUrl.searchParams.set('ajax', '1');
    
    // 显示加载状态
    const tableBody = document.querySelector('#vehicles-table-body');
    tableBody.innerHTML = `
        <tr>
            <td colspan="9" class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2">正在加载车辆数据...</p>
            </td>
        </tr>
    `;
    
    // 发送AJAX请求
    fetch(ajaxUrl.toString())
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应异常');
            }
            return response.json();
        })
        .then(data => {
            // 更新表格内容
            document.querySelector('.table-responsive').innerHTML = data.html;
            
            // 更新URL（不刷新页面）
            window.history.pushState({}, '', url);
            
            // 重新绑定事件
            bindPaginationEvents();
            bindTableEvents();
        })
        .catch(error => {
            console.error('加载数据失败:', error);
            tableBody.innerHTML = `
                <tr>
                    <td colspan="9" class="text-center text-danger">
                        <i class="bi bi-exclamation-triangle"></i> 
                        加载数据失败，请<a href="javascript:window.location.reload()">刷新页面</a>重试
                    </td>
                </tr>
            `;
        });
}

/**
 * 页码跳转函数
 */
function pageTableJump() {
    const input = document.getElementById('pageJumpInput');
    if (!input) return;
    
    const pageNum = parseInt(input.value);
    const maxPage = parseInt(input.getAttribute('max') || '1');
    
    if (pageNum && pageNum >= 1 && pageNum <= maxPage) {
        // 构建URL，保留所有现有参数
        let url = new URL(window.location.href);
        url.searchParams.set('page', pageNum);
        
        // 使用AJAX加载新页面
        loadTableData(url.toString());
    } else {
        // 显示错误提示
        alert('请输入有效的页码 (1-' + maxPage + ')');
    }
}

/**
 * 重新绑定表格内的事件处理
 */
function bindTableEvents() {
    // 查看车辆按钮
    document.querySelectorAll('.view-vehicle-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const vehicleId = this.getAttribute('data-vehicle-id');
            // 处理查看操作
            window.location.href = `/admin/vehicles/view/${vehicleId}`;
        });
    });
    
    // 编辑车辆按钮
    document.querySelectorAll('.edit-vehicle-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const vehicleId = this.getAttribute('data-vehicle-id');
            // 处理编辑操作
            window.location.href = `/admin/vehicles/edit/${vehicleId}`;
        });
    });
    
    // 删除车辆按钮
    document.querySelectorAll('.delete-vehicle-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const vehicleId = this.getAttribute('data-vehicle-id');
            // 删除操作直接执行，不需要确认
            deleteVehicle(vehicleId);
        });
    });
}

/**
 * 删除车辆
 * @param {string} vehicleId - 车辆ID
 */
function deleteVehicle(vehicleId) {
    fetch(`/admin/vehicles/delete/${vehicleId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 重新加载当前页面数据
            loadTableData(window.location.href);
        } else {
            alert(data.message || '删除失败');
        }
    })
    .catch(error => {
        console.error('删除操作失败:', error);
        alert('操作失败，请稍后重试');
    });
} 