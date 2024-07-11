import scrapy
from scrapy.http import Response, Request
from ..utils.paperlist import paper_list


class PaperSpider(scrapy.Spider):
    name = "paper_spider"

    def start_requests(self):
        for p in paper_list:
            yield Request(url=p["url"], callback=self.parse, cb_kwargs=p)

    def parse(self, response: Response, **kwargs):
        table = response.xpath('//*[@id="event-overview"]/table')
        papers = table.xpath("tr/td[2]")
        for paper in papers:
            title = paper.xpath("a[1]/text()").get()
            author_list = paper.xpath('.//div[@class="performers"]/a')
            author = ", ".join([a.xpath("text()").get() for a in author_list])
            yield {"conf": kwargs["conf"], "title": title, "author": author}
