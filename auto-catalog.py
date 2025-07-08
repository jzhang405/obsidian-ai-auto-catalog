
import argparse
import json
import shutil
import os
from pathlib import Path
from openai import OpenAI

# 向上级目录查找.vault标识（假设仓库根目录有特殊文件）
def find_vault_root(start_path):
    current = start_path
    while True:
        if os.path.exists(os.path.join(current, '.obsidian')):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None

def find_md_files(path_list):
    """
    收集路径列表中的所有 Markdown 文件（.md 后缀）
    
    :param path_list: 混合相对/绝对路径的列表，可能包含文件或目录
    :return: 去重后的绝对路径 .md 文件列表
    """
    md_files = set()
    
    for path in path_list:
        # 转换为绝对路径（基于当前工作目录）
        abs_path = os.path.abspath(path)
        
        # 跳过不存在的路径
        if not os.path.exists(abs_path):
            continue
        
        # 直接处理文件
        if os.path.isfile(abs_path):
            if abs_path.lower().endswith('.md'):
                md_files.add(abs_path)
        
        # 递归处理目录
        elif os.path.isdir(abs_path):
            for root, dirs, files in os.walk(abs_path):
                for filename in files:
                    if filename.lower().endswith('.md'):
                        full_path = os.path.join(root, filename)
                        md_files.add(full_path)
    
    return sorted(md_files)  # 按字母顺序返回

class FileOrganizer:
    def __init__(self, config_path=None):
        # 解析配置文件路径
        final_config_path = config_path or self.find_default_config()
        
        # 配置文件验证
        if not os.path.exists(final_config_path):
            raise FileNotFoundError(f"配置文件不存在：{final_config_path}")

        # 加载配置
        with open(final_config_path, encoding='utf-8') as f:
            self.config = json.load(f)

        # 构建分类目录表
        self.category_table = {}
        for category in self.config["categories"]:
            base_dir = Path(category["path"])
            for sub in category["subcategories"]:
                full_path = str(base_dir / sub)
                self.category_table[sub.lower()] = full_path

        # 初始化AI客户端
        self.llm_client = OpenAI(
            api_key=self.config["llm"]["api_key"],
            base_url=self.config["llm"].get("api_base")
        )

    def find_default_config(self):
        """查找默认配置文件"""
        
        vault_root = find_vault_root(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(vault_root, ".obsidian", "auto-catalog.json")
        if os.path.exists(config_path):
            return config_path
  
        raise FileNotFoundError("未找到任何配置文件")

    def analyze_content(self, text):
        """调用LLM进行内容分析"""
        instruction = f"""请从以下选项中选择最匹配的分类（直接返回完整路径）：
        {', '.join(self.category_table.values())}
        无法分类时返回：{self.config['default_path']}"""

        response = self.llm_client.chat.completions.create(
            model=self.config["llm"]["model"],
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": f"分析以下内容：\n{text[:3000]}"}
            ],
            temperature=self.config["llm"]["temperature"]
        )
        return response.choices[0].message.content.strip()

    def predict_move_path(self, file_path, verbose=False):
        """预测文件目标路径"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")

        # 读取文件内容
        try:
            with open(file_path, "r", encoding='utf-8') as f:
                content = f.read(3000)  # 限制读取长度
        except UnicodeDecodeError:
            raise ValueError("非文本文件，无法解析内容")

        # 获取预测路径
        raw_prediction = self.analyze_content(content)
        sanitized_path = self.validate_path(raw_prediction)
        
        if verbose:
            print(f"[DEBUG] 原始预测：{raw_prediction}")
            print(f"[DEBUG] 安全路径：{sanitized_path}")

        return sanitized_path

    def validate_path(self, raw_path):
        """路径安全验证"""
        # 直接匹配完整路径
        if raw_path in self.category_table.values():
            return raw_path
        
        # 提取最后一级目录名称
        last_part = Path(raw_path).name.lower()
        return self.category_table.get(last_part, self.config["default_path"])


def main():
    parser = argparse.ArgumentParser(
        description="智能文件分类工具",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("files", nargs="+", help="需要处理的文件路径")
    parser.add_argument("--config", 
                       help="指定配置文件路径")
    parser.add_argument("--dry-run", action="store_true",
                      help="仅显示预测结果不执行移动")
    parser.add_argument("--verbose", action="store_true",
                      help="显示详细调试信息")
    
    args = parser.parse_args()
    
    # 展开输入路径
    try:
        target_files = find_md_files(args.files)
    except Exception as e:
        print(f"路径展开失败：{str(e)}")
        return

    if not target_files:
        print("未找到可处理的文件")
        return
    elif args.verbose:
        print(f"找到 {len(target_files)} 个 Markdown 文件：")
        for file in target_files:
            print(f" - {file}")
    
    # 查找仓库根目录        
    vault_root = find_vault_root(os.path.dirname(os.path.abspath(__file__)))
    if vault_root != None:
        if args.verbose:
            print(f"仓库根目录：{vault_root}")
    else:
        print("未找到仓库根目录，可能无法正确分类文件。")
        return
        
    # 初始化整理器
    try:
        organizer = FileOrganizer(args.config)
    except Exception as e:
        print(f"初始化失败：{str(e)}")
        return

    # 处理文件
    for file_path in target_files:
        try:
            dest = organizer.predict_move_path(file_path, args.verbose)
            dest = Path(vault_root) / dest
            dest = str(dest.resolve())  # 确保是绝对路径
            if args.verbose:
                print(f"[DEBUG] 预测路径：{dest}")
            if args.dry_run:
                print(f"[DRY RUN] {Path(file_path).name} => {dest}")
            else:
                dest_dir = Path(dest)
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(file_path, dest_dir / Path(file_path).name)
                if args.verbose:
                    print(f"移动成功：{Path(file_path).name} -> {dest}")
                
        except Exception as e:
            print(f"处理失败 [{file_path}]：{str(e)}")
    
if __name__ == "__main__":
    main()
