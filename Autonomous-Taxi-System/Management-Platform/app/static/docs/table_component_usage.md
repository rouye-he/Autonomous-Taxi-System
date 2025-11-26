# 数据表格组件使用文档

本文档介绍了系统中新的模块化表格组件，以及如何在不同模块中使用这些组件。

## 1. 组件结构

表格组件采用继承结构，包含：

- `DataTable`: 通用数据表格组件，提供基础功能
- `NotificationTable`: 继承自DataTable，扩展了通知管理特有功能

文件结构:
```
app/static/js/
  ├── components/
  │   └── dataTable.js      # 通用表格组件
  ├── notifications/
  │   ├── notificationTable.js  # 通知表格组件
  │   └── notifications.js      # 兼容旧版代码
```

## 2. 使用步骤

### 2.1 后端准备

1. **创建独立的表格模板片段**：
   - 创建一个单独的HTML模板片段（如`_table_name.html`）
   - 该片段只包含表格相关内容，不包含页面其他部分

2. **修改控制器支持AJAX请求**：
```python
@blueprint.route('/your-page')
def your_page():
    # ... 获取数据 ...
    
    # 检查是否是AJAX请求
    is_ajax = request.args.get('ajax') == '1'
    include_stats = request.args.get('include_stats') == '1'
    
    # 准备返回数据
    if is_ajax:
        response_data = {
            'html': render_template('your_module/_table_template.html', items=items)
        }
        
        # 如果需要统计数据
        if include_stats:
            response_data['stats'] = {
                'total': total_count,
                'unread': unread_count,
                # 其他统计数据...
            }
        
        return jsonify(response_data)
    
    # 正常页面请求
    return render_template('your_module/index.html', 
                          items=items,
                          total_count=total_count)
```

### 2.2 前端实现

1. **引入组件JavaScript文件**：
```html
<!-- 基础组件 -->
<script src="{{ url_for('static', filename='js/components/dataTable.js') }}"></script>
<!-- 如果使用扩展组件 -->
<script src="{{ url_for('static', filename='js/your_module/yourTable.js') }}"></script>
```

2. **HTML结构**：
```html
<!-- 基础页面内容 -->
<div class="container">
  <h1>标题 <span class="badge bg-primary" id="totalCount">{{ total_count }}</span></h1>

  <!-- 表格容器 -->
  <div class="table-responsive your-table-container">
    {% include 'your_module/_table_template.html' %}
  </div>
</div>
```

3. **初始化表格组件**：
```javascript
document.addEventListener('DOMContentLoaded', function() {
    // 使用通用组件
    const table = new DataTable({
        tableContainer: '.your-table-container',
        baseUrl: '/your-module',
        statsElements: {
            total: 'totalCount',
            // 其他统计元素...
        },
        initRowEvents: function() {
            // 初始化表格行事件
            initRowActions();
        }
    });
    
    // 绑定全局函数到window对象
    window.reloadTable = function(delay) {
        table.reloadTable(delay);
    };
    
    // 初始化行事件
    function initRowActions() {
        // 绑定按钮事件等
        document.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                // 处理点击事件
            });
        });
    }
    
    // 初始化页面加载时的行事件
    initRowActions();
});
```

## 3. 使用通用表格组件 (DataTable)

### 配置参数
```javascript
const options = {
    tableContainer: '.my-table-container',  // 表格容器选择器
    baseUrl: '/my-module',                  // 数据请求基础URL
    statsElements: {                        // 统计元素ID映射
        total: 'totalCount',
        someOther: 'otherCountId' 
    },
    initRowEvents: function() {             // 行事件初始化函数
        // 初始化表格行事件
    },
    showToastOnRefresh: true                // 刷新后是否显示提示
};
```

### 提供的方法

- `reloadTable(delay)`: 重新加载表格数据，可选延迟时间(毫秒)
- `showToast(message, type)`: 显示提示消息，类型可以是success/error/warning/info
- `jumpToPage()`: 跳转到指定页码
- `updateStats(stats)`: 更新统计数据

## 4. 创建模块特定的表格组件

如果需要为特定模块创建表格组件，可以继承DataTable:

1. **创建新组件文件**:
```javascript
/**
 * 模块特定表格组件
 */
class YourModuleTable extends DataTable {
    constructor(options) {
        // 默认配置
        const defaultOptions = {
            tableContainer: '.your-module-table-container',
            baseUrl: '/your-module',
            statsElements: {
                total: 'totalYourModuleCount'
            }
        };
        
        // 合并配置并调用父类构造函数
        super(Object.assign({}, defaultOptions, options));
        
        // 绑定模块特有事件
        this.initModuleSpecificEvents();
    }
    
    // 初始化模块特有事件
    initModuleSpecificEvents() {
        const self = this;
        
        // 示例：绑定特定按钮事件
        document.querySelectorAll('.your-action-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const itemId = this.dataset.id;
                self.performAction(itemId);
            });
        });
    }
    
    // 添加模块特有方法
    performAction(itemId) {
        // 执行操作...
        
        // 操作成功后刷新表格
        this.reloadTable();
    }
}

// 导出给其他模块使用
window.YourModuleTable = YourModuleTable;
```

2. **在页面中使用**:
```javascript
document.addEventListener('DOMContentLoaded', function() {
    // 初始化模块特定表格
    const table = new YourModuleTable();
    
    // 可选择性暴露给全局
    window.yourModuleTable = table;
});
```

## 5. 实际使用案例：通知表格组件

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // 初始化通知表格
    const notificationTable = new NotificationTable({
        // 可以覆盖默认配置
        showToastOnRefresh: false
    });
    
    // 可以直接调用特定方法
    document.getElementById('clearAllBtn').addEventListener('click', function() {
        if (confirm('确定要清空所有通知吗？')) {
            notificationTable.deleteAllNotifications();
        }
    });
});
```

## 6. 后端接口要求详解

为了支持组件的AJAX刷新功能，后端需要满足以下要求：

### 6.1 统一的JSON响应格式

```json
{
    "html": "<table>...</table>",  // 表格HTML内容
    "stats": {                     // 统计数据对象
        "total": 100,
        "unread": 5,
        "other_stat": 20
    }
}
```

### 6.2 路由查询参数

- `ajax=1`: 表示当前是AJAX请求，返回JSON数据
- `include_stats=1`: 请求包含统计数据
- `page=n`: 当前页码

### 6.3 操作结果返回

对于修改操作（如删除、更新），应当返回:

```json
{
    "success": true,
    "message": "操作成功",
    "stats": {
        "total": 99,  // 更新后的统计数据
        "unread": 4
    }
}
```

## 7. 兼容性维护

为保证平滑过渡，注意以下几点：

1. **保持全局函数兼容性**:
```javascript
// 在新组件上暴露旧的全局函数
window.showToast = function(message, type) {
    dataTableInstance.showToast(message, type);
};

window.reloadTable = function(delay) {
    dataTableInstance.reloadTable(delay);
};
```

2. **CSS类兼容性**:
- 保持现有CSS类名不变
- 对于新增样式，使用新的特定前缀

## 8. 注意事项

1. 确保HTML结构中的ID和类名与组件配置一致
2. 在AJAX刷新后，需要重新绑定事件处理程序
3. 统计元素ID映射必须与HTML中的实际ID匹配
4. 模板片段应当只包含表格本身，不包含分页控件等外部元素 