# 项目开发规范更新：组件化与模块化指南

为提高代码的可维护性、可复用性和开发效率，我们将逐步推进系统的组件化与模块化改造。本文档提供了相关的开发指南和最佳实践。

## 1. 组件化架构说明

### 1.1 组件化的目标

- **提高代码复用率**：减少重复代码，便于维护
- **简化开发流程**：新功能可基于现有组件快速构建
- **统一用户体验**：保持系统各模块的交互一致性
- **降低耦合度**：各功能模块相对独立，便于测试和调试

### 1.2 组件类型

- **基础组件**：提供通用功能，如表格、表单、弹窗等
- **业务组件**：针对特定业务场景的复合组件
- **页面组件**：包含完整业务流程的页面级组件

## 2. 代码组织结构

### 2.1 文件命名与目录结构

```
app/
  ├── static/
  │   ├── js/
  │   │   ├── components/          # 通用组件目录
  │   │   │   ├── dataTable.js     # 数据表格基础组件
  │   │   │   ├── forms.js         # 表单基础组件
  │   │   │   └── modals.js        # 弹窗基础组件
  │   │   ├── [模块名]/            # 按功能模块组织
  │   │   │   ├── [模块名]Table.js # 继承自基础组件的模块特定组件
  │   │   │   └── [模块名].js      # 模块主要功能代码
  │   │   ├── css/
  │   │   │   ├── components/          # 组件样式目录
  │   │   │   └── [模块名]/            # 模块特定样式
  │   │   └── docs/                    # 开发文档目录
  │   ├── templates/
  │   │   ├── components/              # 可复用的模板片段
  │   │   └── [模块名]/                # 模块页面模板
  │   └── docs/                    # 开发文档目录
```

### 2.2 命名规范

- 组件类名：使用大驼峰命名法（如 `DataTable`）
- 文件名：使用小驼峰或下划线命名法，与组件名保持一致
- 方法名：使用小驼峰命名法（如 `initRowEvents`）
- CSS类名：使用连字符命名法（如 `notification-table-container`）

## 3. 组件开发指南

### 3.1 基础组件开发

基础组件应该：
- 功能单一，职责清晰
- 高度可配置，支持各种场景
- 提供完善的文档和示例
- 避免直接依赖特定业务逻辑

示例：
```javascript
/**
 * 通用数据表格组件
 */
class DataTable {
    constructor(options) {
        // 提供默认配置
        this.options = Object.assign({
            defaultOption1: 'value1',
            defaultOption2: 'value2'
        }, options);
        
        // 初始化
        this.init();
    }
    
    init() {
        // 初始化逻辑
    }
    
    // 公共方法
    publicMethod() {
        // ...
    }
    
    // 私有方法 (按约定使用下划线前缀)
    _privateMethod() {
        // ...
    }
}
```

### 3.2 业务组件开发

业务组件应该：
- 继承或组合基础组件
- 封装特定业务逻辑
- 使用依赖注入方式接收依赖

示例：
```javascript
/**
 * 通知表格组件
 */
class NotificationTable extends DataTable {
    constructor(options) {
        // 提供模块默认配置
        const defaultOptions = {
            moduleSpecificOption: 'value'
        };
        
        // 调用父类构造函数
        super(Object.assign({}, defaultOptions, options));
        
        // 初始化模块特有功能
        this.initModuleFeatures();
    }
    
    initModuleFeatures() {
        // 模块特有初始化逻辑
    }
    
    // 模块特有方法
    moduleSpecificMethod() {
        // ...
    }
}
```

## 4. 组件使用指南

### 4.1 引入与初始化

```html
<!-- 引入组件 -->
<script src="/static/js/components/dataTable.js"></script>
<script src="/static/js/notifications/notificationTable.js"></script>

<script>
    // 初始化组件
    document.addEventListener('DOMContentLoaded', function() {
        const myTable = new NotificationTable({
            // 配置选项
        });
    });
</script>
```

### 4.2 HTML结构规范

为确保组件能正确工作，HTML结构应遵循一致的命名规范：

```html
<!-- 表格容器示例 -->
<div class="[模块名]-table-container">
    <table class="table">
        <!-- 表格内容 -->
    </table>
</div>

<!-- 按钮示例 -->
<button class="[动作]-[对象]-btn" data-id="123">操作</button>
```

## 5. 从现有代码迁移到组件化架构

### 5.1 迁移步骤

1. **识别通用功能**：分析现有代码，找出可复用的功能
2. **创建基础组件**：将通用功能抽象为基础组件
3. **创建业务组件**：基于基础组件实现特定业务功能
4. **兼容层处理**：创建兼容层保证平滑过渡
5. **测试验证**：确保功能完整性和向后兼容性

### 5.2 兼容性处理

为确保平稳过渡，可采用以下策略：

- 保留全局函数引用
- 使用适配器模式连接旧接口与新组件
- 逐步替换，避免一次性大规模重构

示例：
```javascript
// 兼容旧版全局函数
window.oldGlobalFunction = function() {
    // 调用新组件方法
    if (window.newComponent) {
        window.newComponent.newMethod();
    } else {
        // 降级处理
        console.warn('新组件未加载，降级执行');
        // 旧的实现...
    }
};
```

## 6. 后端适配

### 6.1 API规范

为支持前端组件化，后端API应遵循以下规范：

- **RESTful设计**：资源明确，操作语义清晰
- **统一响应格式**：保持一致的JSON响应结构
- **支持部分刷新**：提供获取部分数据的接口
- **参数规范**：使用一致的参数命名和传递方式

### 6.2 部分刷新支持

后端路由应支持AJAX部分刷新请求：

```python
@app.route('/module')
def module_index():
    # 获取数据
    data = get_module_data()
    
    # AJAX请求返回JSON
    if request.args.get('ajax') == '1':
        return jsonify({
            'html': render_template('module/_table.html', data=data),
            'stats': get_stats()
        })
    
    # 常规请求返回完整页面
    return render_template('module/index.html', data=data)
```

## 7. 性能与可访问性考虑

### 7.1 性能优化

- 延迟加载非关键组件
- 避免不必要的DOM操作
- 使用事件委托减少事件监听器数量
- 缓存DOM查询结果

### 7.2 可访问性

所有组件都应考虑可访问性：

- 确保键盘可访问
- 提供适当的ARIA属性
- 支持屏幕阅读器
- 满足WCAG 2.1标准

## 8. 文档与测试

### 8.1 组件文档

每个组件应提供以下文档：

- 功能说明
- 配置选项
- 公共方法
- 事件
- 使用示例

### 8.2 组件测试

组件测试应包括：

- 单元测试
- 集成测试
- 浏览器兼容性测试
- 性能测试

## 9. 参考资源

- [组件化详细使用文档](./table_component_usage.md)
- [前端开发规范](./frontend_guidelines.md)
- [API文档](./api_documentation.md) 