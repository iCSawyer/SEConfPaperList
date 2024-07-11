# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import scrapy
from itemadapter import ItemAdapter
from typing import Dict, Tuple, List
from .utils.paperlist import paper_list
import os
import orjson
from functools import reduce


def jsonline2md(jsonline: list[dict], header: List[str]) -> str:
    md = ""
    for h in header:
        md += f"| {h} "
    md += "|\n"
    for h in header:
        md += "| --- "
    md += "|\n"
    for j in jsonline:
        for h in header:
            md += f"| {j[h]} "
        md += "|\n"
    return md


class PaperToMarkdownPipeline:
    def __init__(self):
        self.content = []
        self.jsonl_path = "papers.jsonl"
        self.md_path = "papers.md"

    def _update_and_sort(self):
        if os.path.exists(self.jsonl_path):
            with open(self.jsonl_path, "r") as f:
                old_content = f.readlines()
            old_content = [orjson.loads(x) for x in old_content]
            self.content = self.content + old_content
            # reduce by title
            self.content = reduce(lambda x, y: x if y in x else x + [y], self.content, [])

        self.content = [
            {"conf": x["conf"].strip(), "title": x["title"].lstrip("[Remote]").strip(), "author": x["author"].strip()}
            for x in self.content
        ]

        self.content = sorted(
            self.content,
            key=lambda x: (
                -1 * int(x["conf"].split(" ")[-1]),  # year
                ["ICSE", "FSE", "ASE", "ISSTA"].index(x["conf"].split(" ")[0]),  # series
                x["title"],  # title
            ),
        )

        with open(self.jsonl_path, "w") as f:
            for c in self.content:
                f.write(orjson.dumps(c).decode("utf-8") + "\n")

    def process_item(self, item: Dict, spider):
        conf, title, author = item["conf"], item["title"], item["author"]
        self.content.append({"conf": conf, "title": title, "author": author})
        return item

    def open_spider(self, spider: scrapy.Spider):
        spider.log("spider open")
        pass

    def close_spider(self, spider):
        spider.log("spider close")
        self._update_and_sort()
        md = jsonline2md(self.content, ["conf", "title", "author"])
        with open(self.md_path, "w") as f:
            f.write(md)

        # update the README.md
        with open("README.md", "r+") as f:
            readme = f.read()
            start_idx = readme.find("### Paper list\n")
            readme = readme[: start_idx + 15] + md
            readme = readme.replace("conf", "Conference").replace("title", "Title").replace("author", "Authors")
            f.seek(0)
            f.write(readme)
            f.truncate()
