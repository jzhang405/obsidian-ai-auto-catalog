# Obsidian AI Auto-Catalog

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Obsidian](https://img.shields.io/badge/Obsidian-Plugin-green)

智能分类工具，使用AI自动将Obsidian笔记归类到PARA方法中的"领域"和"资源"目录，大幅提升知识管理效率。

## 功能亮点

- 🧠 **AI智能分类**：利用DeepSeek模型分析笔记语义内容
- ⚡ **一键归类**：自动移动文件到配置的目录结构
- 📂 **PARA兼容**：专为"领域(Areas)"和"资源(Resources)"设计
- 🔧 **灵活配置**：完全可定制的分类体系
- 🧪 **沙盒模式**：支持dry-run预览分类结果

## 安装步骤

### 前置要求
- Python 3.8+
- 安装依赖：`pip install pyyaml openai`
- Obsidian笔记应用
- [DeepSeek API密钥](https://platform.deepseek.com/)

```bash
# 克隆仓库
git clone https://github.com/yourusername/obsidian-ai-auto-catalog.git

# 安装依赖
pip install pyyaml openai

# 复制到Obsidian配置目录
cp auto-catalog.py /path/to/vault/.obsidian/scripts/
cp auto-catalog.json /path/to/vault/.obsidian/
```

## 使用指南

### 命令行执行
```bash
python auto-catalog.py "笔记1.md" "笔记2.md" [选项]
```

### 参数说明
| 参数 | 说明 |
|------|------|
| `files` | 要处理的笔记文件路径（支持多个文件） |
| `--config` | 指定配置文件路径（默认：`../auto-catalog.json`） |
| `--dry-run` | 仅显示分类结果不移动文件 |
| `--verbose` | 显示详细调试信息 |
| `-h/--help` | 显示帮助信息 |

### 在Obsidian中使用
1. 安装Obsidian插件："Templater" 或 "QuickAdd"
2. 创建命令快捷方式
3. 通过命令面板运行脚本

## 配置文件详解

### LLM配置 (`llm` 部分)
```json
"llm": {
  "provider": "deepseek",
  "api_key": "sk-your-api-key",  // 必填
  "api_base": "https://api.deepseek.com/v1",
  "model": "deepseek-chat",     // 推荐模型
  "temperature": 0.3,           // 创造性 (0-1)
  "max_tokens": 500             // 响应长度
}
```

### 分类目录配置 (`categories` 部分)
```json
"categories": [
  {
    "path": "2. 领域/01.个人成长",  // 实际存储路径
    "subcategories": ["习惯养成", "时间管理", "目标设定"]  // 三级目录
  },
  {
    "path": "3. 资源/08.参考资料",
    "subcategories": ["数据与图表", "模板与格式"]
  }
],
"default_path": "0. 未分类"  // 未识别文件存放位置
```

### 自定义分类
1. 编辑`auto-catalog.json`
2. 修改`categories`数组：
   - `path`：目标目录路径
   - `subcategories`：三级分类标签
3. 添加/删除分类项

## AI自动移动目录流程
1. 读取笔记内容和标题
2. 发送分析请求到DeepSeek API
3. 解析AI返回的分类建议
4. 匹配最接近的配置目录
5. 移动文件到目标目录

## 注意事项

1. **API成本**：每次分类消耗~0.01元（按DeepSeek定价）
2. **隐私安全**：避免处理敏感内容，API会发送内容到服务器
3. **首次使用**：建议`--dry-run`测试分类效果
4. **备份数据**：重要操作前备份vault
5. **分类校准**：复杂内容可能需要人工调整
6. *自动标签**: 配合"AI Tagger Universe"一起使用更佳（手动加tag，手动移动文件，真是累）

> **提示**：对于专业领域，可调整`temperature=0.1`提高准确性

## 贡献与许可

欢迎提交Issue和PR！[贡献指南](CONTRIBUTING.md)  
本项目采用 [MIT 许可证](LICENSE)
