import os
from datetime import datetime
from notion_client import Client
from mcp.server.fastmcp import FastMCP

# ============================================================
# 初始化
# ============================================================
notion = Client(auth=os.environ.get("NOTION_API_KEY"))

# 4 个数据库 ID
DB_DIARY = os.environ.get("NOTION_DB_DIARY")         # 日记
DB_MOMENT = os.environ.get("NOTION_DB_MOMENT")       # 此刻
DB_PROTOCOL = os.environ.get("NOTION_DB_PROTOCOL")   # 协议
DB_MEMORY = os.environ.get("NOTION_DB_MEMORY")       # Memory

mcp = FastMCP("Claude Notion Assistant")


# ============================================================
# 通用辅助函数
# ============================================================
def get_text(props, field_name, field_type="rich_text"):
    """安全地从 Notion 属性中提取文本"""
    try:
        if field_type == "title":
            return props[field_name]["title"][0]["text"]["content"]
        elif field_type == "rich_text":
            return props[field_name]["rich_text"][0]["text"]["content"]
        elif field_type == "select":
            return props[field_name]["select"]["name"] if props[field_name].get("select") else "未设置"
        elif field_type == "date":
            return props[field_name]["date"]["start"] if props[field_name].get("date") else "未设置"
    except (IndexError, KeyError, TypeError):
        return "无"


# ============================================================
# 📔 日记工具
# ============================================================
@mcp.tool()
def save_diary(content: str, date: str = None) -> str:
    """
    写一篇日记。

    Args:
        content: 日记内容
        date: 日期（格式：2025-12-31），不填则自动用今天
    """
    try:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        properties = {
            "名称": {"title": [{"text": {"content": content}}]},
            "日期": {"date": {"start": date}}
        }

        notion.pages.create(parent={"database_id": DB_DIARY}, properties=properties)
        return f"✅ 日记已保存（{date}）"
    except Exception as e:
        return f"❌ 保存失败：{str(e)}"


@mcp.tool()
def get_diaries(start_date: str = None, end_date: str = None) -> str:
    """
    查看日记。可以按日期范围筛选。

    Args:
        start_date: 开始日期（格式：2025-12-01），不填则获取全部
        end_date: 结束日期（格式：2025-12-31），不填则到今天
    """
    try:
        query = {"database_id": DB_DIARY}

        if start_date:
            date_filter = {"property": "日期", "date": {"on_or_after": start_date}}
            if end_date:
                date_filter = {
                    "and": [
                        {"property": "日期", "date": {"on_or_after": start_date}},
                        {"property": "日期", "date": {"on_or_before": end_date}}
                    ]
                }
            query["filter"] = date_filter

        query["sorts"] = [{"property": "日期", "direction": "descending"}]

        results = notion.databases.query(**query).get("results", [])
        if not results:
            return "没有找到日记。"

        diaries = []
        for page in results:
            p = page["properties"]
            diaries.append(
                f"📔 {get_text(p, '日期', 'date')}\n"
                f"   {get_text(p, '名称', 'title')}\n"
            )
        return f"共 {len(diaries)} 篇日记：\n\n" + "\n".join(diaries)
    except Exception as e:
        return f"❌ 获取失败：{str(e)}"


@mcp.tool()
def search_diary(keyword: str) -> str:
    """
    搜索日记内容。

    Args:
        keyword: 搜索关键词
    """
    try:
        results = notion.databases.query(
            database_id=DB_DIARY,
            filter={"property": "名称", "title": {"contains": keyword}}
        ).get("results", [])

        if not results:
            return f"日记中没有找到与 '{keyword}' 相关的内容。"

        diaries = []
        for page in results:
            p = page["properties"]
            diaries.append(
                f"📔 {get_text(p, '日期', 'date')}\n"
                f"   {get_text(p, '名称', 'title')}\n"
            )
        return f"找到 {len(diaries)} 篇相关日记：\n\n" + "\n".join(diaries)
    except Exception as e:
        return f"❌ 搜索失败：{str(e)}"


@mcp.tool()
def delete_diary(content: str) -> str:
    """
    删除一篇日记。

    Args:
        content: 日记内容（精确匹配名称）
    """
    try:
        results = notion.databases.query(
            database_id=DB_DIARY,
            filter={"property": "名称", "title": {"equals": content}}
        ).get("results", [])

        if not results:
            return f"没有找到这篇日记。"

        for page in results:
            notion.pages.update(page_id=page["id"], archived=True)
        return f"✅ 已删除 {len(results)} 篇日记"
    except Exception as e:
        return f"❌ 删除失败：{str(e)}"


# ============================================================
# ✨ 此刻工具
# ============================================================
@mcp.tool()
def save_moment(content: str, date: str = None) -> str:
    """
    记录一个此刻的想法或感受。

    Args:
        content: 此刻的内容
        date: 日期（格式：2025-12-31），不填则自动用今天
    """
    try:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        properties = {
            "名称": {"title": [{"text": {"content": content}}]},
            "日期": {"date": {"start": date}}
        }

        notion.pages.create(parent={"database_id": DB_MOMENT}, properties=properties)
        return f"✅ 此刻已记录（{date}）"
    except Exception as e:
        return f"❌ 保存失败：{str(e)}"


@mcp.tool()
def get_moments(start_date: str = None, end_date: str = None) -> str:
    """
    查看此刻记录。可以按日期范围筛选。

    Args:
        start_date: 开始日期（格式：2025-12-01），不填则获取全部
        end_date: 结束日期（格式：2025-12-31），不填则到今天
    """
    try:
        query = {"database_id": DB_MOMENT}

        if start_date:
            date_filter = {"property": "日期", "date": {"on_or_after": start_date}}
            if end_date:
                date_filter = {
                    "and": [
                        {"property": "日期", "date": {"on_or_after": start_date}},
                        {"property": "日期", "date": {"on_or_before": end_date}}
                    ]
                }
            query["filter"] = date_filter

        query["sorts"] = [{"property": "日期", "direction": "descending"}]

        results = notion.databases.query(**query).get("results", [])
        if not results:
            return "没有找到此刻记录。"

        moments = []
        for page in results:
            p = page["properties"]
            moments.append(
                f"✨ {get_text(p, '日期', 'date')}\n"
                f"   {get_text(p, '名称', 'title')}\n"
            )
        return f"共 {len(moments)} 条此刻：\n\n" + "\n".join(moments)
    except Exception as e:
        return f"❌ 获取失败：{str(e)}"


@mcp.tool()
def search_moment(keyword: str) -> str:
    """
    搜索此刻记录。

    Args:
        keyword: 搜索关键词
    """
    try:
        results = notion.databases.query(
            database_id=DB_MOMENT,
            filter={"property": "名称", "title": {"contains": keyword}}
        ).get("results", [])

        if not results:
            return f"此刻记录中没有找到与 '{keyword}' 相关的内容。"

        moments = []
        for page in results:
            p = page["properties"]
            moments.append(
                f"✨ {get_text(p, '日期', 'date')}\n"
                f"   {get_text(p, '名称', 'title')}\n"
            )
        return f"找到 {len(moments)} 条相关记录：\n\n" + "\n".join(moments)
    except Exception as e:
        return f"❌ 搜索失败：{str(e)}"


@mcp.tool()
def delete_moment(content: str) -> str:
    """
    删除一条此刻记录。

    Args:
        content: 此刻内容（精确匹配名称）
    """
    try:
        results = notion.databases.query(
            database_id=DB_MOMENT,
            filter={"property": "名称", "title": {"equals": content}}
        ).get("results", [])

        if not results:
            return f"没有找到这条此刻记录。"

        for page in results:
            notion.pages.update(page_id=page["id"], archived=True)
        return f"✅ 已删除 {len(results)} 条此刻记录"
    except Exception as e:
        return f"❌ 删除失败：{str(e)}"


# ============================================================
# 📜 协议工具
# ============================================================
@mcp.tool()
def save_protocol(name: str) -> str:
    """
    保存一条协议/规则/约定。

    Args:
        name: 协议内容
    """
    try:
        properties = {
            "名称": {"title": [{"text": {"content": name}}]}
        }

        notion.pages.create(parent={"database_id": DB_PROTOCOL}, properties=properties)
        return f"✅ 协议已保存：{name}"
    except Exception as e:
        return f"❌ 保存失败：{str(e)}"


@mcp.tool()
def get_all_protocols() -> str:
    """获取所有协议列表。"""
    try:
        results = notion.databases.query(database_id=DB_PROTOCOL).get("results", [])
        if not results:
            return "协议库为空。"

        protocols = []
        for i, page in enumerate(results, 1):
            p = page["properties"]
            protocols.append(f"📜 {i}. {get_text(p, '名称', 'title')}")

        return f"共 {len(protocols)} 条协议：\n\n" + "\n".join(protocols)
    except Exception as e:
        return f"❌ 获取失败：{str(e)}"


@mcp.tool()
def search_protocol(keyword: str) -> str:
    """
    搜索协议。

    Args:
        keyword: 搜索关键词
    """
    try:
        results = notion.databases.query(
            database_id=DB_PROTOCOL,
            filter={"property": "名称", "title": {"contains": keyword}}
        ).get("results", [])

        if not results:
            return f"协议中没有找到与 '{keyword}' 相关的内容。"

        protocols = []
        for i, page in enumerate(results, 1):
            p = page["properties"]
            protocols.append(f"📜 {i}. {get_text(p, '名称', 'title')}")

        return f"找到 {len(protocols)} 条相关协议：\n\n" + "\n".join(protocols)
    except Exception as e:
        return f"❌ 搜索失败：{str(e)}"


@mcp.tool()
def delete_protocol(name: str) -> str:
    """
    删除一条协议。

    Args:
        name: 协议内容（精确匹配）
    """
    try:
        results = notion.databases.query(
            database_id=DB_PROTOCOL,
            filter={"property": "名称", "title": {"equals": name}}
        ).get("results", [])

        if not results:
            return f"没有找到这条协议。"

        for page in results:
            notion.pages.update(page_id=page["id"], archived=True)
        return f"✅ 已删除协议：{name}"
    except Exception as e:
        return f"❌ 删除失败：{str(e)}"


# ============================================================
# 🧠 Memory 工具
# ============================================================
@mcp.tool()
def save_memory(name: str, category: str = "事实", importance: str = "中", date: str = None) -> str:
    """
    保存一条记忆到 Memory 库。

    Args:
        name: 记忆内容
        category: 分类（如：偏好/事实/习惯/人物/其他）
        importance: 重要程度（高/中/低）
        date: 日期（格式：2025-12-31），不填则自动用今天
    """
    try:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        properties = {
            "名称": {"title": [{"text": {"content": name}}]},
            "分类": {"select": {"name": category}},
            "重要程度": {"select": {"name": importance}},
            "日期": {"date": {"start": date}}
        }

        notion.pages.create(parent={"database_id": DB_MEMORY}, properties=properties)
        return f"✅ 记忆已保存：{name}"
    except Exception as e:
        return f"❌ 保存失败：{str(e)}"


@mcp.tool()
def search_memory(keyword: str) -> str:
    """
    搜索 Memory 记忆库。

    Args:
        keyword: 搜索关键词
    """
    try:
        results = notion.databases.query(
            database_id=DB_MEMORY,
            filter={"property": "名称", "title": {"contains": keyword}}
        ).get("results", [])

        if not results:
            return f"Memory 中没有找到与 '{keyword}' 相关的内容。"

        memories = []
        for page in results:
            p = page["properties"]
            memories.append(
                f"🧠 {get_text(p, '名称', 'title')}\n"
                f"   分类：{get_text(p, '分类', 'select')} | 重要程度：{get_text(p, '重要程度', 'select')} | 日期：{get_text(p, '日期', 'date')}\n"
            )
        return f"找到 {len(memories)} 条记忆：\n\n" + "\n".join(memories)
    except Exception as e:
        return f"❌ 搜索失败：{str(e)}"


@mcp.tool()
def get_all_memories(category: str = None) -> str:
    """
    获取所有记忆，可按分类筛选。

    Args:
        category: 可选，按分类筛选（如：偏好/事实/习惯/人物/其他）
    """
    try:
        query = {"database_id": DB_MEMORY}
        if category:
            query["filter"] = {"property": "分类", "select": {"equals": category}}

        results = notion.databases.query(**query).get("results", [])
        if not results:
            return "Memory 为空。" if not category else f"没有分类为 '{category}' 的记忆。"

        memories = []
        for page in results:
            p = page["properties"]
            memories.append(
                f"🧠 {get_text(p, '名称', 'title')} [{get_text(p, '分类', 'select')}] "
                f"重要程度：{get_text(p, '重要程度', 'select')}"
            )
        return f"共 {len(memories)} 条记忆：\n\n" + "\n".join(memories)
    except Exception as e:
        return f"❌ 获取失败：{str(e)}"


@mcp.tool()
def delete_memory(name: str) -> str:
    """
    删除一条记忆。

    Args:
        name: 记忆内容（精确匹配名称）
    """
    try:
        results = notion.databases.query(
            database_id=DB_MEMORY,
            filter={"property": "名称", "title": {"equals": name}}
        ).get("results", [])

        if not results:
            return f"没有找到这条记忆。"

        for page in results:
            notion.pages.update(page_id=page["id"], archived=True)
        return f"✅ 已删除记忆：{name}"
    except Exception as e:
        return f"❌ 删除失败：{str(e)}"


# ============================================================
# 🔍 全局搜索（跨所有数据库）
# ============================================================
@mcp.tool()
def search_all(keyword: str) -> str:
    """
    跨所有数据库搜索关键词。同时搜索日记、此刻、协议、Memory。

    Args:
        keyword: 搜索关键词
    """
    all_results = []

    # 搜日记
    try:
        r = notion.databases.query(
            database_id=DB_DIARY,
            filter={"property": "名称", "title": {"contains": keyword}}
        ).get("results", [])
        for page in r:
            p = page["properties"]
            all_results.append(f"[日记] 📔 {get_text(p, '日期', 'date')} - {get_text(p, '名称', 'title')}")
    except:
        pass

    # 搜此刻
    try:
        r = notion.databases.query(
            database_id=DB_MOMENT,
            filter={"property": "名称", "title": {"contains": keyword}}
        ).get("results", [])
        for page in r:
            p = page["properties"]
            all_results.append(f"[此刻] ✨ {get_text(p, '日期', 'date')} - {get_text(p, '名称', 'title')}")
    except:
        pass

    # 搜协议
    try:
        r = notion.databases.query(
            database_id=DB_PROTOCOL,
            filter={"property": "名称", "title": {"contains": keyword}}
        ).get("results", [])
        for page in r:
            p = page["properties"]
            all_results.append(f"[协议] 📜 {get_text(p, '名称', 'title')}")
    except:
        pass

    # 搜 Memory
    try:
        r = notion.databases.query(
            database_id=DB_MEMORY,
            filter={"property": "名称", "title": {"contains": keyword}}
        ).get("results", [])
        for page in r:
            p = page["properties"]
            all_results.append(f"[Memory] 🧠 {get_text(p, '名称', 'title')} [{get_text(p, '分类', 'select')}]")
    except:
        pass

    if not all_results:
        return f"所有数据库中都没有找到与 '{keyword}' 相关的内容。"

    return f"全局搜索找到 {len(all_results)} 条结果：\n\n" + "\n".join(all_results)


# ============================================================
# 启动服务器
# ============================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    inner = mcp.streamable_http_app()

    class HostFix:
        def __init__(self, app):
            self.app = app
        async def __call__(self, scope, receive, send):
            if scope["type"] in ("http", "websocket"):
                headers = dict(scope.get("headers", []))
                headers[b"host"] = b"localhost"
                scope["headers"] = list(headers.items())
            await self.app(scope, receive, send)

    uvicorn.run(HostFix(inner), host="0.0.0.0", port=port,
                proxy_headers=True, forwarded_allow_ips="*")

