from scrapy import Request, Spider
from w3lib.html import remove_tags


class BandsSpider(Spider):
    name = "bands"

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.genre = kwargs.get("genre", "")
        self.country = kwargs.get("country", "")
        self.get_discography = bool(kwargs.get("get_discography", False))
        self.request_count = 0

    def start_requests(self):
        yield self._get_index_page_request()

    def _get_index_page_request(self):
        request = Request(
            f"https://www.metal-archives.com/search/ajax-advanced/searching/bands/?bandName=&genre={self.genre}&country={self.country}&yearCreationFrom=&yearCreationTo=&bandNotes=&status=&themes=&location=&bandLabelName=&sEcho=14&iColumns=3&sColumns=&iDisplayStart={self.request_count*200}&iDisplayLength=200&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&_=1676470980732"
        )
        self.request_count += 1
        return request
        

    def parse(self, response):
        j = response.json()
        for band in j["aaData"]:
            yield Request(
                band[0].split('href="')[1].split('">')[0],
                callback=self.parse_band,
            )
        if j["iTotalRecords"] > (self.request_count * 200) :
            yield self._get_index_page_request()

    def parse_band(self, response):
        item = {
            "id": response.url.split("/")[-1],
            "band_name": response.xpath("//h1/a/text()").get(),
            "country_of_origin": response.xpath("//dt[.='Country of origin:']/following-sibling::dd/a/text()").get(),
            "location": response.xpath("//dt[.='Location:']/following-sibling::dd/text()").get(),
            "status": response.xpath("//dt[.='Status:']/following-sibling::dd/text()").get(),
            "formed_in": response.xpath("//dt[.='Formed in:']/following-sibling::dd/text()").get(),
            "years_active": remove_tags(response.xpath("//dt[.='Years active:']/following-sibling::dd").get()),
            "genre": response.xpath("//dt[.='Genre:']/following-sibling::dd/text()").get(),
            "lyrical_themes:": response.xpath("//dt[.='Lyrical themes:']/following-sibling::dd/text()").get(),
            "current_label": response.xpath("//dt[.='Current label:']/following-sibling::dd/a/text()").get(),
            "band_comment": remove_tags(response.xpath("//div[@class='band_comment clear']").get()),
        }

        if self.get_discography:
            yield Request(
                response.xpath(".//div[@id='band_disco']/ul/li/a/@href").get(),
                callback=self.parse_discography,
                cb_kwargs={"item": item}
            )
        else:
            yield item

    def parse_discography(self, response, item):
        item["discography"] = []
        for row in response.xpath("//table/tbody/tr"):
            item["discography"].append({
                "name": row.xpath(".//td[1]/a/text()").get(),
                "type": row.xpath(".//td[2]/text()").get(),
                "year": row.xpath(".//td[3]/text()").get(),
                "reviews": row.xpath(".//td[4]/a/text()").get(),
            })
        yield item