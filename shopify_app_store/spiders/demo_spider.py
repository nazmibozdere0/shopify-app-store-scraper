from scrapy import Request
import urllib.request
import re
import pandas as pd

from .app_store import AppStoreSpider
from ..pipelines import WriteToCSV


class DemoSpider(AppStoreSpider):
    """500 app ile hızlı demo. Normal spider'ı bozmaz."""

    name = 'demo'

    SITEMAP_EN = 'https://apps.shopify.com/sitemap_apps_en.xml'

    def __init__(self, limit=500, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_limit = int(limit)

    def start_requests(self):
        apps = pd.read_csv('{}{}{}'.format('./', WriteToCSV.OUTPUT_DIR, 'apps.csv'))
        for _, app in apps.iterrows():
            self.processed_apps[app['url']] = {
                'url': app['url'],
                'lastmod': app['lastmod'],
                'id': app['id'],
            }

        self.processed_reviews = pd.read_csv('{}{}{}'.format('./', WriteToCSV.OUTPUT_DIR, 'reviews.csv'))

        req = urllib.request.Request(self.SITEMAP_EN, headers={'User-Agent': 'Mozilla/5.0'})
        xml = urllib.request.urlopen(req).read().decode('utf-8')

        entries = re.findall(
            r'<url>\s*<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>',
            xml,
        )

        sent = 0
        for loc, lastmod in entries:
            if sent >= self.app_limit:
                break
            if self._is_loc_same_as_processed(loc, lastmod):
                self.logger.info('Skipping unchanged app: %s', loc)
                continue
            yield Request(loc, callback=self.parse, meta={'lastmod': lastmod})
            sent += 1

        self.logger.info('Demo spider: %d app request queued (limit=%d)', sent, self.app_limit)
