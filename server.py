import os
import json
from datetime import datetime
from notion_client import Client
from mcp.server.fastmcp import FastMCP

# 初始化 Notion
notion = Client(auth=os.environ.get("NOTION_API_KEY"))
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

# 创建 MCP 服务器（使用 SSE 传输，适合远程部署）
mcp = FastMCP("Claude Memory")


@mcp.tool()
def save_memory(title: str, content: str, category: str = "事实", importance: str = "中", tags: list[str] = None) -> str:
    """
    保存一条记忆到 Notion 数据库。

    Args:
        title: 记忆的标题
        content: 记忆的具体内容
        category: 类别（偏好/事实/习惯/项目）
        importance: 重要性（高/中/低）
        tags: 标签列表
    """
    try:
        properties = {
            "标题": {
                "title": [{"text": {"content": title}}]
            },
            "内容": {
                "rich_text": [{"text": {"content": content}}]
            },
            "类别": {
                "select": {"name": category}
            },
            "重要性": {
                "select": {"name": importance}
            },
            "日期": {
                "date": {"start": datetime.now().isoformat()}
            }
        }

        if tags:
            properties["标签"] = {
                "multi_select": [{"name": tag} for tag in tags]
            }

        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties=properties
        )

        return f"✅ 记忆已保存：{title}"
    except Exception as e:
        return f"❌ 保存失败：{str(e)}"


@mcp.tool()
def search_memory(keyword: str) -> str:
    """
    通过关键词搜索记忆。

    Args:
        keyword: 搜索关键词
    """
    try:
        response = notion.databases.query(
            database_id=DATABASE_ID,
            filter={
                "or": [
                    {
                        "property": "标题",
                        "title": {"contains": keyword}
                    },
                    {
                        "property": "内容",
                        "rich_text": {"contains": keyword}
                    }
                ]
            }
        )

        results = response.get("results", [])

        if not results:
            return f"没有找到与 '{keyword}' 相关的记忆。"

        memories = []
        for page in results:
            props = page["properties"]
            title = props["标题"]["title"][0]["text"]["content"] if props["标题"]["title"] else "无标题"
            content_text = props["内容"]["rich_text"][0]["text"]["content"] if props["内容"]["rich_text"] else "无内容"
            category_name = props["类别"]["select"]["name"] if props["类别"].get("select") else "未分类"
            importance_name = props["重要性"]["select"]["name"] if props["重要性"].get("select") else "未设置"

            memories.append(f"📌 {title}\n   类别：{category_name} | 重要性：{importance_name}\n   内容：{content_text}\n")

        return f"找到 {len(memories)} 条相关记忆：\n\n" + "\n".join(memories)
    except Exception as e:
        return f"❌ 搜索失败：{str(e)}"


@mcp.tool()
def get_all_memories(category: str = None) -> str:
    """
    获取所有记忆，可按类别筛选。

    Args:
        category: 可选，按类别筛选（偏好/事实/习惯/项目）
    """
    try:
        query_params = {"database_id": DATABASE_ID}

        if category:
            query_params["filter"] = {
                "property": "类别",
                "select": {"equals": category}
            }

        response = notion.databases.query(**query_params)
        results = response.get("results", [])

        if not results:
            return "记忆库为空。" if not category else f"没有类别为 '{category}' 的记忆。"

        memories = []
        for page in results:
            props = page["properties"]
            title = props["标题"]["title"][0]["text"]["content"] if props["标题"]["title"] else "无标题"
            content_text = props["内容"]["rich_text"][0]["text"]["content"] if props["内容"]["rich_text"] else "无内容"
            category_name = props["类别"]["select"]["name"] if props["类别"].get("select") else "未分类"

            memories.append(f"📌 {title} [{category_name}]\n   {content_text}\n")

        return f"共 {len(memories)} 条记忆：\n\n" + "\n".join(memories)
    except Exception as e:
        return f"❌ 获取失败：{str(e)}"


@mcp.tool()
def delete_memory(title: str) -> str:
    """
    通过标题删除一条记忆。

    Args:
        title: 要删除的记忆标题
    """
    try:
        response = notion.databases.query(
            database_id=DATABASE_ID,
            filter={
                "property": "标题",
                "title": {"equals": title}
            }
        )

        results = response.get("results", [])

        if not results:
            return f"没有找到标题为 '{title}' 的记忆。"

        for page in results:
            notion.pages.update(page_id=page["id"], archived=True)

        return f"✅ 已删除 {len(results)} 条标题为 '{title}' 的记忆。"
    except Exception as e:
        return f"❌ 删除失败：{str(e)}"


if __name__ == "__main__":
    mcp.run(transport="sse")
