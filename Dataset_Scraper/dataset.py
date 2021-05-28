import scrapy
from scrapy.crawler import CrawlerProcess


class DatasetItem(scrapy.Item):
    file_urls = scrapy.Field()
    files = scrapy.Field()

class DatasetSpider(scrapy.Spider):
    name = 'Dataset_Scraper'
    url = 'https://kern.humdrum.org/cgi-bin/browse?l=essen%2Feuropa%2Fdeutschl'
    
    # crawler's entry point
# custom headers
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/53       7.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }
    
    custom_settings = {
            'FILES_STORE': 'Dataset',
            'ITEM_PIPELINES':{"scrapy.pipelines.files.FilesPipeline":1}

            }
    def start_requests(self):
        yield scrapy.Request(
                url = self.url,
                headers = self.headers,
                callback = self.parse
                )
    def parse(self,response):
        """ This function first scrapes the links for all categories of midi files.
        """
        links = response.xpath("/html/body/center[2]/center/table/tr/td[@colspan='3']/a[1]/@href").getall()
        
        for link in links:
            yield scrapy.Request(url = link, callback= self.parse_midi)

    def parse_midi(self, response):
        item = DatasetItem()
        mixed_links = response.xpath('.//body/center[3]/center/table/tr[1]/td/table/tr/td/a[3]/@href').getall()
        links = mixed_links[1:]
        for link in links:
            item['file_urls'] = [link]
            yield item
            
        

if __name__ == "__main__":
    #run spider from script
    process = CrawlerProcess()
    process.crawl(DatasetSpider)
    process.start()
    
